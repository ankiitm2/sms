# school/middleware
from django.http import HttpResponseForbidden

class RoleAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        if not request.user.is_authenticated:
            return None

        # Check if user is trying to access a dashboard not meant for their role
        if 'student_dashboard' in request.path and not request.user.is_student:
            return HttpResponseForbidden()
        if 'teacher_dashboard' in request.path and not request.user.is_teacher:
            return HttpResponseForbidden()
        if 'admin_dashboard' in request.path and not request.user.is_admin:
            return HttpResponseForbidden()
        
        return None