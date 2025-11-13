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
]