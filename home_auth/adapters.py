# home_auth/adapters.py
from allauth.account.adapter import DefaultAccountAdapter
from django.urls import reverse
from django.http import HttpResponseRedirect

class CustomAccountAdapter(DefaultAccountAdapter):
    def get_login_redirect_url(self, request):
        if request.user.is_authenticated:
            if request.user.is_teacher:
                return reverse('teacher_dashboard')
            elif request.user.is_student:
                return reverse('student_dashboard')
            elif request.user.is_admin:
                return reverse('admin_dashboard')
        return super().get_login_redirect_url(request)