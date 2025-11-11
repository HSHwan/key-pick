# booking/admin.py
from django.contrib import admin
from . import models

# Admin 사이트에 모델을 등록
# list_display 등을 추가하여 관리자 페이지를 커스터마이징
@admin.register(models.Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ('login_id', 'name', 'phone', 'role', 'is_active')
    list_filter = ('role', 'is_active')
    search_fields = ('login_id', 'name', 'phone')

@admin.register(models.Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ('branch_name', 'location', 'phone', 'is_active')
    search_fields = ('branch_name',)

@admin.register(models.Theme)
class ThemeAdmin(admin.ModelAdmin):
    list_display = ('name', 'branch', 'genre', 'difficulty', 'price', 'is_active', 'status')
    list_filter = ('branch', 'genre', 'difficulty', 'is_active', 'status')
    search_fields = ('name', 'branch__branch_name')

@admin.register(models.Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ('reservation_id', 'member', 'theme', 'reservation_time', 'status')
    list_filter = ('status', 'reservation_time', 'theme__branch')
    search_fields = ('member__name', 'theme__name')

@admin.register(models.Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('payment_id', 'reservation', 'amount', 'payment_status', 'paid_at')
    list_filter = ('payment_status',)

@admin.register(models.Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('review_id', 'member', 'reservation', 'rating', 'created_at')
    list_filter = ('rating',)
    search_fields = ('member__name',)

@admin.register(models.Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ('work_date', 'member', 'branch', 'start_time', 'end_time')
    list_filter = ('work_date', 'branch', 'member')

@admin.register(models.Notice)
class NoticeAdmin(admin.ModelAdmin):
    list_display = ('title', 'member', 'target_branch', 'created_at')
    list_filter = ('target_branch',)
    search_fields = ('title',)

@admin.register(models.IssueReport)
class IssueReportAdmin(admin.ModelAdmin):
    list_display = ('theme', 'reported_by_member', 'status', 'reported_at')
    list_filter = ('status', 'theme__branch')
    search_fields = ('theme__name',)