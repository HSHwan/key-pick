# booking/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # 'http://.../themes/' URL을 views.theme_list 함수에 연결
    # name='theme-list'는 HTML 템플릿에서 이 URL을 부를 때 사용할 별명
    path('themes/', views.theme_list, name='theme-list'),
]