# booking/views.py
from django.shortcuts import render
from .models import Theme, Branch

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
            models.Q(name__icontains=search_query) | 
            models.Q(genre__icontains=search_query)
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