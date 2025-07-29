from django import forms
from .models import Exam, Timetable
from django.core.exceptions import ValidationError
from .models import CustomUser

CLASS_CHOICES = [
    ('Class 1', 'Class 1'),
    ('Class 2', 'Class 2'),
    ('Class 3', 'Class 3'),
    ('Class 4', 'Class 4'),
    ('Class 5', 'Class 5'),
    ('Class 6', 'Class 6'),
    ('Class 7', 'Class 7'),
    ('Class 8', 'Class 8'),
    ('Class 9', 'Class 9'),
    ('Class 10', 'Class 10'),
    ('Class 11', 'Class 11'),
    ('Class 12', 'Class 12'),
]

SECTION_CHOICES = [
    ('A', 'A'),
    ('B', 'B'),
    ('C', 'C'),
    ('D', 'D'),
]

class TimetableForm(forms.ModelForm):
    student_class = forms.ChoiceField(choices=CLASS_CHOICES, widget=forms.Select(attrs={'class': 'form-control'}))
    section = forms.ChoiceField(choices=SECTION_CHOICES, widget=forms.Select(attrs={'class': 'form-control'}))
    
    class Meta:
        model = Timetable
        fields = '__all__'
        widgets = {
            'day': forms.Select(attrs={'class': 'form-control'}),
            'start_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'end_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'subject': forms.TextInput(attrs={'class': 'form-control'}),
            'teacher': forms.Select(attrs={'class': 'form-control'}),
            'classroom': forms.TextInput(attrs={'class': 'form-control'}),
            'color': forms.HiddenInput(),  # We'll handle this separately
        }

    def __init__(self, *args, **kwargs):
        request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        
        # Set up teacher queryset
        self.fields['teacher'].queryset = CustomUser.objects.filter(is_teacher=True)
        
        if request and request.user.is_teacher:
            self.fields['teacher'].initial = request.user
            self.fields['teacher'].disabled = True

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