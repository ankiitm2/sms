# school/admin
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


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('subject', 'sender', 'sent_at', 'recipients_list')
    list_filter = ('sent_at', 'sender')
    search_fields = ('subject', 'sender__first_name', 'sender__last_name', 'body')
    filter_horizontal = ('recipients',)
    
    def recipients_list(self, obj):
        return ", ".join([r.get_full_name() for r in obj.recipients.all()])
    recipients_list.short_description = 'Recipients'