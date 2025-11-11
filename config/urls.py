# escape_room_project/urls.py
from django.contrib import admin
from django.urls import path, include # include 추가

urlpatterns = [
    path('admin/', admin.site.urls),
    # '' (루트) 경로를 포함한 모든 booking 관련 URL을
    # booking/urls.py 파일에서 관리하도록 위임
    path('', include('booking.urls')), 
]