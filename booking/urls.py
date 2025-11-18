# booking/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('my-page/', views.my_page_view, name='my-page'),
    path('themes/', views.theme_list_view, name='theme-list'),
    path('themes/<int:theme_id>/', views.theme_detail_view, name='theme-detail'),
    path('review/create/<int:reservation_id>/', views.review_create_view, name='review-create'),
    path('review/update/<int:review_id>/', views.review_update_view, name='review-update'),
    path('reservation/create/<int:theme_id>/', views.reservation_create_view, name='reservation-create'),
    path('reservation/complete/<int:reservation_id>/', views.reservation_complete_view, name='reservation-complete'),
    path('reservation/cancel/<int:reservation_id>/', views.reservation_cancel_view, name='reservation-cancel'),
    path('manager/dashboard/', views.theme_manager_dashboard_view, name='theme-manager-dashboard'),
    path('manager/stats/', views.branch_manager_dashboard_view, name='branch-manager-stats'),
    path('manager/checkin/<int:reservation_id>/', views.checkin_update_view, name='checkin-update'),
    path('manager/complete/<int:reservation_id>/', views.complete_reservation_view, name='complete-reservation'),
]