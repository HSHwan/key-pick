# booking/views.py
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Count, Sum, Q, Avg
from django.contrib.auth import logout, login, authenticate
from django.shortcuts import render, get_object_or_404, redirect
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.utils import timezone
from django.contrib import messages
from django.views.decorators.http import require_POST
from datetime import date, timedelta

# 모델과 폼 import
from .models import *
from .forms import ReviewForm, ReservationForm, IssueReportForm, ScheduleForm, BranchThemeUpdateForm

# 1. 메인 & 테마 (Theme)
def theme_list_view(request):
    search_query = request.GET.get('search_query', '')
    branch_id = request.GET.get('branch', '')
    sort_by = request.GET.get('sort', 'latest')
    
    # 기본 쿼리셋 (평점 평균과 리뷰 개수 계산 포함)
    themes = Theme.objects.filter(is_active=True, status='Ready').annotate(
        avg_rating=Avg('reservation__review__rating'),
        review_count=Count('reservation__review')
    )
    
    if search_query:
        themes = themes.filter(
            Q(name__icontains=search_query) | 
            Q(genre__icontains=search_query)
        )
    if branch_id:
        themes = themes.filter(branch_id=branch_id)
        
    if sort_by == 'rating':
        themes = themes.order_by('-avg_rating')
    elif sort_by == 'reviews':
        themes = themes.order_by('-review_count')
    else:
        themes = themes.order_by('-theme_id')
        
    branches = Branch.objects.filter(is_active=True)

    context = {
        'themes': themes,
        'branches': branches,
        'selected_branch': branch_id,
        'search_query': search_query,
        'sort_by': sort_by,
    }
    return render(request, 'booking/theme_list.html', context)

def theme_detail_view(request, theme_id):
    theme = get_object_or_404(Theme, theme_id=theme_id, is_active=True)
    reviews = Review.objects.filter(reservation__theme=theme)
    
    context = {
        'theme': theme,
        'reviews': reviews,
    }
    return render(request, 'booking/theme_detail.html', context)

# 2. 회원 (Member: Signup, Login, Logout, MyPage)
def signup_view(request):
    if request.method == 'POST':
        login_id = request.POST.get('login_id')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')
        name = request.POST.get('name')
        phone = request.POST.get('phone')
        
        context = {}
        
        if not (login_id and password and password_confirm and name and phone):
            context['error'] = '모든 칸을 입력해주세요.'
            return render(request, 'booking/signup.html', context)

        if password != password_confirm:
            context['error'] = '비밀번호가 일치하지 않습니다.'
            return render(request, 'booking/signup.html', context)
        
        if Member.objects.filter(login_id=login_id).exists():
            context['error'] = '이미 사용 중인 ID입니다.'
            return render(request, 'booking/signup.html', context)
        
        if Member.objects.filter(phone=phone).exists():
            context['error'] = '이미 등록된 연락처입니다.'
            return render(request, 'booking/signup.html', context)

        try:
            user = Member.objects.create_user(
                login_id=login_id,
                password=password,
                name=name,
                phone=phone,
                role='Customer'
            )
            user_auth = authenticate(request, username=login_id, password=password)
            if user_auth:
                login(request, user_auth)
            return redirect('theme-list') 

        except Exception as e:
            context['error'] = f'가입 중 오류가 발생했습니다: {e}'
            return render(request, 'booking/signup.html', context)
    else:
        return render(request, 'booking/signup.html')

def login_view(request):
    context = {}
    if request.method == 'POST':
        login_id = request.POST.get('username') 
        password = request.POST.get('password')

        if not (login_id and password):
            context['error'] = 'ID와 비밀번호를 모두 입력해주세요.'
            return render(request, 'booking/login.html', context)

        user = authenticate(request, username=login_id, password=password)

        if user is not None:
            login(request, user)
            return redirect('theme-list')
        else:
            context['error'] = '로그인 ID 또는 비밀번호가 올바르지 않습니다.'
            return render(request, 'booking/login.html', context)
    else:
        return render(request, 'booking/login.html')

@login_required
def logout_view(request):
    logout(request)
    return redirect('theme-list') 

@login_required 
def my_page_view(request):
    reservations = Reservation.objects.filter(
        member=request.user
    ).order_by('-reservation_time')

    reviews = Review.objects.filter(
        member=request.user
    ).order_by('-created_at')

    context = {
        'reservations': reservations,
        'reviews': reviews,
    }
    return render(request, 'booking/my_page.html', context)

# 3. 예약 (Reservation)
@login_required
@transaction.atomic
def reservation_create_view(request, theme_id):
    theme = get_object_or_404(Theme, theme_id=theme_id, is_active=True, status='Ready')
    
    if request.method == 'POST':
        form = ReservationForm(request.POST)
        if form.is_valid():
            reservation_time = form.cleaned_data['reservation_time']
            num_of_participants = form.cleaned_data['num_of_participants']

            if reservation_time < timezone.now():
                messages.error(request, '예약 시간은 현재 시간보다 이후여야 합니다.')
                form.add_error('reservation_time', '지난 시간은 예약할 수 없습니다.')
                
            existing_reservation = Reservation.objects.filter(
                theme=theme,
                reservation_time=reservation_time,
                status__in=['Confirmed', 'CheckedIn']
            ).exists()
            
            if existing_reservation:
                messages.error(request, '해당 시간은 이미 예약이 마감되었습니다.')
                form.add_error('reservation_time', '이미 예약된 시간입니다.')

            if form.errors:
                 context = {'form': form, 'theme': theme}
                 return render(request, 'booking/reservation_form.html', context)

            try:
                reservation = form.save(commit=False)
                reservation.member = request.user
                reservation.theme = theme
                
                total_price = theme.price * num_of_participants
                reservation.total_price = total_price
                
                reservation.save()
                
                Payment.objects.create(
                    reservation=reservation,
                    payment_method='가상 카드',
                    amount=total_price,
                    payment_status='Paid'
                )
                
                messages.success(request, f'"{theme.name}" 예약이 완료되었습니다.')
                return redirect('reservation-complete', reservation_id=reservation.reservation_id)
            
            except Exception as e:
                messages.error(request, f'예약 중 오류가 발생했습니다. (Error: {e})')
                
    else:
        form = ReservationForm()
    
    context = {
        'form': form,
        'theme': theme,
    }
    return render(request, 'booking/reservation_form.html', context)

@login_required
def reservation_complete_view(request, reservation_id):
    reservation = get_object_or_404(
        Reservation, 
        reservation_id=reservation_id, 
        member=request.user
    )
    context = {
        'reservation': reservation,
    }
    return render(request, 'booking/reservation_complete.html', context)

@login_required
@require_POST
def reservation_cancel_view(request, reservation_id):
    reservation = get_object_or_404(Reservation, reservation_id=reservation_id, member=request.user)
    
    if reservation.status != 'Confirmed':
        messages.error(request, "취소할 수 없는 예약 상태입니다.")
        return redirect('my-page')

    reservation.status = 'Cancelled'
    reservation.save()
    
    messages.success(request, "예약이 취소되었습니다.")
    return redirect('my-page')

# 4. 리뷰 (Review)
@login_required
def review_create_view(request, reservation_id):
    reservation = get_object_or_404(Reservation, reservation_id=reservation_id)

    if reservation.member != request.user:
        raise PermissionDenied("본인의 예약에 대해서만 리뷰를 작성할 수 있습니다.")
    
    if reservation.status != 'Completed':
        raise Http404("이용 완료된 예약 건에 대해서만 리뷰 작성이 가능합니다.")
        
    try:
        if reservation.review:
             return redirect('review-update', review_id=reservation.review.review_id)
    except Review.DoesNotExist:
        pass

    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.member = request.user
            review.reservation = reservation
            review.save()
            return redirect('theme-detail', theme_id=reservation.theme.theme_id)
    else:
        form = ReviewForm()

    context = {
        'form': form,
        'reservation': reservation,
        'theme': reservation.theme,
    }
    return render(request, 'booking/review_form.html', context)

@login_required
def review_update_view(request, review_id):
    review = get_object_or_404(Review, review_id=review_id)
    
    if review.member != request.user:
        raise PermissionDenied("본인의 리뷰만 수정할 수 있습니다.")
        
    if request.method == 'POST':
        form = ReviewForm(request.POST, instance=review)
        if form.is_valid():
            form.save()
            return redirect('theme-detail', theme_id=review.reservation.theme.theme_id)
    else:
        form = ReviewForm(instance=review) 

    context = {
        'form': form,
        'review': review,
        'theme': review.reservation.theme,
    }
    return render(request, 'booking/review_form.html', context)

# 관리자 대시보드 (Manager Dashboard)
@login_required
def theme_manager_dashboard_view(request):
    """테마 관리자 대시보드"""
    if request.user.role not in ['ThemeManager', 'BranchManager', 'Admin']:
        raise PermissionDenied("테마 관리자 권한이 필요합니다.")
    
    # 시설 문제 보고 처리 (POST)
    if request.method == 'POST':
        issue_form = IssueReportForm(request.POST)
        if issue_form.is_valid():
            issue = issue_form.save(commit=False)
            issue.reported_by_member = request.user
            issue.status = 'Reported'
            issue.save()
            return redirect('theme-manager-dashboard')
    else:
        issue_form = IssueReportForm()

    today = date.today()
    
    if request.user.role == 'BranchManager':
        reservations = Reservation.objects.filter(
            reservation_time__date=today
        ).select_related('member', 'theme', 'theme__branch').order_by('reservation_time')
    else:
        reservations = Reservation.objects.filter(
            reservation_time__date=today
        ).select_related('member', 'theme', 'theme__branch').order_by('reservation_time')
    
    stats = {
        'total': reservations.count(),
        'confirmed': reservations.filter(status='Confirmed').count(),
        'checked_in': reservations.filter(status='CheckedIn').count(),
        'completed': reservations.filter(status='Completed').count(),
        'cancelled': reservations.filter(status='Cancelled').count(),
    }
    
    recent_issues = IssueReport.objects.filter(
        status__in=['Reported', 'InProgress']
    ).select_related('theme', 'reported_by_member').order_by('-reported_at')[:5]

    themes = Theme.objects.all().order_by('branch', 'name')
    
    context = {
        'reservations': reservations,
        'stats': stats,
        'recent_issues': recent_issues,
        'today': today,
        'issue_form': issue_form,
        'themes': themes,
    }
    
    return render(request, 'booking/manager_dashboard.html', context)

@login_required
def branch_manager_dashboard_view(request):
    """지점 관리자 대시보드"""
    if request.user.role not in ['BranchManager', 'Admin']:
        raise PermissionDenied("지점 관리자 권한이 필요합니다.")
    
    today = date.today()
    month_start = today.replace(day=1)
    if today.month == 12:
        month_end = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
    else:
        month_end = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
    
    branches = Branch.objects.filter(is_active=True)
    
    branch_sales = []
    for branch in branches:
        sales = Payment.objects.filter(
            reservation__theme__branch=branch,
            payment_status='Paid',
            paid_at__date__gte=month_start,
            paid_at__date__lte=month_end
        ).aggregate(
            total=Sum('amount'),
            count=Count('payment_id')
        )
        
        # 0으로 나누기 방지 및 평균 계산 (템플릿 계산 오류 해결)
        total = sales['total'] or 0
        count = sales['count'] or 0
        if count > 0:
            avg_sales = total / count
        else:
            avg_sales = 0

        branch_sales.append({
            'branch': branch,
            'total_sales': total,
            'reservation_count': count,
            'avg_sales': avg_sales,
        })
    
    week_start = today
    week_end = today + timedelta(days=7)
    
    schedules = Schedule.objects.filter(
        work_date__gte=week_start,
        work_date__lte=week_end
    ).select_related('member', 'branch', 'assigned_theme').order_by('work_date', 'start_time')
    
    theme_stats = Theme.objects.filter(
        is_active=True
    ).annotate(
        reservation_count=Count(
            'reservation',
            filter=Q(
                reservation__reservation_time__date__gte=month_start,
                reservation__reservation_time__date__lte=month_end,
                reservation__status='Completed'
            )
        ),
        avg_rating=Avg(
            'reservation__review__rating',
            filter=Q(reservation__status='Completed')
        )
    ).order_by('-reservation_count')[:10]
    
    context = {
        'branch_sales': branch_sales,
        'schedules': schedules,
        'theme_stats': theme_stats,
        'month_start': month_start,
        'month_end': month_end,
        'week_start': week_start,
        'week_end': week_end,
    }
    
    return render(request, 'booking/manager_stats.html', context)

@login_required
def branch_theme_update_view(request, theme_id):
    if request.user.role not in ['BranchManager', 'Admin']:
        raise PermissionDenied("지점 관리자 권한이 필요합니다.")
        
    theme = get_object_or_404(Theme, theme_id=theme_id)
    
    # 담당 지점인지 확인
    if request.user.role == 'BranchManager':
        has_permission = BranchAssignment.objects.filter(
            member=request.user,
            branch=theme.branch
        ).exists()
        
        if not has_permission:
            raise PermissionDenied("본인이 담당하는 지점의 테마만 수정할 수 있습니다.")

    if request.method == 'POST':
        form = BranchThemeUpdateForm(request.POST, instance=theme)
        if form.is_valid():
            form.save()
            messages.success(request, "테마 정보가 수정되었습니다.")
            return redirect('branch-manager-stats')
    else:
        form = BranchThemeUpdateForm(instance=theme)
        
    context = {'form': form, 'theme': theme}
    return render(request, 'booking/theme_update_form.html', context)

# 관리자 액션 (입실, 완료, 노쇼, 문제 보고, 스케줄 추가)
@login_required
def checkin_update_view(request, reservation_id):
    if request.user.role not in ['ThemeManager', 'BranchManager', 'Admin']:
        raise PermissionDenied("테마 관리자 권한이 필요합니다.")
    
    reservation = get_object_or_404(Reservation, reservation_id=reservation_id)
    
    if reservation.status == 'Confirmed':
        reservation.status = 'CheckedIn'
        reservation.save()
    
    return redirect('theme-manager-dashboard')

@login_required
def complete_reservation_view(request, reservation_id):
    if request.user.role not in ['ThemeManager', 'BranchManager', 'Admin']:
        raise PermissionDenied("테마 관리자 권한이 필요합니다.")
    
    reservation = get_object_or_404(Reservation, reservation_id=reservation_id)
    
    if request.method == 'POST':
        hint_count = request.POST.get('hint_count', 0)
        is_success = request.POST.get('is_success') == 'on'
        clear_time = request.POST.get('clear_time', None)
        
        reservation.status = 'Completed'
        reservation.hint_count = int(hint_count)
        reservation.is_success = is_success
        
        if clear_time:
            reservation.clear_time = int(clear_time) * 60
        
        reservation.save()
        
        return redirect('theme-manager-dashboard')
    
    context = {
        'reservation': reservation,
    }
    return render(request, 'booking/complete_reservation.html', context)

@login_required
def noshow_update_view(request, reservation_id):
    if request.user.role not in ['ThemeManager', 'BranchManager', 'Admin']:
        raise PermissionDenied("권한이 없습니다.")
    
    reservation = get_object_or_404(Reservation, reservation_id=reservation_id)
    
    if reservation.status == 'Confirmed':
        reservation.status = 'NoShow'
        reservation.save()
    
    return redirect('theme-manager-dashboard')

@login_required
def issue_create_view(request):
    if request.user.role not in ['ThemeManager', 'BranchManager', 'Admin']:
        raise PermissionDenied("관리자 권한이 필요합니다.")
        
    if request.method == 'POST':
        form = IssueReportForm(request.POST)
        if form.is_valid():
            issue = form.save(commit=False)
            issue.reported_by_member = request.user
            issue.status = 'Reported'
            issue.save()
            return redirect('theme-manager-dashboard')
    else:
        form = IssueReportForm()
        
    context = {'form': form}
    return render(request, 'booking/issue_form.html', context)

@login_required
def schedule_create_view(request):
    if request.user.role not in ['BranchManager', 'Admin']:
        raise PermissionDenied("지점 관리자 권한이 필요합니다.")
        
    if request.method == 'POST':
        form = ScheduleForm(request.POST)
        if form.is_valid():
            schedule = form.save(commit=False)
            # 지점 정보가 없으면 첫 번째 활성 지점으로 자동 할당
            if not schedule.branch_id:
                 first_branch = Branch.objects.filter(is_active=True).first()
                 if first_branch:
                     schedule.branch = first_branch
            schedule.save()
            return redirect('branch-manager-stats')
    else:
        form = ScheduleForm()
        
    context = {'form': form}
    return render(request, 'booking/schedule_form.html', context)

# 공지사항 (Notice)
def notice_list_view(request):
    notices = Notice.objects.all().order_by('-created_at')
    context = {'notices': notices}
    return render(request, 'booking/notice_list.html', context)

# 리뷰 삭제 (Review Delete)
@login_required
@require_POST # 리뷰 삭제는 작성자만 가능하도록 권한 설정함
def review_delete_view(request, review_id):
    review = get_object_or_404(Review, review_id=review_id)

    if review.member != request.user:
        raise PermissionDenied("본인의 리뷰만 삭제할 수 있습니다.")
    
    theme_id = review.reservation.theme.theme_id
    review.delete()
    messages.success(request, "리뷰가 삭제되었습니다.")

    return redirect('my-page') # 삭제 후 마이페이지로 이동

@login_required
@require_POST
def theme_status_toggle_view(request, theme_id):
    """테마 상태를 '운영 가능' <-> '점검 중'으로 변경"""
    if request.user.role not in ['ThemeManager', 'BranchManager', 'Admin']:
        raise PermissionDenied("권한이 없습니다.")
        
    theme = get_object_or_404(Theme, theme_id=theme_id)
    
    if theme.status == 'Ready':
        theme.status = 'Maintenance'
        messages.warning(request, f"'{theme.name}' 테마가 [점검 중] 상태로 변경되었습니다. (예약 불가)")
    else:
        theme.status = 'Ready'
        messages.success(request, f"'{theme.name}' 테마가 [운영 가능] 상태로 변경되었습니다.")
    
    theme.save()
    
    return redirect('theme-manager-dashboard')