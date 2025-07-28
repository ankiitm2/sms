from django import forms
from .models import Exam, Timetable
from django.core.exceptions import ValidationError
import datetime

class TimetableForm(forms.ModelForm):
    class Meta:
        model = Timetable
        fields = '__all__'
        widgets = {
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
        }

class ExamForm(forms.ModelForm):
    class Meta:
        model = Exam
        fields = '__all__'
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        
        # Remove teacher field if user is not admin
        if self.request and not self.request.user.is_admin:
            self.fields.pop('teacher', None)

    def clean(self):
        cleaned_data = super().clean()
        date = cleaned_data.get('date')
        teacher = cleaned_data.get('teacher', self.request.user if self.request else None)
        
        if date and teacher:
            existing_exams = Exam.objects.filter(
                date=date,
                teacher=teacher
            ).count()
            
            if existing_exams >= 2:
                raise ValidationError(
                    "A teacher cannot have more than 2 exams in a day."
                )
        
        return cleaned_data