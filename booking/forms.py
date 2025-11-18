# booking/forms.py
from django import forms
from .models import Review, Reservation, IssueReport, Schedule, Branch

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        # 사용자에게 입력받을 필드만 지정
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.NumberInput(attrs={'min': 1, 'max': 5, 'class': 'form-control'}),
            'comment': forms.Textarea(attrs={'rows': 5, 'class': 'form-control', 'placeholder': '테마 이용 후기를 남겨주세요.'}),
        }
        labels = {
            'rating': '별점 (1~5점)',
            'comment': '리뷰 내용',
        }

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