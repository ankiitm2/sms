# school/models.py
from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
import uuid
from home_auth.admin import CustomUser
from django.urls import reverse
from django.utils import timezone

class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('exam', 'Exam Notification'),
        ('assignment', 'Assignment Notification'),
        ('general', 'General Notification'),
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=100, blank=True)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, default='general')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    related_url = models.URLField(blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
    
    def __str__(self):
        return f"{self.get_notification_type_display()} for {self.user.email}"
    
    def save(self, *args, **kwargs):
        if not self.title:
            self.title = self.get_notification_type_display()
        super().save(*args, **kwargs)
    
    @property
    def time_since(self):
        now = timezone.now()
        diff = now - self.created_at
        
        if diff.days > 365:
            years = diff.days // 365
            return f"{years} year{'s' if years > 1 else ''} ago"
        if diff.days > 30:
            months = diff.days // 30
            return f"{months} month{'s' if months > 1 else ''} ago"
        if diff.days > 0:
            return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
        if diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
        if diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
        return "Just now"

class StudentTeacherRelationship(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='teachers')
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='students')
    subject = models.CharField(max_length=100)
    
    class Meta:
        unique_together = ('student', 'teacher', 'subject')
        
    def __str__(self):
        return f"{self.student} - {self.teacher} ({self.subject})"
    

class Exam(models.Model):
    name = models.CharField(max_length=100)
    subject = models.CharField(max_length=100)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    student_class = models.CharField(max_length=50)
    section = models.CharField(max_length=10, default='A')
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'is_teacher': True},
        related_name='exams_created'
    )
    room = models.CharField(max_length=50)
    max_marks = models.PositiveIntegerField(default=100)
    description = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['date', 'start_time']
    
    def __str__(self):
        return f"{self.name} - {self.subject} ({self.date}) for {self.student_class} {self.section}"
    

class Message(models.Model):
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='sent_messages',
        on_delete=models.CASCADE
    )
    recipients = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='received_messages'
    )
    subject = models.CharField(max_length=200)
    body = models.TextField()
    sent_at = models.DateTimeField(default=timezone.now)
    is_read = models.BooleanField(default=False)
    parent = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='replies'
    )

    class Meta:
        ordering = ['-sent_at']
        permissions = [
            ("broadcast_message", "Can send messages to multiple recipients"),
        ]

    def __str__(self):
        return f"{self.subject} (From: {self.sender}, To: {', '.join([r.get_full_name() for r in self.recipients.all()])})"
    
    def get_absolute_url(self):
        return reverse('message_detail', args=[str(self.id)])

class MessageAttachment(models.Model):
    message = models.ForeignKey(
        Message,
        related_name='attachments',
        on_delete=models.CASCADE
    )
    file = models.FileField(upload_to='message_attachments/%Y/%m/%d/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def filename(self):
        return self.file.name.split('/')[-1]
    

class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=10, unique=True)
    description = models.TextField(blank=True, null=True)
    head = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'is_teacher': True},
        related_name='headed_departments'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.code})"
    

class Holiday(models.Model):
    name = models.CharField(max_length=100)
    date = models.DateField()
    recurring = models.BooleanField(default=False)
    description  = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['date']
        verbose_name_plural = 'Holidays'

    def __str__(self):
        return f"{self.name} ({self.date})"
    

class Subject(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True, null=True)
    student_class = models.CharField(max_length=50, blank=True, null=True)
    section = models.CharField(max_length=10, blank=True, null=True)
    department = models.ForeignKey(
        'Department',
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='subjects'
    )
    timetable = models.ForeignKey(
        'Timetable',
        on_delete=models.CASCADE,
        related_name='subjects',
        null=True,
        blank=True
    )
    teachers = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        limit_choices_to={'is_teacher': True},
        related_name='subjects_taught',
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        
    def __str__(self):
        return f"{self.name} ({self.code})"
    

class Timetable(models.Model):
    CLASS_DAYS = [
        ('Monday', 'Monday'),
        ('Tuesday', 'Tuesday'),
        ('Wednesday', 'Wednesday'),
        ('Thursday', 'Thursday'),
        ('Friday', 'Friday'),
        ('Saturday', 'Saturday'),
    ]

    student_class = models.CharField(max_length=50)
    section = models.CharField(max_length=10)
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name='timetable_entries'
    )
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='timetable_teacher'
    )
    day = models.CharField(max_length=10, choices=CLASS_DAYS)
    start_time = models.TimeField()
    end_time = models.TimeField()
    classroom = models.CharField(max_length=50, blank=True, null=True)
    color = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return f"{self.subject} - {self.student_class} {self.section} ({self.day})"