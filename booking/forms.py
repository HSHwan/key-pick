# booking/forms.py
from django import forms
from .models import Review, Reservation

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
        # 사용자로부터 예약 시간과 참가 인원만 입력받음
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