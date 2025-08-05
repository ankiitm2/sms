# home_auth/signals.py
from allauth.account.signals import user_signed_up
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.utils import timezone
from student.models import Parent

@receiver(user_signed_up)
def assign_student_role(request, user, sociallogin=None, **kwargs):
    """
    Automatically assign student role to users who sign up via Google OAuth
    """
    if sociallogin and sociallogin.account.provider == 'google':
        user.is_student = True
        user.save()
        
        # Create a student profile if your model requires it
        Student = get_user_model()
        if hasattr(user, 'student_profile'):
            # Update existing profile if needed
            pass
        else:
            # Create minimal student profile
            Student.objects.create(
                user=user,
                first_name=user.first_name,
                last_name=user.last_name,
                student_class='Class 1',  # Default class
                section='A',              # Default section
                date_of_birth='2000-01-01',  # Default DOB
                gender='Male',            # Default gender
                joining_date=timezone.now().date(),
                parent=Parent.objects.create()  # Minimal parent record
            )