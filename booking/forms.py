# booking/forms.py
from django import forms
from .models import *

# 리뷰 폼
class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.NumberInput(attrs={'min': 1, 'max': 5, 'class': 'form-control'}),
            'comment': forms.Textarea(attrs={'rows': 5, 'class': 'form-control', 'placeholder': '테마 이용 후기를 남겨주세요.'}),
        }
        labels = {
            'rating': '별점 (1~5점)',
            'comment': '리뷰 내용',
        }

# 예약 폼
class ReservationForm(forms.ModelForm):
    class Meta:
        model = Reservation
        fields = ['reservation_time', 'num_of_participants']
        widgets = {
            'reservation_time': forms.DateTimeInput(
                attrs={'type': 'datetime-local', 'class': 'form-control'}
            ),
            'num_of_participants': forms.NumberInput(
                attrs={'min': 1, 'class': 'form-control', 'placeholder': '인원 수'}
            ),
        }
        labels = {
            'reservation_time': '예약 날짜 및 시간',
            'num_of_participants': '참가 인원',
        }

# 시설 문제 보고 폼
class IssueReportForm(forms.ModelForm):
    class Meta:
        model = IssueReport
        fields = ['theme', 'issue_description']
        widgets = {
            'issue_description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': '문제 상황을 자세히 적어주세요.'}),
            'theme': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'theme': '문제 발생 테마',
            'issue_description': '내용',
        }

# 스케줄 등록 폼
class ScheduleForm(forms.ModelForm):
    class Meta:
        model = Schedule
        fields = ['member', 'branch', 'work_date', 'start_time', 'end_time', 'assigned_theme']
        widgets = {
            'work_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'start_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'end_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'member': forms.Select(attrs={'class': 'form-select'}),
            'branch': forms.Select(attrs={'class': 'form-select'}),
            'assigned_theme': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'member': '담당 직원',
            'branch': '근무 지점',
            'assigned_theme': '배정 테마 (선택)',
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(ScheduleForm, self).__init__(*args, **kwargs)

        if user:
            if user.role == 'BranchManager':
                my_branch_ids = BranchAssignment.objects.filter(member=user).values_list('branch_id', flat=True)
                
                self.fields['branch'].queryset = Branch.objects.filter(
                    branch_id__in=my_branch_ids, 
                    is_active=True
                )
                
                my_staff_ids = BranchAssignment.objects.filter(
                    branch_id__in=my_branch_ids,
                    member__role='ThemeManager'
                ).values_list('member_id', flat=True)
                
                self.fields['member'].queryset = Member.objects.filter(
                    member_id__in=my_staff_ids
                )

                self.fields['assigned_theme'].queryset = Theme.objects.filter(
                    branch_id__in=my_branch_ids, 
                    is_active=True
                )

            elif user.role == 'Admin':
                pass

# 지점 관리자용 테마 수정 폼
class BranchThemeUpdateForm(forms.ModelForm):
    class Meta:
        model = Theme
        fields = ['price', 'discount_rate', 'status', 'is_active']
        widgets = {
            'price': forms.NumberInput(attrs={'class': 'form-control'}),
            'discount_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'price': '기본 가격',
            'discount_rate': '할인율 (%)',
            'status': '운영 상태',
            'is_active': '활성화 여부'
        }
# 공지사항 작성
class NoticeForm(forms.ModelForm):
    class Meta:
        model = Notice
        fields = ['title', 'content', 'target_branch']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '제목을 입력하세요'}),
            'content': forms.Textarea(attrs={'rows': 10, 'class': 'form-control', 'placeholder': '내용을 입력하세요'}),
            'target_branch': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'title': '제목',
            'content': '내용',
            'target_branch': '대상 지점 (선택 안 함: 전체 공지)',
        }