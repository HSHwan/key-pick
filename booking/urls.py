# booking/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # 담당자 B의 작업 (이미 존재함)
    path('themes/', views.theme_list, name='theme-list'),
    
    # 담당자 A의 작업 (추가)
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('my-page/', views.my_page_view, name='my-page'),
]