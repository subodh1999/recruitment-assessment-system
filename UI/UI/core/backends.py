from django.contrib.auth.backends import BaseBackend
from django.contrib.auth import get_user_model
from .models import Candidate, Employee

CustomUser = get_user_model() 

class CustomAuthBackend(BaseBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            candidate = Candidate.objects.get(email=username)
            if candidate.password == password: 
                user, created = CustomUser.objects.get_or_create(username=username)
                user.email = username
                user.user_type = 'candidate'
                user.set_unusable_password()
                user.save()
                return user
        except Candidate.DoesNotExist:
            pass

        try:
            employee = Employee.objects.get(email=username)
            if employee.password == password:
                user, created = CustomUser.objects.get_or_create(username=username)
                user.email = username

                if employee.designation == 'HR':
                    user.user_type = 'hr'
                elif employee.designation == 'PM':
                    user.user_type = 'pm'
                else:
                    user.user_type = 'employee'

                user.set_unusable_password()
                user.save()
                return user
        except Employee.DoesNotExist:
            pass

        return None

    def get_user(self, user_id):
        try:
            return CustomUser.objects.get(pk=user_id)
        except CustomUser.DoesNotExist:
            return None