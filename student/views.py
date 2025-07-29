from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponseForbidden
from .models import *
from school.utils import create_notification
from school.models import Notification
from django.contrib.auth.decorators import login_required


def add_student(request):
    if request.method == 'POST':
        try:
            # Student fields
            student_data = {
                'first_name': request.POST.get('first_name'),
                'last_name': request.POST.get('last_name'),
                'student_id': request.POST.get('student_id'),
                'gender': request.POST.get('gender'),
                'date_of_birth': request.POST.get('date_of_birth'),
                'student_class': request.POST.get('student_class'),
                'joining_date': request.POST.get('joining_date'),
                'mobile_number': request.POST.get('mobile_number'),
                'admission_number': request.POST.get('admission_number'),
                'section': request.POST.get('section'),
                'student_image': request.FILES.get('student_image'),
                # Removed 'religion' as it's not in your model
            }

            # Parent fields
            parent_data = {
                'father_name': request.POST.get('father_name'),
                'father_occupation': request.POST.get('father_occupation'),
                'father_mobile': request.POST.get('father_mobile'),
                'father_email': request.POST.get('father_email'),
                'mother_name': request.POST.get('mother_name'),
                'mother_occupation': request.POST.get('mother_occupation'),
                'mother_mobile': request.POST.get('mother_mobile'),
                'mother_email': request.POST.get('mother_email'),
                'present_address': request.POST.get('present_address'),
                'permanent_address': request.POST.get('permanent_address')
            }

            # Create parent first
            parent = Parent.objects.create(**parent_data)
            
            # Then create student with the parent reference
            student = Student.objects.create(parent=parent, **student_data)
            if request.user.is_authenticated:
                create_notification(request.user, f"Added new student: {student.first_name} {student.last_name} (ID: {student.student_id})")
            messages.success(request, 'Student added successfully')
            return redirect('student_list')

        except Exception as e:
            messages.error(request, f'Error adding student: {str(e)}')
            return render(request, "students/add-student.html")

    return render(request, "students/add-student.html")

def student_list(request):
    student_list = Student.objects.select_related('parent').all()
    unread_notification = request.user.notification_set.filter(is_read=False)
    context = {
        'student_list': student_list,
        'unread_notification': unread_notification,
        'default_avatar': 'img/profiles/avatar-02.jpg'  # Pass default image path
    }
    return render(request, "students/students.html", context)

@login_required
def edit_profile(request):
    if request.method == 'POST':
        try:
            # Update basic user fields for all users
            request.user.first_name = request.POST.get('first_name')
            request.user.last_name = request.POST.get('last_name')
            request.user.email = request.POST.get('email')
            
            if 'profile_picture' in request.FILES:
                if request.user.profile_picture:
                    request.user.profile_picture.delete()
                request.user.profile_picture = request.FILES['profile_picture']
            
            request.user.save()

            # Only handle student-specific fields if user is a student
            if request.user.is_student:
                student, created = Student.objects.get_or_create(
                    user=request.user,
                    defaults={
                        'first_name': request.user.first_name,
                        'last_name': request.user.last_name,
                        'student_class': request.POST.get('student_class', 'Class 1'),
                        'section': request.POST.get('section', 'A'),
                        'date_of_birth': '2000-01-01',
                        'gender': 'Male',
                        'joining_date': timezone.now().date(),
                        'mobile_number': request.POST.get('mobile_number', ''),
                        'admission_number': '',
                        'parent': Parent.objects.create()
                    }
                )
                
                if not created:
                    student.mobile_number = request.POST.get('mobile_number', '')
                    student.student_class = request.POST.get('student_class', 'Class 1')
                    student.section = request.POST.get('section', 'A')
                    student.save()

            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')  # Redirect to view profile after saving
            
        except Exception as e:
            messages.error(request, f'Error updating profile: {str(e)}')
    
    # Prepare context
    context = {
        'user': request.user,
        'unread_notification_count': Notification.objects.filter(
            user=request.user, 
            is_read=False
        ).count()
    }
    
    # Only add student-specific context if user is a student
    if request.user.is_student:
        CLASS_CHOICES = ['Class ' + str(i) for i in range(1, 13)]
        SECTION_CHOICES = ['A', 'B', 'C', 'D']
        
        context.update({
            'class_options': CLASS_CHOICES,
            'section_options': SECTION_CHOICES,
        })
        
        try:
            context['student'] = Student.objects.get(user=request.user)
        except Student.DoesNotExist:
            pass
    
    return render(request, 'profile/edit.html', context)

@login_required
def edit_student_profile(request):
    if not request.user.is_student:
        return HttpResponseForbidden()

    # Get or create student profile
    student, created = Student.objects.get_or_create(user=request.user)
    
    # Define class and section options
    CLASS_CHOICES = [
        'Class 1', 'Class 2', 'Class 3', 'Class 4', 'Class 5',
        'Class 6', 'Class 7', 'Class 8', 'Class 9', 'Class 10',
        'Class 11', 'Class 12'
    ]
    SECTION_CHOICES = ['A', 'B', 'C', 'D']

    if request.method == 'POST':
        try:
            # Update user fields
            request.user.first_name = request.POST.get('first_name')
            request.user.last_name = request.POST.get('last_name')
            request.user.email = request.POST.get('email')
            
            # Handle profile picture upload
            if 'profile_picture' in request.FILES:
                if request.user.profile_picture:
                    request.user.profile_picture.delete()
                request.user.profile_picture = request.FILES['profile_picture']
            
            request.user.save()
            
            # Update student fields
            student.mobile_number = request.POST.get('mobile_number')
            student.student_class = request.POST.get('student_class')
            student.section = request.POST.get('section')
            student.save()
            
            messages.success(request, 'Profile updated successfully!')
            return redirect('student_profile')
            
        except Exception as e:
            messages.error(request, f'Error updating profile: {str(e)}')

    context = {
        'user': request.user,
        'student': student,
        'class_options': CLASS_CHOICES,
        'section_options': SECTION_CHOICES,
        'unread_notification_count': Notification.objects.filter(
            user=request.user, 
            is_read=False
        ).count()
    }
    return render(request, "students/edit_profile.html", context)

def edit_student(request, slug):
    student = get_object_or_404(Student, slug=slug)
    parent = student.parent
    
    if request.method == 'POST':
        try:
            # Update student fields
            student.first_name = request.POST.get('first_name')
            student.last_name = request.POST.get('last_name')
            student.student_id = request.POST.get('student_id')
            student.gender = request.POST.get('gender')
            student.date_of_birth = request.POST.get('date_of_birth')
            student.student_class = request.POST.get('student_class')
            student.joining_date = request.POST.get('joining_date')
            student.mobile_number = request.POST.get('mobile_number')
            student.admission_number = request.POST.get('admission_number')
            student.section = request.POST.get('section')
            
            # Handle image upload
            if 'student_image' in request.FILES:
                # Delete old image if exists
                if student.student_image:
                    student.student_image.delete()
                student.student_image = request.FILES['student_image']
            
            # Update parent fields
            parent.father_name = request.POST.get('father_name')
            parent.father_occupation = request.POST.get('father_occupation')
            parent.father_mobile = request.POST.get('father_mobile')
            parent.father_email = request.POST.get('father_email')
            parent.mother_name = request.POST.get('mother_name')
            parent.mother_occupation = request.POST.get('mother_occupation')
            parent.mother_mobile = request.POST.get('mother_mobile')
            parent.mother_email = request.POST.get('mother_email')
            parent.present_address = request.POST.get('present_address')
            parent.permanent_address = request.POST.get('permanent_address')
            
            # Save both objects
            parent.save()
            student.save()
            
            messages.success(request, 'Student updated successfully')
            return redirect('student_list')
            
        except Exception as e:
            messages.error(request, f'Error updating student: {str(e)}')
    
    context = {
        'student': student,
        'parent': parent,
        'date_of_birth': student.date_of_birth.strftime('%Y-%m-%d'),
        'joining_date': student.joining_date.strftime('%Y-%m-%d')
    }
    return render(request, "students/edit-student.html", context)

@login_required
def view_profile(request):
    context = {
        'user': request.user,
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
    
    return render(request, 'profile/view.html', context)

def view_student(request, slug):
    student = get_object_or_404(Student, slug=slug)
    context = {'student': student}
    return render(request, "students/student-details.html", context)

def delete_student(request, slug):
    if request.method == 'POST':
        student = get_object_or_404(Student, slug=slug)
        student_name = f"{student.first_name} {student.last_name}"
        if request.user.is_authenticated:
            create_notification(request.user, f"Deleted student: {student_name} (ID: {student.student_id})")
        student.delete()
        messages.success(request, 'Student deleted successfully')
        return redirect('student_list')
    return HttpResponseForbidden()