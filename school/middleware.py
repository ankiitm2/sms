# school/middleware.py
from django.http import HttpResponseForbidden

class RoleAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Skip for auth URLs
        if request.path.startswith(('/accounts/', '/authentication/')):
            return self.get_response(request)
            
        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        # Skip middleware for auth pages
        if request.path.startswith(('/accounts/', '/authentication/')):
            return None
            
        if not request.user.is_authenticated:
            return None
            
        # Default all authenticated users to student dashboard if no role is set
        if 'dashboard' in request.path:
            if not any([request.user.is_teacher, request.user.is_student, request.user.is_admin]):
                request.user.is_student = True  # Auto-assign student role
                request.user.save()
                from django.urls import reverse
                from django.shortcuts import redirect
                return redirect('student_dashboard')
                
        return None