# school/signals
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Exam, Notification
from student.models import Student
from django.urls import reverse

@receiver(post_save, sender=Exam)
def create_exam_notification(sender, instance, created, **kwargs):
    if created:
        students = Student.objects.filter(
            student_class=instance.student_class,
            section=instance.section
        ).select_related('user')
        
        for student in students:
            if student.user:
                Notification.objects.create(
                    user=student.user,
                    title=f"New Exam: {instance.name}",
                    message=f"A new {instance.name} exam for {instance.subject} is scheduled on {instance.date}",
                    notification_type='exam',
                    related_url=reverse('exam_list')
                )