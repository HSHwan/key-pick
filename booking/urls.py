# booking/urls.py
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    #메인 페이지 (접속 시 바로 테마 목록 보여주기)
    path('', views.theme_list_view, name='root'),

    # 회원가입 및 로그인
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('my-page/', views.my_page_view, name='my-page'),
    
    # 테마 및 리뷰
    path('themes/', views.theme_list_view, name='theme-list'),
    path('themes/<int:theme_id>/', views.theme_detail_view, name='theme-detail'),
    path('review/create/<int:reservation_id>/', views.review_create_view, name='review-create'),
    path('review/update/<int:review_id>/', views.review_update_view, name='review-update'),
    
    # 예약
    path('reservation/create/<int:theme_id>/', views.reservation_create_view, name='reservation-create'),
    path('reservation/complete/<int:reservation_id>/', views.reservation_complete_view, name='reservation-complete'),
    path('reservation/cancel/<int:reservation_id>/', views.reservation_cancel_view, name='reservation-cancel'),
    
    # 관리자 대시보드 (기본)
    path('manager/dashboard/', views.theme_manager_dashboard_view, name='theme-manager-dashboard'),
    path('manager/stats/', views.branch_manager_dashboard_view, name='branch-manager-stats'),
    path('manager/checkin/<int:reservation_id>/', views.checkin_update_view, name='checkin-update'),
    path('manager/complete/<int:reservation_id>/', views.complete_reservation_view, name='complete-reservation'),
    path('manager/theme/update/<int:theme_id>/', views.branch_theme_update_view, name='branch-theme-update'),
    
    # 관리자 추가
    path('manager/noshow/<int:reservation_id>/', views.noshow_update_view, name='noshow-update'),
    path('manager/issue/create/', views.issue_create_view, name='issue-create'),
    path('manager/schedule/create/', views.schedule_create_view, name='schedule-create'),
    
    # 공지사항
    path('notices/', views.notice_list_view, name='notice-list'),

    # 비밀번호 재설정
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='booking/password_reset.html'), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='booking/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='booking/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='booking/password_reset_complete.html'), name='password_reset_complete'),
]