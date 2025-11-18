# booking/forms.py
from django import forms
from .models import Review, Reservation, IssueReport, Schedule, Branch

# 1. 리뷰 폼
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

# 2. 예약 폼
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

# 3. 시설 문제 보고 폼 (이 부분이 누락되어 에러 발생)
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

# 4. 스케줄 등록 폼
class ScheduleForm(forms.ModelForm):
    class Meta:
        model = Schedule
        fields = ['member', 'branch', 'work_date', 'start_time', 'end_time', 'assigned_theme']
        widgets = {
            'work_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'start_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'end_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'member': forms.Select(attrs={'class': 'form-control'}),
            'branch': forms.Select(attrs={'class': 'form-control'}),
            'assigned_theme': forms.Select(attrs={'class': 'form-control'}),
        }