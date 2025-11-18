# booking/admin.py
from django.contrib import admin
from django.utils.html import format_html
from . import models

# 1. Member (회원)
@admin.register(models.Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ('login_id', 'name', 'phone', 'role', 'is_active', 'created_at')
    list_filter = ('role', 'is_active', 'created_at')
    search_fields = ('login_id', 'name', 'phone')
    ordering = ('-created_at',)
    
    # 읽기 전용 필드 (수정 불가)
    readonly_fields = ('created_at', 'last_login')
    
    # 필드 그룹화
    fieldsets = (
        ('기본 정보', {
            'fields': ('login_id', 'name', 'phone', 'role')
        }),
        ('권한 및 상태', {
            'fields': ('is_active', 'is_staff', 'is_admin')
        }),
        ('기타', {
            'fields': ('created_at', 'last_login'),
            'classes': ('collapse',)  # 접을 수 있게
        }),
    )

# 2. Branch (지점)
@admin.register(models.Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ('branch_name', 'location', 'phone', 'is_active', 'theme_count')
    list_filter = ('is_active',)
    search_fields = ('branch_name', 'location')
    
    def theme_count(self, obj):
        """해당 지점의 테마 개수"""
        return obj.theme_set.count()
    theme_count.short_description = '테마 수'

# 3. Theme (테마)
@admin.register(models.Theme)
class ThemeAdmin(admin.ModelAdmin):
    list_display = ('name', 'branch', 'genre', 'difficulty', 'price', 'discount_rate', 'status_badge', 'is_active')
    list_filter = ('branch', 'genre', 'difficulty', 'is_active', 'status')
    search_fields = ('name', 'branch__branch_name', 'genre')
    ordering = ('branch', 'name')
    
    # 필드 그룹화
    fieldsets = (
        ('기본 정보', {
            'fields': ('branch', 'name', 'genre', 'difficulty', 'duration')
        }),
        ('가격 정보', {
            'fields': ('price', 'discount_rate')
        }),
        ('설명 및 상태', {
            'fields': ('description', 'status', 'is_active')
        }),
    )
    
    def status_badge(self, obj):
        """테마 상태를 색상으로 표시"""
        if obj.status == 'Ready':
            color = 'green'
            text = '운영 가능'
        else:
            color = 'red'
            text = '점검 중'
        return format_html(
            '<span style="color: {}; font-weight: bold;">●</span> {}',
            color, text
        )
    status_badge.short_description = '상태'

# 4. Reservation (예약)
@admin.register(models.Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ('reservation_id', 'member_name', 'theme', 'reservation_time', 'status_badge', 'total_price', 'num_of_participants')
    list_filter = ('status', 'reservation_time', 'theme__branch')
    search_fields = ('member__name', 'theme__name', 'reservation_id')
    ordering = ('-reservation_time',)
    date_hierarchy = 'reservation_time'  # 날짜별 필터링
    
    readonly_fields = ('reservation_id',)
    
    def member_name(self, obj):
        return obj.member.name if obj.member else '탈퇴회원'
    member_name.short_description = '예약자'
    
    def status_badge(self, obj):
        """예약 상태를 색상으로 표시"""
        colors = {
            'Confirmed': 'blue',
            'CheckedIn': 'green',
            'Completed': 'gray',
            'Cancelled': 'red',
            'NoShow': 'orange',
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">●</span> {}',
            colors.get(obj.status, 'black'), obj.get_status_display()
        )
    status_badge.short_description = '상태'

# 5. Payment (결제)
@admin.register(models.Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('payment_id', 'reservation', 'amount', 'payment_method', 'payment_status', 'paid_at')
    list_filter = ('payment_status', 'payment_method', 'paid_at')
    search_fields = ('reservation__reservation_id', 'reservation__member__name')
    ordering = ('-paid_at',)
    date_hierarchy = 'paid_at'
    
    readonly_fields = ('payment_id', 'paid_at')

# 6. Review (리뷰)
@admin.register(models.Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('review_id', 'member_name', 'theme_name', 'rating_stars', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('member__name', 'reservation__theme__name', 'comment')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    
    readonly_fields = ('review_id', 'created_at')
    
    def member_name(self, obj):
        return obj.member.name if obj.member else '탈퇴회원'
    member_name.short_description = '작성자'
    
    def theme_name(self, obj):
        return obj.reservation.theme.name
    theme_name.short_description = '테마'
    
    def rating_stars(self, obj):
        """별점을 별 아이콘으로 표시"""
        return '⭐' * obj.rating
    rating_stars.short_description = '별점'

# 7. Schedule (직원 스케줄)
@admin.register(models.Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ('work_date', 'member', 'branch', 'work_time', 'assigned_theme')
    list_filter = ('work_date', 'branch', 'member')
    search_fields = ('member__name', 'branch__branch_name')
    ordering = ('-work_date', 'start_time')
    date_hierarchy = 'work_date'
    
    def work_time(self, obj):
        return f"{obj.start_time.strftime('%H:%M')} ~ {obj.end_time.strftime('%H:%M')}"
    work_time.short_description = '근무 시간'

# 8. Notice (공지사항)
@admin.register(models.Notice)
class NoticeAdmin(admin.ModelAdmin):
    list_display = ('title', 'member', 'target_branch', 'created_at')
    list_filter = ('target_branch', 'created_at')
    search_fields = ('title', 'content')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    
    readonly_fields = ('created_at',)

# 9. IssueReport (시설 문제 보고)
@admin.register(models.IssueReport)
class IssueReportAdmin(admin.ModelAdmin):
    list_display = ('report_id', 'theme', 'reported_by', 'status_badge', 'reported_at')
    list_filter = ('status', 'theme__branch', 'reported_at')
    search_fields = ('theme__name', 'reported_by_member__name', 'issue_description')
    ordering = ('-reported_at',)
    date_hierarchy = 'reported_at'
    
    readonly_fields = ('report_id', 'reported_at')
    
    fieldsets = (
        ('보고 정보', {
            'fields': ('theme', 'reported_by_member', 'issue_description')
        }),
        ('처리 상태', {
            'fields': ('status',)
        }),
        ('기타', {
            'fields': ('reported_at',),
            'classes': ('collapse',)
        }),
    )
    
    def reported_by(self, obj):
        return obj.reported_by_member.name if obj.reported_by_member else '시스템'
    reported_by.short_description = '보고자'
    
    def status_badge(self, obj):
        """처리 상태를 색상으로 표시"""
        colors = {
            'Reported': 'red',
            'InProgress': 'orange',
            'Resolved': 'green',
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">●</span> {}',
            colors.get(obj.status, 'black'), obj.get_status_display()
        )
    status_badge.short_description = '상태'