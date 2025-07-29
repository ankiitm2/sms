# school/views.py
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from .models import Notification
from django.contrib.auth.decorators import login_required
from home_auth.models import CustomUser
from django.contrib.auth.hashers import make_password
from django.contrib import messages
from .models import StudentTeacherRelationship, Timetable, Exam
from django.views.generic import ListView
from student.models import Student
from django.views.generic import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from .forms import TimetableForm, ExamForm
from datetime import time
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
import datetime
from django.utils import timezone

def index(request):
    # Redirect to login page or dashboard based on authentication
    if request.user.is_authenticated:
        return redirect('dashboard')
    return redirect('login') 

@login_required
def dashboard(request):
    if request.user.is_admin:
        return redirect('admin_dashboard')
    elif request.user.is_teacher:
        return redirect('teacher_dashboard')
    elif request.user.is_student:
        # Prepare context with user's name
        unread_notification = Notification.objects.filter(user=request.user, is_read=False).order_by('-created_at')
        unread_notification_count = unread_notification.count()
        context = {
            'unread_notification': unread_notification,
            'unread_notification_count': unread_notification_count,
            'user': request.user  # Pass the user object to template
        }
        return render(request, "students/student-dashboard.html", context)
    else:
        return redirect('login')
    
@login_required
def student_dashboard(request):
    if not request.user.is_student:
        return HttpResponseForbidden()
    
    try:
        student = Student.objects.get(user=request.user)
        
        # Get exams for student's class and section
        upcoming_exams = Exam.objects.filter(
            student_class=student.student_class,
            section=student.section,
            date__gte=datetime.date.today()
        ).order_by('date', 'start_time')
        
        context = {
            'user': request.user,
            'student': student,
            'upcoming_exams': upcoming_exams,
            'unread_notification_count': Notification.objects.filter(
                user=request.user, 
                is_read=False
            ).count()
        }
        return render(request, "students/student-dashboard.html", context)
        
    except Student.DoesNotExist:
        messages.error(request, "Student profile not found. Please complete your profile.")
        return redirect('edit_profile')

@login_required
def student_teachers(request):
    if not request.user.is_student:
        return HttpResponseForbidden()
    
    # Debug print
    relationships = StudentTeacherRelationship.objects.filter(student=request.user).select_related('teacher')
    print(f"Found {relationships.count()} relationships")
    for rel in relationships:
        print(f"Teacher: {rel.teacher.email}, Subject: {rel.subject}")
    
    context = {
        'teachers': relationships,
        'unread_notification_count': Notification.objects.filter(
            user=request.user, 
            is_read=False
        ).count(),
        'user': request.user
    }
    return render(request, "students/student-teachers.html", context)

@login_required
def teacher_dashboard(request):
    if not request.user.is_teacher:
        return HttpResponseForbidden()

    # Fetch unread notifications
    unread_notifications = Notification.objects.filter(
        user=request.user,
        is_read=False
    ).order_by('-created_at')

    # Count distinct classes and students
    classes_teaching = Timetable.objects.filter(
        teacher=request.user
    ).values('student_class', 'section').distinct().count()

    students_taught = StudentTeacherRelationship.objects.filter(
        teacher=request.user
    ).values('student').distinct().count()

    upcoming_classes = Timetable.objects.filter(
        teacher=request.user
    ).order_by('day', 'start_time')[:5] 

    context = {
        'user': request.user,
        'unread_notifications': unread_notifications,
        'unread_notification_count': unread_notifications.count(),
        'classes_teaching': classes_teaching,
        'students_taught': students_taught,
        'tests_to_grade': [],
        'upcoming_classes': upcoming_classes,
    }
    return render(request, "teachers/teacher_dashboard.html", context)


@login_required
def teacher_list(request):
    if not (request.user.is_admin or request.user.is_teacher or request.user.is_student):
        return HttpResponseForbidden()
    
    teachers = CustomUser.objects.filter(is_teacher=True).only(
    'first_name', 'last_name', 'email', 'date_joined', 'profile_picture'
        )
    unread_notifications = Notification.objects.filter(user=request.user, is_read=False)
    
    context = {
        'teachers': teachers,
        'user': request.user,
        'unread_notification_count': unread_notifications.count(),
        'unread_notification': unread_notifications
    }
    return render(request, "teachers/teacher_list.html", context)

@login_required
def add_teacher(request):
    if not request.user.is_admin:
        return HttpResponseForbidden()
    
    if request.method == 'POST':
        try:
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            email = request.POST.get('email')
            password = request.POST.get('password')
            profile_picture = request.FILES.get('profile_picture')

            # Validate required fields
            if not all([first_name, last_name, email, password]):
                messages.error(request, 'Please fill in all required fields')
                return redirect('add_teacher')

            if CustomUser.objects.filter(email=email).exists():
                messages.error(request, 'Email already exists')
                return redirect('add_teacher')

            # Create teacher
            teacher = CustomUser.objects.create(
                username=email,
                email=email,
                first_name=first_name,
                last_name=last_name,
                password=make_password(password),
                is_teacher=True
            )

            if profile_picture:
                teacher.profile_picture = profile_picture
                teacher.save()

            messages.success(request, 'Teacher added successfully')
            return redirect('teacher_list')

        except Exception as e:
            messages.error(request, f'Error adding teacher: {str(e)}')
            return redirect('add_teacher')

    return render(request, "teachers/add_teacher.html")

@login_required
def edit_teacher(request, pk):
    if not request.user.is_admin:
        return HttpResponseForbidden()
    
    teacher = get_object_or_404(CustomUser, pk=pk, is_teacher=True)
    
    if request.method == 'POST':
        # Handle teacher edit form
        pass
    
    return render(request, "teachers/edit_teacher.html", {'teacher': teacher})

@login_required
def teacher_schedule(request):
    if not request.user.is_teacher:
        return HttpResponseForbidden()
    
    # Get timetable entries for this teacher
    timetable_entries = Timetable.objects.filter(
        teacher=request.user
    ).order_by('day', 'start_time')
    
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    
    context = {
        'timetable_entries': timetable_entries,
        'days': days,
        'user': request.user,
        'unread_notification_count': Notification.objects.filter(
            user=request.user, 
            is_read=False
        ).count()
    }
    return render(request, "teachers/teacher_schedule.html", context)

@login_required
def create_assignment(request):
    if not request.user.is_teacher:
        return HttpResponseForbidden()
    return render(request, "teachers/create_assignment.html")

@login_required
def grade_submissions(request):
    if not request.user.is_teacher:
        return HttpResponseForbidden()
    return render(request, "teachers/grade_submissions.html")

@login_required
def take_attendance(request):
    if not request.user.is_teacher:
        return HttpResponseForbidden()
    return render(request, "teachers/attendance.html")


@login_required
def teacher_profile_view(request):
    if not request.user.is_teacher:
        return HttpResponseForbidden()
    
    context = {
        'user': request.user,
        'teacher': request.user,
        'unread_notification_count': Notification.objects.filter(
            user=request.user, 
            is_read=False
        ).count()
    }
    return render(request, "teachers/teacher_profile_view.html", context)


@login_required
def teacher_profile(request):
    if not request.user.is_teacher:
        return HttpResponseForbidden()
    
    # Calculate years of service
    years_of_service = 0
    if request.user.joining_date:
        today = timezone.now().date()
        years_of_service = today.year - request.user.joining_date.year
        if today.month < request.user.joining_date.month or \
           (today.month == request.user.joining_date.month and today.day < request.user.joining_date.day):
            years_of_service -= 1
    
    # Get teacher's subjects and classes (example implementation)
    subjects = ['Math', 'Science']  # Replace with actual data from your models
    classes = ['Class 10A', 'Class 11B']  # Replace with actual data
    total_students = 45  # Replace with actual count
    
    context = {
        'user': request.user,
        'teacher': request.user,
        'years_of_service': years_of_service,
        'subjects': subjects,
        'classes': classes,
        'total_students': total_students,
        'unread_notification_count': Notification.objects.filter(
            user=request.user, 
            is_read=False
        ).count()
    }
    return render(request, "teachers/teacher_profile.html", context)

@login_required
def teacher_profile_edit(request):
    if not request.user.is_teacher:
        return HttpResponseForbidden()
    
    if request.method == 'POST':
        try:
            # Update basic fields
            request.user.first_name = request.POST.get('first_name')
            request.user.last_name = request.POST.get('last_name')
            request.user.email = request.POST.get('email')
            request.user.phone = request.POST.get('phone')
            request.user.department = request.POST.get('department')
            request.user.qualification = request.POST.get('qualification')
            request.user.specialization = request.POST.get('specialization')
            request.user.bio = request.POST.get('bio')
            
            # Handle dates
            joining_date = request.POST.get('joining_date')
            if joining_date:
                request.user.joining_date = joining_date
            
            # Handle profile picture
            if 'profile_picture' in request.FILES:
                if request.user.profile_picture:
                    request.user.profile_picture.delete()
                request.user.profile_picture = request.FILES['profile_picture']
            
            request.user.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('teacher_profile')
            
        except Exception as e:
            messages.error(request, f'Error updating profile: {str(e)}')
    
    context = {
        'user': request.user,
        'unread_notification_count': Notification.objects.filter(
            user=request.user, 
            is_read=False
        ).count()
    }
    return render(request, "teachers/teacher_profile_edit.html", context)


class ExamCreateView(LoginRequiredMixin, CreateView):
    model = Exam
    form_class = ExamForm
    template_name = 'exam_form.html'
    success_url = reverse_lazy('exam_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs
    
    def form_valid(self, form):
        try:
            if not self.request.user.is_admin:
                form.instance.teacher = self.request.user
            response = super().form_valid(form)
            messages.success(self.request, 'Exam created successfully!')
            return response
        except Exception as e:
            messages.error(self.request, f'Error creating exam: {str(e)}')
            return self.form_invalid(form)

class ExamUpdateView(LoginRequiredMixin, UpdateView):
    model = Exam
    form_class = ExamForm
    template_name = 'exam_form.html'
    success_url = reverse_lazy('exam_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs
    
    def form_valid(self, form):
        if not self.request.user.is_admin:
            form.instance.teacher = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, 'Exam updated successfully!')
        return response

class ExamListView(LoginRequiredMixin, ListView):
    model = Exam
    template_name = 'exam_list.html'
    context_object_name = 'exams'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        
        if user.is_teacher:
            return queryset.filter(teacher=user)
        elif user.is_student:
            try:
                student = Student.objects.get(user=user)
                return queryset.filter(
                    student_class=student.student_class,
                    section=student.section,
                    date__gte=timezone.now().date()  # Only show upcoming exams
                ).order_by('date', 'start_time')
            except Student.DoesNotExist:
                return queryset.none()
        elif user.is_admin:
            return queryset.order_by('date', 'start_time')
        
        return queryset.none()


@login_required
def admin_dashboard(request):
    if not request.user.is_admin:
        return HttpResponseForbidden()
    
    unread_notification = Notification.objects.filter(
        user=request.user, 
        is_read=False
    ).order_by('-created_at')
    
    context = {
        'unread_notification': unread_notification,
        'unread_notification_count': unread_notification.count(),
        'user': request.user
    }
    return render(request, "admin/admin-dashboard.html", context)

@login_required
def mark_notification_as_read(request):
    if request.method == 'POST':
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return JsonResponse({'status': 'success'})
    return HttpResponseForbidden()

@login_required
def clear_all_notification(request):
    if request.method == "POST":
        Notification.objects.filter(user=request.user).delete()
        return JsonResponse({'status': 'success', 'count': 0})
    return HttpResponseForbidden()


class TimetableView(LoginRequiredMixin, ListView):
    model = Timetable
    template_name = 'time-table.html'
    context_object_name = 'timetable_entries'

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.is_student:
            try:
                student = Student.objects.get(user=self.request.user)
                return queryset.filter(
                    student_class=student.student_class,
                    section=student.section
                ).order_by('day', 'start_time')
            except Student.DoesNotExist:
                return queryset.none()
        elif self.request.user.is_teacher:
            return queryset.filter(teacher=self.request.user).order_by('day', 'start_time')
        elif self.request.user.is_admin:
            return queryset.order_by('day', 'start_time')
        return queryset.none()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['days'] = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        context['user'] = self.request.user
        context['unread_notification_count'] = Notification.objects.filter(
            user=self.request.user, 
            is_read=False
        ).count()
        return context
    
class TimetableCreateView(LoginRequiredMixin, CreateView):
    model = Timetable
    form_class = TimetableForm
    template_name = 'timetable_form.html'
    success_url = reverse_lazy('time_table')

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.teacher = self.request.user
        obj.student_class = form.cleaned_data['student_class']
        obj.section = form.cleaned_data['section']
        obj.save()
        messages.success(self.request, 'Timetable entry added successfully!')
        return super().form_valid(form)


class TimetableCalendarView(LoginRequiredMixin, View):
    def get(self, request):
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        time_slots = [time(h, 0).strftime('%H:%M') for h in range(8, 18)]  # 8AM to 6PM
        
        if request.user.is_student:
            try:
                student = Student.objects.get(user=request.user)
                timetable = Timetable.objects.filter(
                    student_class=student.student_class,
                    section=student.section
                ).order_by('day', 'start_time')
            except Student.DoesNotExist:
                timetable = []
        elif request.user.is_teacher:
            timetable = Timetable.objects.filter(teacher=request.user).order_by('day', 'start_time')
        else:
            timetable = Timetable.objects.all().order_by('day', 'start_time')
        
        # Organize timetable by day and time
        timetable_data = {day: {} for day in days}
        for entry in timetable:
            start_str = entry.start_time.strftime('%H:%M')
            end_str = entry.end_time.strftime('%H:%M')
            timetable_data[entry.day].setdefault(start_str, []).append({
            'subject_name': entry.subject,
            'teacher_name': entry.teacher.get_full_name(),
            'class': entry.student_class,
            'section': entry.section,
        })

        
        context = {
            'entries': Timetable.objects.all().order_by('day', 'start_time'),
            'days': days,
            'time_slots': time_slots,
        }
        return render(request, 'timetable_calendar.html', context)

class TimetableUpdateView(LoginRequiredMixin, UpdateView):
    model = Timetable
    form_class = TimetableForm
    template_name = 'timetable_form.html'
    success_url = reverse_lazy('time_table')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Edit Timetable Entry'
        return context

class TimetableDeleteView(LoginRequiredMixin, DeleteView):
    model = Timetable
    template_name = 'timetable_confirm_delete.html'
    success_url = reverse_lazy('time_table')

class ExamUpdateView(LoginRequiredMixin, UpdateView):
    model = Exam
    form_class = ExamForm
    template_name = 'exam_form.html'
    success_url = reverse_lazy('exam_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if not self.request.user.is_admin:
            kwargs['instance'].teacher = self.request.user
        return kwargs

class ExamDeleteView(LoginRequiredMixin, DeleteView):
    model = Exam
    template_name = 'exam_confirm_delete.html'
    success_url = reverse_lazy('exam_list')