from django.db import models
from django.utils.text import slugify
from home_auth.models import CustomUser
from django.utils import timezone

# Create your models here.
class Parent(models.Model):
    father_name = models.CharField(max_length=100)
    father_occupation = models.CharField(max_length=100)
    father_email = models.EmailField(max_length=100)
    father_mobile = models.CharField(max_length=100)
    mother_name = models.CharField(max_length=100)
    mother_occupation = models.CharField(max_length=100, null=True, blank=True)
    mother_mobile = models.CharField(max_length=100)
    mother_email = models.EmailField(max_length=100)
    present_address = models.TextField(max_length=100)
    permanent_address = models.TextField(max_length=100)

    def __str__(self):
        return f"{self.father_name} & {self.mother_name}"
    
class Student(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    student_id = models.CharField(max_length=100)
    gender = models.CharField(max_length=10, choices=[('Male','Male'), ('Female', 'Female'), ("Others", 'Others')])
    date_of_birth = models.DateField()
    student_class = models.CharField(max_length=100)
    joining_date = models.DateField()
    mobile_number = models.CharField(max_length=15, default='')
    admission_number = models.CharField(max_length=15)
    section = models.CharField(max_length=15)
    student_image = models.ImageField(upload_to='student/', blank=True, null=True)
    parent = models.OneToOneField(Parent, on_delete=models.CASCADE)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    user = models.OneToOneField(
        CustomUser, 
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='student_profile'
    )

    def save(self, *args, **kwargs):
        # Delete old image when updating
        if self.pk:
            try:
                old = Student.objects.get(pk=self.pk)
                if old.student_image and old.student_image != self.student_image:
                    old.student_image.delete(save=False)
            except Student.DoesNotExist:
                pass

        if not self.date_of_birth:
            self.date_of_birth = '2000-01-01'
        if not self.joining_date:
            self.joining_date = timezone.now().date()
        if not self.gender:
            self.gender = 'Male'
        if not self.student_class:
            self.student_class = 'Class 1'
        if not self.section:
            self.section = 'A'
        
        # Generate slug if not exists
        if not self.slug:
            base_slug = slugify(f"{self.first_name}-{self.last_name}-{self.student_id}")
            unique_slug = base_slug
            counter = 1
            
            while Student.objects.filter(slug=unique_slug).exclude(id=self.id).exists():
                unique_slug = f"{base_slug}-{counter}"
                counter += 1
                
            self.slug = unique_slug
            
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Delete image file when student record is deleted"""
        if self.student_image:
            self.student_image.delete()
        super().delete(*args, **kwargs)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.student_id})"