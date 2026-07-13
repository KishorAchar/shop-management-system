from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

class EmailBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        try:
            # Username is CASE-SENSITIVE (exact match).
            # Email lookup remains case-insensitive (emails are case-insensitive by spec).
            users = UserModel.objects.filter(
                Q(email__iexact=username) | Q(username__exact=username)
            )
            for user in users:
                if user.check_password(password):
                    return user
            return None
        except Exception:
            return None
