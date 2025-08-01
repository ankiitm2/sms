# school/forms
from django import forms
from .models import Exam, Timetable
from django.core.exceptions import ValidationError
from .models import CustomUser
from django.contrib.auth import get_user_model
from .models import Department
from .models import Message, MessageAttachment

User = get_user_model()

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
        fields = ['name', 'subject', 'date', 'start_time', 'end_time', 
                 'student_class', 'section', 'room', 'max_marks', 'description']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = single_file_clean(data, initial)
        return result

class MessageForm(forms.ModelForm):
    attachments = MultipleFileField(required=False)
    recipients = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        widget=forms.SelectMultiple(attrs={'class': 'select2'}),
        required=True
    )

    class Meta:
        model = Message
        fields = ['subject', 'body', 'recipients', 'parent']
        widgets = {
            'subject': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Subject'
            }),
            'body': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 8,
                'placeholder': 'Type your message here...'
            }),
            'parent': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        # Remove 'user' from kwargs if it exists
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # If we have a user, we can customize the form
        if self.user:
            # Example: Exclude current user from recipients
            self.fields['recipients'].queryset = User.objects.exclude(id=self.user.id)


class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ['name', 'code', 'description', 'head']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'head': forms.Select(attrs={'class': 'form-control select2'}),
        }

    def __int__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['head'].queryset = CustomUser.objects.filter(is_teacher=True)