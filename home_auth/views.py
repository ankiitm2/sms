from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from .models import CustomUser, PasswordResetRequest
from django.contrib import messages
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.utils.crypto import get_random_string
from school.models import Notification
from .models import Timetable
from django.contrib.auth import get_user_model
from django.views import View
from django.utils import timezone
from student.models import Student, Parent


@login_required
def edit_profile(request):
    if request.method == 'POST':
        try:
            # Update user fields
            request.user.first_name = request.POST.get('first_name')
            request.user.last_name = request.POST.get('last_name')
            request.user.email = request.POST.get('email')
            
            if 'profile_picture' in request.FILES:
                if request.user.profile_picture:
                    request.user.profile_picture.delete()
                request.user.profile_picture = request.FILES['profile_picture']
            
            request.user.save()

            if request.user.is_student:
                # Get or create student profile with all required fields
                student, created = Student.objects.get_or_create(
                    user=request.user,
                    defaults={
                        'first_name': request.user.first_name,
                        'last_name': request.user.last_name,
                        'student_class': request.POST.get('student_class', 'Class 1'),
                        'section': request.POST.get('section', 'A'),
                        'date_of_birth': '2000-01-01',  # Default value
                        'gender': 'Male',               # Default value
                        'joining_date': timezone.now().date(),
                        'mobile_number': request.POST.get('mobile_number', ''),
                        'admission_number': '',
                        'parent': Parent.objects.create()  # Create minimal parent
                    }
                )
                
                # Update student fields
                if not created:
                    student.mobile_number = request.POST.get('mobile_number', '')
                    student.student_class = request.POST.get('student_class', 'Class 1')
                    student.section = request.POST.get('section', 'A')
                    student.save()

            messages.success(request, 'Profile updated successfully!')
            return redirect('edit_profile')
            
        except Exception as e:
            messages.error(request, f'Error updating profile: {str(e)}')
    
    # Prepare context with class and section options
    CLASS_CHOICES = [
        'Class 1', 'Class 2', 'Class 3', 'Class 4', 'Class 5',
        'Class 6', 'Class 7', 'Class 8', 'Class 9', 'Class 10',
        'Class 11', 'Class 12'
    ]
    SECTION_CHOICES = ['A', 'B', 'C', 'D']
    
    context = {
        'user': request.user,
        'class_options': CLASS_CHOICES,
        'section_options': SECTION_CHOICES,
        'unread_notification_count': Notification.objects.filter(
            user=request.user, 
            is_read=False
        ).count()
    }
    
    if request.user.is_student:
        try:
            context['student'] = Student.objects.get(user=request.user)
        except Student.DoesNotExist:
            pass
    
    return render(request, 'profile/edit.html', context)

def signup_view(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        role = request.POST.get('role', 'student')  
        profile_picture = request.FILES.get('profile_picture')
        
        # Basic validation
        if not all([first_name, last_name, email, password, confirm_password]):
            messages.error(request, 'Please fill in all required fields')
            return redirect('signup')
            
        if password != confirm_password:
            messages.error(request, 'Passwords do not match')
            return redirect('signup')
            
        # Check if email already exists
        if CustomUser.objects.filter(email=email).exists():
            messages.error(request, 'Email address is already in use')
            return redirect('signup')
            
        try:
            # Create the user
            user = CustomUser.objects.create_user(
                username=email,
                email=email,
                first_name=first_name,
                last_name=last_name,
                password=password,
            )
            
            if profile_picture:
                user.profile_picture = profile_picture

            if role == 'student':
                user.is_student = True
                # Create complete student profile
                Student.objects.create(
                    user=user,
                    first_name=first_name,
                    last_name=last_name,
                    student_class=request.POST.get('student_class', 'Class 1'),
                    section=request.POST.get('section', 'A'),
                    date_of_birth='2000-01-01',  # Default value
                    joining_date=timezone.now().date(),
                    gender='Male',
                    mobile_number='',
                    admission_number='',
                    parent=Parent.objects.create()  # Minimal parent record
                )
            
            user.save()
            login(request, user)
            messages.success(request, 'Signup successful!')
            return redirect('dashboard')
            
        except Exception as e:
            messages.error(request, f'Error during signup: {str(e)}')
            return redirect('signup')
            
    return render(request, 'authentication/register.html')


def login_view(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        
        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            
            # Redirect to appropriate dashboard
            if user.is_teacher:
                return redirect('teacher_dashboard')
            elif user.is_student:
                return redirect('student_dashboard')
            elif user.is_admin:
                return redirect('admin_dashboard')
            
        else:
            messages.error(request, 'Invalid credentials')
    
    return render(request, 'authentication/login.html')


def forgot_password_view(request):
    if request.method == 'POST':
        email = request.POST['email']
        user = CustomUser.objects.filter(email=email).first()
        
        if user:
            token = get_random_string(32)
            reset_request = PasswordResetRequest.objects.create(user=user, email=email, token=token)
            reset_request.send_reset_email(request)
            messages.success(request, 'Reset link sent to your email.')
        else:
            messages.error(request, 'Email not found.')
    
    return render(request, 'authentication/forgot-password.html')  # Render forgot password template


def reset_password_view(request, token):
    reset_request = PasswordResetRequest.objects.filter(token=token).first()
    
    if not reset_request or not reset_request.is_valid():
        messages.error(request, 'Invalid or expired reset link')
        return redirect('index')

    if request.method == 'POST':
        new_password = request.POST['new_password']
        reset_request.user.set_password(new_password)
        reset_request.user.save()
        messages.success(request, 'Password reset successful')
        return redirect('login')

    return render(request, 'authentication/reset_password.html', {'token': token})  # Render reset password template


def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('index')

User = get_user_model()

class TimetableView(View):
    def get(self, request):
        user = request.user

        if user.is_teacher:
            # Show teacher's own timetable
            timetable_entries = Timetable.objects.filter(teacher=user)
        elif user.is_student:
            # Show timetable for student's class and section
            try:
                student = Student.objects.get(user=user)
                timetable_entries = Timetable.objects.filter(
                    student_class=student.student_class,
                    section=student.section
                ).order_by('day', 'start_time')
            except Student.DoesNotExist:
                timetable_entries = Timetable.objects.none()
        else:
            timetable_entries = Timetable.objects.none()

        return render(request, 'time-table.html', {
            'timetable_entries': timetable_entries
        })