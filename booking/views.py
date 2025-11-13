# booking/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q 
from django.contrib.auth import logout, login, authenticate
from .models import Theme, Branch, Member, Reservation, Review

def theme_list(request):
    """
    고객용 테마 목록 조회 및 검색/필터링 뷰
    """
    
    # 1. 쿼리 파라미터(GET 요청) 받기
    # 예: /themes/?search_query=공포&branch=1
    search_query = request.GET.get('search_query', '')
    branch_id = request.GET.get('branch', '')
    
    # 2. 기본 쿼리셋 (활성화된 테마만)
    themes = Theme.objects.filter(is_active=True, status='Ready')
    
    # 3. 검색어(search_query)가 있으면 필터링
    if search_query:
        # 테마명 또는 장르에 검색어가 포함된 경우
        themes = themes.filter(
            Q(name__icontains=search_query) | 
            Q(genre__icontains=search_query)
        )
        
    # 4. 지점(branch)이 선택되었으면 필터링
    if branch_id:
        themes = themes.filter(branch_id=branch_id)
        
    # 5. 검색/필터링에 사용할 전체 지점 목록도 전달
    branches = Branch.objects.filter(is_active=True)

    # 6. context에 담아 템플릿으로 전달
    context = {
        'themes': themes,
        'branches': branches,
        'selected_branch': branch_id, # 사용자가 선택한 값 기억
        'search_query': search_query, # 사용자가 입력한 값 기억
    }
    
    # 'booking/theme_list.html' 템플릿을 사용하여 페이지를 렌더링
    return render(request, 'booking/theme_list.html', context)

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