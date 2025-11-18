# booking/models.py
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.core.validators import MinValueValidator, MaxValueValidator

# ----------------------------------------------------------------------
# 1. Member (회원) - Django 인증 시스템을 맞춤 설정 (Custom)
# ----------------------------------------------------------------------
class MemberManager(BaseUserManager):
    def create_user(self, login_id, name, phone, role='Customer', password=None):
        if not login_id:
            raise ValueError('Must have a login_id')
        
        user = self.model(
            login_id=login_id,
            name=name,
            phone=phone,
            role=role,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, login_id, name, phone, password):
        # 슈퍼유저는 role을 'Admin'으로 설정하여 생성
        return self.create_user(
            login_id=login_id,
            name=name,
            phone=phone,
            password=password,
            role='Admin',
        )

class Member(AbstractBaseUser):
    """
    DB 필드: member_id, login_id, password, name, phone, role, created_at
    (+ last_login은 AbstractBaseUser가 기본적으로 포함하지만, 사용하지 않아도 무방)
    """
    
    ROLE_CHOICES = (
        ('Customer', '고객'),
        ('ThemeManager', '테마 관리자'),
        ('BranchManager', '지점 관리자'),
        ('Admin', '총괄 관리자'),
    )

    member_id = models.AutoField(primary_key=True)
    login_id = models.CharField(max_length=100, unique=True, verbose_name="로그인 ID")
    name = models.CharField(max_length=50, verbose_name="이름")
    phone = models.CharField(max_length=20, unique=True, verbose_name="연락처")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='Customer', verbose_name="역할")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="가입일")

    objects = MemberManager()

    USERNAME_FIELD = 'login_id'
    REQUIRED_FIELDS = ['name', 'phone']

    def __str__(self):
        return f"[{self.get_role_display()}] {self.name}"

    # ----------------------------------------------------------------
    # Django Admin 및 인증 시스템 호환을 위한 가상 필드 (Property)
    # DB에는 저장되지 않고, 코드상에서만 role을 확인하여 작동함
    # ----------------------------------------------------------------

    @property
    def is_staff(self):
        """Admin, 지점/테마 관리자만 관리자 페이지 접속 가능"""
        return self.role in ['Admin', 'ThemeManager', 'BranchManager']

    @property
    def is_superuser(self):
        """Admin 역할만 모든 권한(슈퍼유저) 보유"""
        return self.role == 'Admin'

    @property
    def is_active(self):
        """별도 정지 로직이 없다면 항상 True 반환"""
        return True

    # 권한 확인 메서드
    def has_perm(self, perm, obj=None):
        return self.is_superuser

    def has_module_perms(self, app_label):
        return self.is_superuser

# ----------------------------------------------------------------------
# 2. Branch (지점)
# ----------------------------------------------------------------------
class Branch(models.Model):
    branch_id = models.AutoField(primary_key=True)
    branch_name = models.CharField(max_length=100, unique=True, verbose_name="지점명")
    location = models.TextField(verbose_name="위치")
    phone = models.CharField(max_length=20, verbose_name="지점 연락처")
    is_active = models.BooleanField(default=True, verbose_name="활성 상태")

    def __str__(self):
        return self.branch_name

# ----------------------------------------------------------------------
# 3. Theme (테마)
# ----------------------------------------------------------------------
class Theme(models.Model):
    STATUS_CHOICES = (
        ('Ready', '운영 가능'),
        ('Maintenance', '점검 중'),
    )

    theme_id = models.AutoField(primary_key=True)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, verbose_name="지점")
    name = models.CharField(max_length=100, verbose_name="테마명")
    genre = models.CharField(max_length=50, verbose_name="장르")
    difficulty = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)], verbose_name="난이도"
    )
    duration = models.IntegerField(verbose_name="소요 시간 (분)")
    price = models.DecimalField(max_digits=10, decimal_places=0, verbose_name="기본 가격")
    discount_rate = models.DecimalField(
        max_digits=5, decimal_places=2, default=0.00, verbose_name="할인율 (%)"
    )
    description = models.TextField(verbose_name="테마 설명")
    is_active = models.BooleanField(default=True, verbose_name="활성 상태")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Ready', verbose_name="테마 상태")

    def __str__(self):
        return f"[{self.branch.branch_name}] {self.name}"

# ----------------------------------------------------------------------
# 4. Reservation (예약)
# ----------------------------------------------------------------------
class Reservation(models.Model):
    STATUS_CHOICES = (
        ('Confirmed', '예약 확정'),
        ('CheckedIn', '입실 완료'),
        ('Completed', '이용 완료'),
        ('Cancelled', '예약 취소'),
        ('NoShow', '노쇼'),
    )

    reservation_id = models.AutoField(primary_key=True)
    member = models.ForeignKey(Member, on_delete=models.SET_NULL, null=True, verbose_name="예약 회원")
    theme = models.ForeignKey(Theme, on_delete=models.PROTECT, verbose_name="예약 테마") # 테마가 삭제되면 안 됨
    reservation_time = models.DateTimeField(verbose_name="예약 시간")
    num_of_participants = models.IntegerField(verbose_name="참가 인원")
    total_price = models.DecimalField(max_digits=10, decimal_places=0, verbose_name="최종 결제액")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Confirmed', verbose_name="예약 상태")
    hint_count = models.IntegerField(default=0, verbose_name="힌트 사용 횟수")
    is_success = models.BooleanField(null=True, blank=True, verbose_name="탈출 성공 여부")
    clear_time = models.IntegerField(null=True, blank=True, verbose_name="클리어 시간 (초)") # 초 단위로 저장

    def __str__(self):
        return f"{self.reservation_time} - {self.theme.name} ({self.member.name if self.member else '탈퇴회원'})"

# ----------------------------------------------------------------------
# 5. Payment (결제)
# ----------------------------------------------------------------------
class Payment(models.Model):
    payment_id = models.AutoField(primary_key=True)
    reservation = models.OneToOneField(Reservation, on_delete=models.CASCADE, verbose_name="관련 예약")
    payment_method = models.CharField(max_length=50, verbose_name="결제 수단")
    amount = models.DecimalField(max_digits=10, decimal_places=0, verbose_name="결제 금액")
    payment_status = models.CharField(max_length=20, verbose_name="결제 상태") # (예: 'Paid', 'Refunded')
    paid_at = models.DateTimeField(auto_now_add=True, verbose_name="결제 시각")

    def __str__(self):
        return f"{self.reservation.reservation_id} - {self.amount}원"

# ----------------------------------------------------------------------
# 6. Review (리뷰)
# ----------------------------------------------------------------------
class Review(models.Model):
    review_id = models.AutoField(primary_key=True)
    reservation = models.OneToOneField(Reservation, on_delete=models.CASCADE, verbose_name="관련 예약")
    member = models.ForeignKey(Member, on_delete=models.SET_NULL, null=True, verbose_name="작성자")
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)], verbose_name="별점"
    )
    comment = models.TextField(blank=True, verbose_name="리뷰 내용")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="작성일")

    def __str__(self):
        return f"Review {self.review_id} by {self.member.name if self.member else ''}"

# ----------------------------------------------------------------------
# 7. Schedule (직원 스케줄)
# ----------------------------------------------------------------------
class Schedule(models.Model):
    schedule_id = models.AutoField(primary_key=True)
    member = models.ForeignKey(Member, on_delete=models.CASCADE, verbose_name="담당 직원")
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, verbose_name="근무 지점")
    work_date = models.DateField(verbose_name="근무 날짜")
    start_time = models.TimeField(verbose_name="시작 시간")
    end_time = models.TimeField(verbose_name="종료 시간")
    assigned_theme = models.ForeignKey(
        Theme, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="배정 테마"
    )

    def __str__(self):
        return f"{self.work_date} {self.member.name} @ {self.branch.branch_name}"

# ----------------------------------------------------------------------
# 8. Notice (공지사항)
# ----------------------------------------------------------------------
class Notice(models.Model):
    notice_id = models.AutoField(primary_key=True)
    member = models.ForeignKey(Member, on_delete=models.SET_NULL, null=True, verbose_name="작성자 (Admin)")
    title = models.CharField(max_length=255, verbose_name="제목")
    content = models.TextField(verbose_name="내용")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="작성일")
    target_branch = models.ForeignKey(
        Branch, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="대상 지점 (전체 공지 시 NULL)"
    )

    def __str__(self):
        return self.title

# ----------------------------------------------------------------------
# 9. IssueReport (시설 문제 보고)
# ----------------------------------------------------------------------
class IssueReport(models.Model):
    STATUS_CHOICES = (
        ('Reported', '보고됨'),
        ('InProgress', '처리 중'),
        ('Resolved', '해결 완료'),
    )

    report_id = models.AutoField(primary_key=True)
    theme = models.ForeignKey(Theme, on_delete=models.CASCADE, verbose_name="문제 테마")
    reported_by_member = models.ForeignKey(Member, on_delete=models.SET_NULL, null=True, verbose_name="보고자")
    issue_description = models.TextField(verbose_name="문제 설명")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Reported', verbose_name="처리 상태")
    reported_at = models.DateTimeField(auto_now_add=True, verbose_name="보고 시각")

    def __str__(self):
        return f"Issue in {self.theme.name} ({self.get_status_display()})"