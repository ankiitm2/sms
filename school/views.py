# school/views.py
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from .models import Notification, Department
from django.contrib.auth.decorators import login_required
from home_auth.models import CustomUser
from django.contrib.auth.hashers import make_password
from django.contrib import messages
from .models import StudentTeacherRelationship, Timetable, Exam
from django.views.generic import ListView
from student.models import Student
from django.views.generic import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from .forms import TimetableForm, ExamForm, DepartmentForm
from datetime import time
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
import datetime
from django.utils import timezone
from django.db.models import Q
from django.core.exceptions import PermissionDenied
from .models import Message, MessageAttachment, Holiday, Subject
from .forms import MessageForm, HolidayForm, SubjectForm
from django.contrib import messages
from django.core.paginator import Paginator
from django.urls import reverse


def index(request):
    # Redirect to login page or dashboard based on authentication
    if request.user.is_authenticated:
        return redirect('dashboard')
    return redirect('login') 


@login_required
def all_notifications(request):
    notifications = request.user.notifications.all().order_by('-created_at')
    
    # Counts for filters
    unread_count = request.user.notifications.filter(is_read=False).count()
    read_count = request.user.notifications.filter(is_read=True).count()
    exam_count = request.user.notifications.filter(notification_type='exam').count()
    assignment_count = request.user.notifications.filter(notification_type='assignment').count()
    announcement_count = request.user.notifications.filter(notification_type='announcement').count()
    message_count = request.user.notifications.filter(notification_type='message').count()
    
    context = {
        'notifications': notifications,
        'unread_count': unread_count,
        'read_count': read_count,
        'exam_count': exam_count,
        'assignment_count': assignment_count,
        'announcement_count': announcement_count,
        'message_count': message_count,
    }
    return render(request, 'notifications/all.html', context)

@login_required
def get_unread_notifications(request):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        notifications = request.user.notifications.filter(is_read=False).order_by('-created_at')[:5]
        data = {
            'notifications': [
                {
                    'id': str(notif.id),
                    'title': notif.title,
                    'message': notif.message,
                    'time_since': notif.time_since,
                    'is_read': notif.is_read,
                    'url': notif.related_url or '#',
                } for notif in notifications
            ],
            'unread_count': request.user.notifications.filter(is_read=False).count()
        }
        return JsonResponse(data)
    return JsonResponse({}, status=400)

@login_required
def mark_notification_as_read(request, notification_id=None):
    if request.method == 'POST':
        if notification_id:
            # Mark single notification as read
            request.user.notifications.filter(id=notification_id).update(is_read=True)
        else:
            # Mark all notifications as read
            request.user.notifications.filter(is_read=False).update(is_read=True)
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def delete_notification(request, notification_id):
    if request.method == 'POST':
        request.user.notifications.filter(id=notification_id).delete()
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)

def unread_notification_count(request):
    if request.user.is_authenticated:
        count = request.user.notifications.filter(is_read=False).count()
        return JsonResponse({'count': count})
    return JsonResponse({'count': 0})

def auth_status(request):
    return JsonResponse({
        'authenticated': request.user.is_authenticated,
        'username': getattr(request.user, 'username', None),
        'is_student': getattr(request.user, 'is_student', False),
        'is_teacher': getattr(request.user, 'is_teacher', False),
        'is_admin': getattr(request.user, 'is_admin', False),
        'session': dict(request.session),
    })

@login_required
def dashboard(request):
    if not request.user.is_authenticated:
        return redirect('login')
    
    # Default to student dashboard if no role is set
    if not any([request.user.is_teacher, request.user.is_student, request.user.is_admin]):
        request.user.is_student = True
        request.user.save()
    
    if request.user.is_teacher:
        return redirect('teacher_dashboard')
    elif request.user.is_admin:
        return redirect('admin_dashboard')
    
    # Default case (including is_student=True)
    return redirect('student_dashboard')
    
@login_required
def student_dashboard(request):
    if not request.user.is_student:
        return HttpResponseForbidden()
    
    try:
        student = Student.objects.get(user=request.user)
        today = timezone.now().date()
        
        # Get all exams for student's class and section
        exams = Exam.objects.filter(
            student_class=student.student_class,
            section=student.section
        ).order_by('date', 'start_time')
        
        # Separate into upcoming and past exams
        upcoming_exams = exams.filter(date__gte=today)
        past_exams = exams.filter(date__lt=today)
        
        context = {
            'user': request.user,
            'student': student,
            'exams': exams,  # Pass all exams
            'upcoming_exams': upcoming_exams,
            'past_exams': past_exams,
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
            request.user.qualification = request.POST.get('qualification')
            request.user.specialization = request.POST.get('specialization')
            request.user.bio = request.POST.get('bio')
            
            # Handle department assignment
            department_id = request.POST.get('department')
            if department_id:
                try:
                    department = Department.objects.get(id=department_id)
                    request.user.department = department
                except Department.DoesNotExist:
                    messages.error(request, 'Selected department does not exist')
            else:
                request.user.department = None
            
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
    
    departments = Department.objects.all()
    context = {
        'user': request.user,
        'departments': departments,
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
            # Automatically set the teacher to the current user if they're a teacher
            if self.request.user.is_teacher:
                form.instance.teacher = self.request.user
            elif not self.request.user.is_admin:
                # Only admins can assign exams to other teachers
                raise PermissionDenied("You don't have permission to create exams")
            
            response = super().form_valid(form)
            
            # Create notifications for students in this class/section
            students = Student.objects.filter(
                student_class=form.instance.student_class,
                section=form.instance.section
            ).select_related('user')
            
            for student in students:
                if student.user:  # Check if student has a user account
                    Notification.objects.create(
                        user=student.user,
                        message=f"New exam scheduled: {form.instance.name} on {form.instance.date}"
                    )
            
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
            return queryset.filter(teacher=user).order_by('date', 'start_time')
        elif user.is_student:
            try:
                student = Student.objects.get(user=user)
                return queryset.filter(
                    student_class=student.student_class,
                    section=student.section
                ).order_by('date', 'start_time')
            except Student.DoesNotExist:
                return queryset.none()
        elif user.is_admin:
            return queryset.order_by('date', 'start_time')
        
        return queryset.none()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['today'] = timezone.now().date()
        return context


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
        user = self.request.user
        
        if user.is_student:
            try:
                student = Student.objects.get(user=user)
                return queryset.filter(
                    student_class=student.student_class,
                    section=student.section
                ).order_by('day', 'start_time')
            except Student.DoesNotExist:
                messages.error(self.request, "Student profile not complete. Please update your class and section.")
                return queryset.none()
        elif user.is_teacher:
            # Teachers see their own entries plus all entries for their classes
            classes_teaching = queryset.filter(teacher=user).values_list(
                'student_class', 'section'
            ).distinct()
            return queryset.filter(
                Q(teacher=user) |
                Q(student_class__in=[c[0] for c in classes_teaching],
                  section__in=[c[1] for c in classes_teaching])
            ).order_by('day', 'start_time')
        elif user.is_admin:
            return queryset.order_by('day', 'start_time')
        return queryset.none()
    
class TimetableCalendarView(LoginRequiredMixin, View):
    def get(self, request):
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
        time_slots = [time(h, 0).strftime('%H:%M') for h in range(8, 18)]  # 8AM to 6PM
        
        # Initialize a complete data structure
        timetable_data = {
            day: {time_slot: None for time_slot in time_slots}
            for day in days
        }
        
        # Get appropriate timetable entries
        try:
            if request.user.is_student:
                student = Student.objects.get(user=request.user)
                entries = Timetable.objects.filter(
                    student_class=student.student_class,
                    section=student.section
                ).order_by('day', 'start_time')
            elif request.user.is_teacher:
                entries = Timetable.objects.filter(
                    teacher=request.user
                ).order_by('day', 'start_time')
            else:  # admin
                entries = Timetable.objects.all().order_by('day', 'start_time')
            
            # Populate the timetable_data structure
            for entry in entries:
                day = entry.day
                time_key = entry.start_time.strftime('%H:%M')
                if day in timetable_data and time_key in timetable_data[day]:
                    timetable_data[day][time_key] = entry
                    
        except Student.DoesNotExist:
            messages.error(request, "Student profile not found")
            entries = []
        
        context = {
            'days': days,
            'time_slots': time_slots,
            'timetable_data': timetable_data,  # Structured data for template
            'entries': entries,  # Original queryset for debugging
            'user': request.user,
            'unread_notification_count': Notification.objects.filter(
                user=request.user, 
                is_read=False
            ).count()
        }
        return render(request, 'timetable_calendar.html', context)
    
class TimetableCreateView(LoginRequiredMixin, CreateView):
    model = Timetable
    form_class = TimetableForm
    template_name = 'timetable_form.html'
    success_url = reverse_lazy('time_table')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        try:
            # Set teacher automatically if user is teacher
            if self.request.user.is_teacher:
                form.instance.teacher = self.request.user
            
            # Ensure class and section are properly saved
            student_class = form.cleaned_data['student_class']
            section = form.cleaned_data['section']
            
            # Check for existing entries to prevent duplicates
            if Timetable.objects.filter(
                day=form.cleaned_data['day'],
                start_time=form.cleaned_data['start_time'],
                student_class=student_class,
                section=section
            ).exists():
                messages.error(self.request, 'A timetable entry already exists for this time slot')
                return self.form_invalid(form)
            
            # Save the instance
            self.object = form.save()
            
            messages.success(self.request, 'Timetable entry added successfully!')
            return redirect(self.get_success_url())
            
        except Exception as e:
            messages.error(self.request, f'Error saving timetable: {str(e)}')
            return self.form_invalid(form)

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


@login_required
def inbox(request):
    # Get filter parameter from request
    message_filter = request.GET.get('filter', 'all')
    
    # Get messages based on filter and user role
    if request.user.is_admin:
        # Admin can see all messages
        if message_filter == 'inbox':
            messages = Message.objects.filter(recipients=request.user, parent__isnull=True)
        elif message_filter == 'sent':
            messages = Message.objects.filter(sender=request.user, parent__isnull=True)
        else:  # 'all'
            messages = Message.objects.filter(
                Q(recipients=request.user) | Q(sender=request.user),
                parent__isnull=True
            ).distinct()
    else:
        # Regular users see normal filtered messages
        if message_filter == 'inbox':
            messages = request.user.received_messages.filter(parent__isnull=True)
        elif message_filter == 'sent':
            messages = request.user.sent_messages.filter(parent__isnull=True)
        else:  # 'all'
            messages = (request.user.received_messages.filter(parent__isnull=True) | 
                       request.user.sent_messages.filter(parent__isnull=True)).distinct()
    
    # Order by most recent and paginate
    messages = messages.order_by('-sent_at')
    paginator = Paginator(messages, 10)
    page_number = request.GET.get('page')
    messages = paginator.get_page(page_number)
    
    return render(request, 'inbox/inbox.html', {
        'messages': messages,
        'current_filter': message_filter,
        'unread_count': request.user.received_messages.filter(is_read=False).count()
    })

@login_required
def message_detail(request, message_id):
    message = get_object_or_404(
        Message.objects.select_related('sender'),
        Q(id=message_id),
        Q(recipients=request.user) | Q(sender=request.user)
    )
    
    # Mark as read if recipient
    if request.user in message.recipients.all() and not message.is_read:
        message.is_read = True
        message.save()
    
    # Get complete thread
    thread_messages = Message.objects.filter(
        Q(id=message_id) | Q(parent=message_id)
    ).order_by('sent_at').select_related('sender').prefetch_related('recipients')
    
    if request.method == 'POST':
        form_data = request.POST.copy()
        form_data['subject'] = f"Re: {message.subject}"
        form_data['parent'] = message.id
        
        form = MessageForm(form_data, request.FILES)
        if form.is_valid():
            reply = form.save(commit=False)
            reply.sender = request.user
            reply.parent = message
            reply.save()
            
            # Set recipients - include all original recipients plus sender
            recipients = list(message.recipients.all())
            if message.sender not in recipients:
                recipients.append(message.sender)
            reply.recipients.set(recipients)
            
            # Handle attachments
            files = request.FILES.getlist('attachments')
            for f in files:
                MessageAttachment.objects.create(message=reply, file=f)
            
            # Create toast notification
            messages.success(request, 'Reply sent successfully!')
            
            for recipient in recipients:
                if recipient != request.user:
                    # Create notification with proper URL
                    notification = Notification.objects.create(
                        user=recipient,
                        title=f"New message: {message.subject}",
                        message=f"New message from {request.user.get_full_name()}",
                        notification_type='message',
                        related_url=reverse('message_detail', args=[message.id])
                    )
                    
                    # For students, ensure they can access the message
                    if recipient.is_student:
                        # Make sure student has permission to view the message
                        message.recipients.add(recipient)
                        message.save()
    
    else:
        initial = {
            'parent': message.id,
            'subject': f"Re: {message.subject}",
            'body': f"\n\n--- Original Message ---\n{message.body}",
            'recipients': [message.sender.id]
        }
        form = MessageForm(initial=initial)
    
    return render(request, 'inbox/message_detail.html', {
        'message': message,
        'thread_messages': thread_messages,
        'form': form,
        'can_delete': (request.user.is_admin or request.user == message.sender) and not request.user.is_student
    })

@login_required
def compose_message(request, reply_to=None):
    parent = None
    if reply_to:
        parent = get_object_or_404(Message, id=reply_to)
    
    if request.method == 'POST':
        form = MessageForm(request.POST, request.FILES)
        if form.is_valid():
            message = form.save(commit=False)
            message.sender = request.user  # Set sender from request.user
            message.save()
            
            # Add recipients from the form
            recipients = form.cleaned_data['recipients']
            message.recipients.set(recipients)
            
            # Handle multiple file attachments
            files = request.FILES.getlist('attachments')
            for f in files:
                MessageAttachment.objects.create(
                    message=message,
                    file=f
                )
            
            messages.success(request, 'Message sent successfully!')
            return redirect('inbox')
    else:
        initial = {}
        if parent:
            initial = {
                'subject': f"Re: {parent.subject}",
                'parent': parent.id,
                'recipients': [parent.sender.id]
            }
        form = MessageForm(initial=initial)
    
    return render(request, 'inbox/compose.html', {
        'form': form,
        'parent': parent
    })


@login_required
def admin_message_list(request):
    if not request.user.is_admin:
        return HttpResponseForbidden()
    
    messages = Message.objects.all().order_by('-sent_at')
    return render(request, 'admin/message_list.html', {'messages': messages})

@login_required
def delete_message(request, message_id):
    if not request.user.is_admin:
        return HttpResponseForbidden()
    
    message = get_object_or_404(Message, id=message_id)
    
    if request.method == 'POST':
        # Create notifications for all participants
        participants = list(message.recipients.all())
        participants.append(message.sender)
        
        for user in participants:
            if user != request.user:
                Notification.objects.create(
                    user=user,
                    title="Message deleted",
                    message=f"Message '{message.subject}' was deleted by admin",
                    notification_type='message'
                )
        
        message.delete()
        messages.success(request, 'Message deleted successfully')
        return redirect('admin_message_list')
    
    return render(request, 'admin/confirm_delete.html', {'message': message})

class DepartmentListView(LoginRequiredMixin, ListView):
    model = Department
    template_name = 'departments/department_list.html'
    context_object_name = 'departments'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['unread_notification_count'] = Notification.objects.filter(
            user = self.request.user,
            is_read = False
        ).count()
        return context
    
class DepartmentCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Department
    form_class = DepartmentForm
    template_name = 'departments/department_form.html'
    success_url = reverse_lazy('department_list')

    def test_func(self):
        return self.request.user.is_admin

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Department created successfully!')
        return response

class DepartmentUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Department
    form_class = DepartmentForm
    template_name = 'departments/department_form.html'
    success_url = reverse_lazy('department_list')

    def test_func(self):
        return self.request.user.is_admin

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Department updated successfully!')
        return response

class DepartmentDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Department
    template_name = 'departments/department_confirm_delete.html'
    success_url = reverse_lazy('department_list')

    def test_func(self):
        return self.request.user.is_admin

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Department deleted successfully!')
        return super().delete(request, *args, **kwargs)
    

class HolidayListView(LoginRequiredMixin, ListView):
    model = Holiday
    template_name = 'holidays/holiday_list.html'
    context_object_name = 'holidays'

    def get_queryset(self):
        return Holiday.objects.filter(date__gte=timezone.now().date()).order_by('date')
    
class HolidayCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Holiday
    form_class = HolidayForm
    template_name = 'holidays/holiday_form.html'
    success_url = reverse_lazy('holiday_list')

    def test_func(self):
        return self.request.user.is_admin
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Holiday added successfully!')
        return response
    
class HolidayUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Holiday
    form_class = HolidayForm
    template_name = 'holiday/holiday_form.html'
    success_url = reverse_lazy('holiday_list')

    def test_func(self):
        return self.request.user.is_admin
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Holiday updated successfully!')
        return response
    
class HolidayDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Holiday
    template_name = 'holiday/holiday_confirm_delete.html'
    success_url = reverse_lazy('holiday_list')

    def test_func(self):
        return self.request.user.is_admin
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Holiday deleted successfully!')
        return super().delete(request, *args, **kwargs)
    
class SubjectListView(LoginRequiredMixin, ListView):
    model = Subject
    template_name = 'subjects/subject_list.html'
    context_object_name = 'subjects'

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
    
        if user.is_teacher:
            return queryset.filter(teachers=user).order_by('name')
        elif user.is_admin:
            return queryset.all().order_by('name')
        elif user.is_student:
            try:
                student = Student.objects.get(user=user)
                # Query subjects directly by class and section
                return queryset.filter(
                    student_class=student.student_class,
                    section=student.section
                ).order_by('name')
            except Student.DoesNotExist:
                messages.error(self.request, "Student profile not found. Please complete your profile.")
                return queryset.none()
        return queryset.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        if user.is_student:
            try:
                student = Student.objects.get(user=user)
                context['student_class'] = student.student_class
                context['student_section'] = student.section
            except Student.DoesNotExist:
                pass
                
        context['unread_notification_count'] = Notification.objects.filter(
            user=user, 
            is_read=False
        ).count()
        return context


class SubjectCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Subject
    form_class = SubjectForm
    template_name = 'subjects/subject_form.html'
    success_url = reverse_lazy('subject_list')

    def test_func(self):
        return self.request.user.is_admin or self.request.user.is_teacher
    
    def form_valid(self, form):
        response = super().form_valid(form)
        
        # Automatically assign current teacher if user is teacher
        if self.request.user.is_teacher:
            self.object.teachers.add(self.request.user)
            self.object.save()
            
        messages.success(self.request, 'Subject created successfully!')
        return response
    
class SubjectUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Subject
    form_class = SubjectForm
    template_name = 'subjects/subject_form.html'
    success_url = reverse_lazy('subject_list')

    def test_func(self):
        return self.request.user.is_admin or self.request.user in self.get_object().teachers.all()
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Subject updated successfully!')
        return response
    
class SubjectDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Subject
    template_name = 'subjects/subject_confirm_delete.html'
    success_url = reverse_lazy('subject_list')

    def test_func(self):
        return self.request.user.is_admin
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Subject deleted successfully!')
        return super().delete(request, *args, **kwargs)