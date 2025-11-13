# booking/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import Http404
from .models import Theme, Branch, Review, Reservation
from .forms import ReviewForm # 방금 만든 폼 import

# 테마 목록 뷰
def theme_list_view(request):
    search_query = request.GET.get('search_query', '')
    branch_id = request.GET.get('branch', '')
    
    themes = Theme.objects.filter(is_active=True, status='Ready')
    
    if search_query:
        themes = themes.filter(
            models.Q(name__icontains=search_query) | 
            models.Q(genre__icontains=search_query)
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