# models.py
from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
import uuid
from home_auth.admin import CustomUser

class Notification(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    message = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.message


class StudentTeacherRelationship(models.Model):
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='teachers')
    teacher = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='students')
    subject = models.CharField(max_length=100)
    
    class Meta:
        unique_together = ('student', 'teacher', 'subject')
        
    def __str__(self):
        return f"{self.student} - {self.teacher} ({self.subject})"
    

class Timetable(models.Model):
    DAY_CHOICES = [
        ('Monday', 'Monday'),
        ('Tuesday', 'Tuesday'),
        ('Wednesday', 'Wednesday'),
        ('Thursday', 'Thursday'),
        ('Friday', 'Friday'),
        ('Saturday', 'Saturday'),
        ('Sunday', 'Sunday'),
    ]
    
    COLOR_CHOICES = [
        ('#FF5733', 'Red'),
        ('#33FF57', 'Green'),
        ('#3357FF', 'Blue'),
        ('#F333FF', 'Purple'),
        ('#FF33F3', 'Pink'),
        ('#33FFF5', 'Teal'),
    ]
    
    color = models.CharField(max_length=7, choices=COLOR_CHOICES, default='#3357FF')
    day = models.CharField(max_length=10, choices=DAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    subject = models.CharField(max_length=100)
    teacher = models.ForeignKey(
        CustomUser, 
        on_delete=models.CASCADE, 
        limit_choices_to={'is_teacher': True}
    )
    student_class = models.CharField(max_length=50)
    section = models.CharField(max_length=10)
    classroom = models.CharField(max_length=50)
    
    class Meta:
        unique_together = ('day', 'start_time', 'student_class', 'section')
        ordering = ['day', 'start_time']
    
    def __str__(self):
        return f"{self.day} {self.start_time}-{self.end_time}: {self.subject}"
    

class Exam(models.Model):
    name = models.CharField(max_length=100)
    subject = models.CharField(max_length=100)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    student_class = models.CharField(max_length=50)
    section = models.CharField(max_length=10, blank=True, null=True)
    teacher = models.ForeignKey(
        CustomUser, 
        on_delete=models.CASCADE,
        limit_choices_to={'is_teacher': True}
    )
    room = models.CharField(max_length=50)
    max_marks = models.PositiveIntegerField(default=100)
    
    class Meta:
        ordering = ['date', 'start_time']
        constraints = [
            models.UniqueConstraint(
                fields=['date', 'teacher'],
                name='max_two_exams_per_teacher_per_day'
            )
        ]
    
    def __str__(self):
        return f"{self.name} - {self.subject} ({self.date})"