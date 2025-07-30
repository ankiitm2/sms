from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
import uuid
from django.templatetags.static import static as static_func
from django.utils.crypto import get_random_string
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import User



# Create your models here.
class CustomUser(AbstractUser):
    email = models.EmailField(max_length=100, unique=True)
    is_authorized = models.BooleanField(default=False)
    is_student = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    is_teacher = models.BooleanField(default=False)
    student_class = models.CharField(max_length=50, null=True, blank=True)
    section = models.CharField(max_length=10, null=True, blank=True)

    phone = models.CharField(max_length=20, null=True, blank=True)
    department = models.CharField(max_length=100, null=True, blank=True)
    qualification = models.CharField(max_length=100, null=True, blank=True)
    specialization = models.CharField(max_length=100, null=True, blank=True)
    bio = models.TextField(null=True, blank=True)
    joining_date = models.DateField(null=True, blank=True)

    profile_picture = models.ImageField(
        upload_to='profile_pictures/',
        null=True,
        blank=True,
        default=None
    )

    @property
    def unread_notification_count(self):
        return self.notifications.filter(is_read=False).count()

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def get_profile_picture_url(self):
        if self.profile_picture and hasattr(self.profile_picture, 'url'):
            return self.profile_picture.url
        return static_func('img/profiles/avatar-02.jpg')
    
class PasswordResetRequest(models.Model):
    user = models.ForeignKey('CustomUser', on_delete=models.CASCADE)
    email = models.EmailField()
    token = models.CharField(max_length=32, default=get_random_string(32), editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    TOKEN_VALIDITY_PERIOD = timezone.timedelta(hours=1)

    def is_valid(self):
        return timezone.now() <= self.created_at + self.TOKEN_VALIDITY_PERIOD
    
    def send_reset_email(self, request):
        reset_link = request.build_absolute_uri(f"/authentication/reset-password/{self.token}/")
        send_mail(
        'Password Reset Request',
        f'Click the following link to reset your password: {reset_link}',
        settings.DEFAULT_FROM_EMAIL,
        [self.email],
        fail_silently=False
    )

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
    subject = models.CharField(max_length=100)
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='timetable_teacher')
    day = models.CharField(max_length=10, choices=CLASS_DAYS)
    start_time = models.TimeField()
    end_time = models.TimeField()

    def __str__(self):
        return f"{self.subject} - {self.student_class} {self.section} ({self.day})"
