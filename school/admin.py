from django.contrib import admin
from .models import *
# Register your models here.

admin.site.register(Notification)
admin.site.register(StudentTeacherRelationship)
@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ('name', 'subject', 'date', 'student_class', 'section', 'teacher')
    list_filter = ('date', 'student_class', 'section', 'teacher')
    search_fields = ('name', 'subject', 'student_class')