# booking/forms.py
from django import forms
from .models import Review

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