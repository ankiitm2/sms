from django.urls import path
from .views import (
    index, dashboard, student_dashboard, student_teachers,
    teacher_dashboard, teacher_schedule, create_assignment,
    grade_submissions, take_attendance, teacher_profile,
    teacher_list, add_teacher, edit_teacher, admin_dashboard,
    mark_notification_as_read, clear_all_notification,
    TimetableView, TimetableCreateView, TimetableUpdateView, TimetableCalendarView, TimetableDeleteView, ExamListView, ExamCreateView, ExamUpdateView, ExamDeleteView
)

urlpatterns = [
    path('', index, name="index"),
    path('dashboard/', dashboard, name='dashboard'),
    
    # Student URLs
    path('student/dashboard/', student_dashboard, name='student_dashboard'),
    path('student/teachers/', student_teachers, name='student_teachers'),
    
    # Teacher URLs
    path('teacher/dashboard/', teacher_dashboard, name='teacher_dashboard'),
    path('teacher/schedule/', teacher_schedule, name='teacher_schedule'),
    path('teacher/assignments/create/', create_assignment, name='create_assignment'),
    path('teacher/assignments/grade/', grade_submissions, name='grade_submissions'),
    path('teacher/attendance/', take_attendance, name='attendance'),
    path('teacher/profile/', teacher_profile, name='teacher_profile'),
    path('teachers/', teacher_list, name='teacher_list'),
    path('teachers/add/', add_teacher, name='add_teacher'),
    path('teachers/<int:pk>/edit/', edit_teacher, name='edit_teacher'),
    
    # Timetable URLs
    path('time-table/', TimetableView.as_view(), name='time_table'),
    path('time-table/add/', TimetableCreateView.as_view(), name='add_timetable'),
    path('time-table/<int:pk>/edit/', TimetableUpdateView.as_view(), name='edit_timetable'),
    path('time-table/<int:pk>/delete/', TimetableDeleteView.as_view(), name='delete_timetable'),
    path('time-table/calendar/', TimetableCalendarView.as_view(), name='timetable_calendar'),
    
    path('exams/', ExamListView.as_view(), name='exam_list'),
    path('exams/add/', ExamCreateView.as_view(), name='add_exam'),
    path('exams/<int:pk>/edit/', ExamUpdateView.as_view(), name='edit_exam'),
    path('exams/<int:pk>/delete/', ExamDeleteView.as_view(), name='delete_exam'),

    # Admin URLs
    path('admin/dashboard/', admin_dashboard, name='admin_dashboard'),
    
    # Notification URLs
    path('notification/mark-as-read/', mark_notification_as_read, name='mark_notification_as_read'),
    path('notification/clear-all/', clear_all_notification, name="clear_all_notification"),
]