#school/urls
from django.urls import path
from .views import (
    index, dashboard, student_dashboard, student_teachers,
    teacher_dashboard, teacher_schedule, create_assignment,
    grade_submissions, take_attendance, teacher_profile, teacher_profile_view, teacher_profile_edit, teacher_list, add_teacher, edit_teacher, admin_dashboard, admin_message_list,
    mark_notification_as_read, get_unread_notifications, delete_notification, all_notifications, unread_notification_count, inbox, message_detail, compose_message, delete_message,
    TimetableView, TimetableCreateView, TimetableUpdateView, TimetableCalendarView, TimetableDeleteView, ExamListView, ExamCreateView, ExamUpdateView, ExamDeleteView, DepartmentListView, DepartmentCreateView, DepartmentUpdateView, DepartmentDeleteView
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
    path('teacher/profile/view/', teacher_profile_view, name='teacher_profile'),
    path('teacher/profile/edit/', teacher_profile_edit, name='teacher_profile_edit'),
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
    path('notifications/', all_notifications, name='all_notifications'),
    path('notifications/unread-count/', unread_notification_count, name='unread_notification_count'),
    path('notifications/unread/', get_unread_notifications, name='get_unread_notifications'),
    path('notifications/mark-as-read/', mark_notification_as_read, name='mark_notification_as_read'),
    path('notifications/mark-as-read/<uuid:notification_id>/', mark_notification_as_read, name='mark_single_notification_as_read'),
    path('notifications/delete/<uuid:notification_id>/', delete_notification, name='delete_notification'),

    path('inbox/', inbox, name='inbox'),
    path('inbox/<int:message_id>/', message_detail, name='message_detail'),
    path('inbox/compose/', compose_message, name='compose_message'),
    path('inbox/compose/<int:reply_to>/', compose_message, name='reply_message'),
    path('inbox/<int:message_id>/delete/', delete_message, name='delete_message'),

    path('admin/messages/', admin_message_list, name='admin_message_list'),
    path('admin/messages/<int:message_id>/delete/', delete_message, name='delete_message'),

    # Department URLs
    path('departments/', DepartmentListView.as_view(), name='department_list'),
    path('departments/add/', DepartmentCreateView.as_view(), name='add_department'),
    path('departments/<int:pk>/edit/', DepartmentUpdateView.as_view(), name='edit_department'),
    path('departments/<int:pk>/delete/', DepartmentDeleteView.as_view(), name='delete_department'),
]