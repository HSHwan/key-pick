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
from .forms import ReviewForm, ReservationForm
from .models import Theme, Branch, Member, Reservation, Review, IssueReport, Payment, Schedule
from datetime import date, timedelta

# 테마 목록 뷰
def theme_list_view(request):
    search_query = request.GET.get('search_query', '')
    branch_id = request.GET.get('branch', '')
    
    themes = Theme.objects.filter(is_active=True, status='Ready')
    
    if search_query:
        themes = themes.filter(
            Q(name__icontains=search_query) | 
            Q(genre__icontains=search_query)
        )
    if branch_id:
        themes = themes.filter(branch_id=branch_id)
        
    branches = Branch.objects.filter(is_active=True)

    context = {
        'themes': themes,
        'branches': branches,
        'selected_branch': branch_id,
        'search_query': search_query,
    }
    return render(request, 'booking/theme_list.html', context)

# 테마 상세 뷰
def theme_detail_view(request, theme_id):
    theme = get_object_or_404(Theme, theme_id=theme_id, is_active=True)
    
    # 해당 테마에 달린 모든 리뷰들을 가져옴
    reviews = Review.objects.filter(reservation__theme=theme)
    
    context = {
        'theme': theme,
        'reviews': reviews,
    }
    return render(request, 'booking/theme_detail.html', context)

# 리뷰 작성 뷰
@login_required # 로그인 필수
def review_create_view(request, reservation_id):
    # 1. 리뷰를 작성할 대상 예약(Reservation)을 찾음
    reservation = get_object_or_404(Reservation, reservation_id=reservation_id)

    # 2. 권한 확인 (본인의 예약인지? 이용 완료했는지?)
    if reservation.member != request.user:
        raise PermissionDenied("본인의 예약에 대해서만 리뷰를 작성할 수 있습니다.")
    
    if reservation.status != 'Completed':
        raise Http404("이용 완료된 예약 건에 대해서만 리뷰 작성이 가능합니다.")
        
    # 3. 이미 리뷰를 작성했는지 확인 (OneToOneField 덕분에 가능)
    try:
        if reservation.review: # 이미 리뷰가 존재하면
             return redirect('review-update', review_id=reservation.review.review_id)
    except Review.DoesNotExist:
        pass # 리뷰가 없으면 통과

    # 4. 폼 처리 (GET / POST)
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            # commit=False: DB에 바로 저장하지 않고, 추가 정보(member, reservation)를 먼저 채움
            review = form.save(commit=False)
            review.member = request.user
            review.reservation = reservation
            review.save()
            # 리뷰 작성 완료 후, 테마 상세 페이지로 이동
            return redirect('theme-detail', theme_id=reservation.theme.theme_id)
    else:
        form = ReviewForm() # GET 요청 시 빈 폼

    context = {
        'form': form,
        'reservation': reservation,
        'theme': reservation.theme,
    }
    return render(request, 'booking/review_form.html', context)

# 리뷰 수정 뷰
@login_required
def review_update_view(request, review_id):
    review = get_object_or_404(Review, review_id=review_id)
    
    # 권한 확인 (본인의 리뷰인지?)
    if review.member != request.user:
        raise PermissionDenied("본인의 리뷰만 수정할 수 있습니다.")
        
    if request.method == 'POST':
        # instance=review: 기존 리뷰 객체 위에 폼 데이터를 덮어씀 (수정)
        form = ReviewForm(request.POST, instance=review)
        if form.is_valid():
            form.save()
            # 수정 완료 후, 테마 상세 페이지로 이동
            return redirect('theme-detail', theme_id=review.reservation.theme.theme_id)
    else:
        # GET 요청 시, 기존 리뷰 내용이 채워진 폼
        form = ReviewForm(instance=review) 

    context = {
        'form': form,
        'review': review, # 템플릿에서 '수정'임을 명시하기 위해 전달
        'theme': review.reservation.theme,
    }
    return render(request, 'booking/review_form.html', context)

def signup_view(request):
    """
    회원가입 뷰
    - GET 요청: 회원가입 템플릿(signup.html)을 보여줍니다.
    - POST 요청: 폼 데이터를 받아 회원가입을 처리합니다.
    """
    
    # 1. POST 요청 (폼 데이터가 제출되었을 때)
    if request.method == 'POST':
        # 2. signup.html의 <form>에서 name 속성으로 보낸 데이터를 추출
        login_id = request.POST.get('login_id')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')
        name = request.POST.get('name')
        phone = request.POST.get('phone')
        
        # 3. 데이터 유효성 검사 (Validation)
        context = {} # 템플릿에 오류 메시지를 전달하기 위한 변수

        # 3-1. 모든 필드가 채워졌는지 확인
        if not (login_id and password and password_confirm and name and phone):
            context['error'] = '모든 칸을 입력해주세요.'
            return render(request, 'booking/signup.html', context)

        # 3-2. 비밀번호와 비밀번호 확인이 일치하는지
        if password != password_confirm:
            context['error'] = '비밀번호가 일치하지 않습니다.'
            return render(request, 'booking/signup.html', context)
        
        # 3-3. (선택) ID 또는 연락처 중복 확인
        if Member.objects.filter(login_id=login_id).exists():
            context['error'] = '이미 사용 중인 ID입니다.'
            return render(request, 'booking/signup.html', context)
        
        if Member.objects.filter(phone=phone).exists():
            context['error'] = '이미 등록된 연락처입니다.'
            return render(request, 'booking/signup.html', context)

        # 4. 사용자 생성
        try:
            # booking/models.py의 MemberManager.create_user 호출
            user = Member.objects.create_user(
                login_id=login_id,
                password=password,
                name=name,
                phone=phone,
                role='Customer'  # 고객(Customer)으로 역할 고정
            )
            
            # 5. 가입 성공 시 자동 로그인
            # (주의: authenticate는 login_id 필드를 username 매개변수로 받습니다.
            #       Member 모델의 USERNAME_FIELD='login_id' 설정 덕분입니다.)
            user_auth = authenticate(request, username=login_id, password=password)
            if user_auth:
                login(request, user_auth)
            
            # 6. 'theme-list' (테마 목록) 페이지로 이동
            return redirect('theme-list') 

        except Exception as e:
            # 기타 데이터베이스 오류 등
            context['error'] = f'가입 중 오류가 발생했습니다: {e}'
            return render(request, 'booking/signup.html', context)

    # 2. GET 요청 (그냥 /signup/ 페이지에 처음 방문했을 때)
    else:
        # 비어있는 회원가입 템플릿(signup.html)을 보여줌
        return render(request, 'booking/signup.html')

def login_view(request):
    """
    로그인 뷰
    - GET 요청: 로그인 템플릿(login.html)을 보여줍니다.
    - POST 요청: 폼 데이터를 받아 로그인을 처리합니다.
    """
    context = {}

    # 1. POST 요청 (폼 데이터가 제출되었을 때)
    if request.method == 'POST':
        # 2. login.html의 <form>에서 name 속성으로 보낸 데이터를 추출
        # (주의: login.html에서 login_id를 'username'이라는 name으로 보냈다면)
        login_id = request.POST.get('username') 
        password = request.POST.get('password')

        # 3. 데이터 유효성 검사
        if not (login_id and password):
            context['error'] = 'ID와 비밀번호를 모두 입력해주세요.'
            return render(request, 'booking/login.html', context)

        # 4. 사용자 인증 (Authentication)
        #    Member 모델의 USERNAME_FIELD='login_id' 설정 덕분에
        #    'username' 매개변수에 login_id 값을 전달합니다.
        user = authenticate(request, username=login_id, password=password)

        # 5. 인증 성공/실패 처리
        if user is not None:
            # 6. 인증 성공! 세션에 사용자를 로그인시킴
            login(request, user)
            
            # 7. 'theme-list' (테마 목록) 페이지로 이동
            return redirect('theme-list')
        else:
            # 8. 인증 실패 (ID가 없거나, 비밀번호가 틀림)
            context['error'] = '로그인 ID 또는 비밀번호가 올바르지 않습니다.'
            return render(request, 'booking/login.html', context)

    # 2. GET 요청 (그냥 /login/ 페이지에 처음 방문했을 때)
    else:
        # 비어있는 로그인 템플릿(login.html)을 보여줌
        return render(request, 'booking/login.html')

@login_required # 로그인이 된 사용자만 로그아웃할 수 있습니다.
def logout_view(request):
    """
    로그아웃 뷰.
    템플릿(HTML)을 보여주지 않고, 로그아웃 로직만 처리한 뒤
    'theme-list' (테마 목록) 페이지로 즉시 이동시킵니다.
    """
    # 1. Django 세션에서 사용자를 로그아웃시킵니다.
    logout(request)
    
    # 2. 'theme-list'라는 이름의 URL로 사용자를 이동시킵니다.
    #    (이 URL은 booking/urls.py에 정의되어 있습니다)
    return redirect('theme-list') 

@login_required 
def my_page_view(request):
    """
    마이페이지 뷰.
    로그인한 사용자의 예약 목록과 리뷰 목록을 조회하여
    'my_page.html' 템플릿으로 전달합니다.
    """
    
    # 1. 현재 로그인한 사용자(request.user)의 예약 목록을 조회합니다.
    #    제안서 기능: '본인의 예약 내역을 확인'
    reservations = Reservation.objects.filter(
        member=request.user
    ).order_by('-reservation_time') # 최근 예약이 위로 오도록 정렬

    # 2. 현재 로그인한 사용자의 리뷰 목록을 조회합니다.
    #    제안서 기능: '본인이 작성한 리뷰를 관리'
    reviews = Review.objects.filter(
        member=request.user
    ).order_by('-created_at') # 최근 리뷰가 위로 오도록 정렬

    # 3. 템플릿에 전달할 context 데이터를 만듭니다.
    context = {
        'reservations': reservations,
        'reviews': reviews,
    }
    
    # 4. 템플릿을 렌더링하여 반환합니다.
    return render(request, 'booking/my_page.html', context)

# 예약 생성 뷰
@login_required # 로그인 필수
@transaction.atomic # 트랜잭션 보장 (예약/결제 로직)
def reservation_create_view(request, theme_id):
    """
    테마 예약 및 결제 처리 뷰 (GET: 폼, POST: 처리)
    """
    theme = get_object_or_404(Theme, theme_id=theme_id, is_active=True, status='Ready')
    
    if request.method == 'POST':
        form = ReservationForm(request.POST)
        if form.is_valid():
            reservation_time = form.cleaned_data['reservation_time']
            num_of_participants = form.cleaned_data['num_of_participants']

            # --- 유효성 검사 (Validation) ---
            # 1. 과거 시간 검사
            if reservation_time < timezone.now():
                messages.error(request, '예약 시간은 현재 시간보다 이후여야 합니다.')
                form.add_error('reservation_time', '지난 시간은 예약할 수 없습니다.')
                
            # 2. 중복 예약 검사 (DB에서 해당 테마, 해당 시간에 확정된 예약이 있는지 확인)
            existing_reservation = Reservation.objects.filter(
                theme=theme,
                reservation_time=reservation_time,
                status__in=['Confirmed', 'CheckedIn'] # '확정' 또는 '입실' 상태
            ).exists()
            
            if existing_reservation:
                messages.error(request, '해당 시간은 이미 예약이 마감되었습니다.')
                form.add_error('reservation_time', '이미 예약된 시간입니다.')

            # 폼 유효성 검사 실패 시, 폼과 에러 메시지를 다시 렌더링
            if form.errors:
                 context = {'form': form, 'theme': theme}
                 return render(request, 'booking/reservation_form.html', context)

            # --- 트랜잭션 시작 (모두 성공 또는 모두 실패) ---
            try:
                # 1. Reservation 객체 생성 (아직 DB 저장X)
                reservation = form.save(commit=False)
                reservation.member = request.user
                reservation.theme = theme
                
                # 2. 총 가격 계산 (기본 가격 * 인원)
                total_price = theme.price * num_of_participants
                reservation.total_price = total_price
                
                # 3. 예약 저장 (Reservation INSERT)
                reservation.save()
                
                # 4. Payment 객체 생성 (가상 결제 처리)
                # (실제 프로젝트에서는 여기서 PG사 API를 호출하고 콜백을 받음)
                Payment.objects.create(
                    reservation=reservation,
                    payment_method='가상 카드', # 실제로는 PG사에서 받은 정보
                    amount=total_price,
                    payment_status='Paid'
                )
                
                # 5. 성공 메시지 및 완료 페이지로 리다이렉트
                messages.success(request, f'"{theme.name}" 예약이 완료되었습니다.')
                return redirect('reservation-complete', reservation_id=reservation.reservation_id)
            
            except Exception as e:
                # 트랜잭션 중 오류 발생 시 롤백(Rollback)됨
                messages.error(request, f'예약 중 오류가 발생했습니다. (Error: {e})')
                
    else: # GET 요청 시 (예약하기 버튼 클릭)
        form = ReservationForm()
    
    context = {
        'form': form,
        'theme': theme,
    }
    return render(request, 'booking/reservation_form.html', context)

# 예약 완료 뷰
@login_required
def reservation_complete_view(request, reservation_id):
    """
    예약 완료 후 보여줄 확인 페이지
    """
    # 본인의 예약만 조회 가능하도록 `member=request.user` 조건 추가
    reservation = get_object_or_404(
        Reservation, 
        reservation_id=reservation_id, 
        member=request.user
    )
    context = {
        'reservation': reservation,
    }
    return render(request, 'booking/reservation_complete.html', context)

# 예약 취소 뷰
@login_required
@require_POST # POST 요청만 허용
def reservation_cancel_view(request, reservation_id):
    # 본인의 예약인지 확인
    reservation = get_object_or_404(Reservation, reservation_id=reservation_id, member=request.user)
    
    # 이미 취소되었거나 완료된 예약인지 확인
    if reservation.status != 'Confirmed':
        messages.error(request, "취소할 수 없는 예약 상태입니다.")
        return redirect('my-page') # 마이페이지 URL 이름 가정

    # 상태 변경 (환불 로직은 여기에 추가 가능)
    reservation.status = 'Cancelled'
    reservation.save()
    
    messages.success(request, "예약이 취소되었습니다.")
    return redirect('my-page') # 마이페이지로 리다이렉트

@login_required
def theme_manager_dashboard_view(request):
    """
    테마 관리자 대시보드
    - 오늘 예약 현황 조회
    - 입실 관리 (예약 상태 변경)
    - 시설 문제 보고
    """
    # 권한 확인
    if request.user.role not in ['ThemeManager', 'BranchManager', 'Admin']:
        raise PermissionDenied("테마 관리자 권한이 필요합니다.")
    
    # 오늘 날짜
    today = date.today()
    
    # 오늘의 예약 목록 (지점 관리자는 자신의 지점만, 관리자는 전체)
    if request.user.role == 'BranchManager':
        # 지점 관리자: 자신이 관리하는 지점의 예약만
        # (실제로는 Member 모델에 managed_branch 필드가 필요하지만, 여기서는 간단히 처리)
        reservations = Reservation.objects.filter(
            reservation_time__date=today
        ).select_related('member', 'theme', 'theme__branch').order_by('reservation_time')
    else:
        # 테마 관리자 또는 Admin: 전체 예약
        reservations = Reservation.objects.filter(
            reservation_time__date=today
        ).select_related('member', 'theme', 'theme__branch').order_by('reservation_time')
    
    # 예약 상태별 통계
    stats = {
        'total': reservations.count(),
        'confirmed': reservations.filter(status='Confirmed').count(),
        'checked_in': reservations.filter(status='CheckedIn').count(),
        'completed': reservations.filter(status='Completed').count(),
        'cancelled': reservations.filter(status='Cancelled').count(),
    }
    
    # 최근 문제 보고 (미해결 건만)
    recent_issues = IssueReport.objects.filter(
        status__in=['Reported', 'InProgress']
    ).select_related('theme', 'reported_by_member').order_by('-reported_at')[:5]
    
    context = {
        'reservations': reservations,
        'stats': stats,
        'recent_issues': recent_issues,
        'today': today,
    }
    
    return render(request, 'booking/manager_dashboard.html', context)


@login_required
def branch_manager_dashboard_view(request):
    """
    지점 관리자 대시보드
    - 지점 매출 통계
    - 스케줄 관리
    - 테마별 예약 현황
    """
    # 권한 확인
    if request.user.role not in ['BranchManager', 'Admin']:
        raise PermissionDenied("지점 관리자 권한이 필요합니다.")
    
    # 이번 달 시작/종료 날짜
    today = date.today()
    month_start = today.replace(day=1)
    if today.month == 12:
        month_end = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
    else:
        month_end = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
    
    # 전체 지점 목록
    branches = Branch.objects.filter(is_active=True)
    
    # 이번 달 매출 통계 (지점별)
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
        
        branch_sales.append({
            'branch': branch,
            'total_sales': sales['total'] or 0,
            'reservation_count': sales['count'] or 0,
        })
    
    # 이번 주 스케줄 (오늘부터 7일)
    week_start = today
    week_end = today + timedelta(days=7)
    
    schedules = Schedule.objects.filter(
        work_date__gte=week_start,
        work_date__lte=week_end
    ).select_related('member', 'branch', 'assigned_theme').order_by('work_date', 'start_time')
    
    # 테마별 예약 현황 (이번 달)
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
def checkin_update_view(request, reservation_id):
    """
    예약 상태를 '입실 완료'로 변경
    """
    if request.user.role not in ['ThemeManager', 'BranchManager', 'Admin']:
        raise PermissionDenied("테마 관리자 권한이 필요합니다.")
    
    reservation = get_object_or_404(Reservation, reservation_id=reservation_id)
    
    if reservation.status == 'Confirmed':
        reservation.status = 'CheckedIn'
        reservation.save()
    
    return redirect('theme-manager-dashboard')


@login_required
def complete_reservation_view(request, reservation_id):
    """
    예약을 '이용 완료' 상태로 변경
    (힌트 사용 횟수, 탈출 성공 여부, 클리어 시간 입력)
    """
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
            # 분 단위로 받아서 초 단위로 저장
            reservation.clear_time = int(clear_time) * 60
        
        reservation.save()
        
        return redirect('theme-manager-dashboard')
    
    context = {
        'reservation': reservation,
    }
    
    return render(request, 'booking/complete_reservation.html', context)
