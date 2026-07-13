# accounts/forms.py
from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from .models import User
import re

class CyberLoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in ['username', 'password']:
            if field_name in self.fields:
                self.fields[field_name].widget.attrs.update({
                    'class': 'input-field',
                    'placeholder': 'Portal Handle' if field_name == 'username' else '••••••••'
                })

class CyberRegistrationForm(UserCreationForm):
    email = forms.EmailField(widget=forms.EmailInput(attrs={
        'class': 'input-field',
        'placeholder': 'citizen@nexus.com'
    }))
    sector = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'input-field',
        'placeholder': 'Sector 1'
    }))
    
    class Meta:
        model = User
        fields = ['username', 'email', 'sector']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'input-field'
        # Override username field with stricter constraints
        self.fields['username'].widget.attrs.update({
            'class': 'input-field',
            'placeholder': 'e.g. johnDoe',
            'id': 'id_username',
            'minlength': '3',
            'maxlength': '15',
            'pattern': '[a-zA-Z0-9_]+',
        })
        self.fields['username'].help_text = (
            "3-15 characters. At least 1 uppercase letter required. Letters, numbers, underscores only."
        )

    def clean_password2(self):
        password = self.cleaned_data.get('password1', '')

        # Minimum 8 characters
        if len(password) < 8:
            raise forms.ValidationError("Password must be at least 8 characters long.")

        # At least 1 uppercase letter
        if not re.search(r'[A-Z]', password):
            raise forms.ValidationError("Password must contain at least 1 uppercase letter.")

        # At least 1 number
        if not re.search(r'[0-9]', password):
            raise forms.ValidationError("Password must contain at least 1 number.")

        # Allowed characters only: letters, digits, underscore, @
        if not re.match(r'^[a-zA-Z0-9_@]+$', password):
            raise forms.ValidationError(
                "Password may only contain letters, numbers, underscores (_) and @ symbol."
            )

        return super().clean_password2()

    def clean_username(self):
        username = self.cleaned_data.get('username', '')

        # Enforce minimum length
        if len(username) < 3:
            raise forms.ValidationError("Username must be at least 3 characters long.")

        # Enforce maximum length
        if len(username) > 15:
            raise forms.ValidationError("Username must be 15 characters or fewer.")

        # Enforce at least 1 uppercase letter
        if not re.search(r'[A-Z]', username):
            raise forms.ValidationError("Username must contain at least 1 uppercase letter.")

        # Enforce allowed characters (letters, digits, underscores — mixed case allowed)
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            raise forms.ValidationError(
                "Username may only contain letters, numbers, and underscores."
            )

        # Case-insensitive uniqueness check
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("This username is already taken.")

        return username


class CyberAdminRegistrationForm(CyberRegistrationForm):
    security_code = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'input-field',
            'placeholder': 'NEXUS-XXXX-XXXX'
        }),
        help_text="Master Key for Station clearance."
    )
    
    class Meta(CyberRegistrationForm.Meta):
        fields = CyberRegistrationForm.Meta.fields + ['security_code']

    def clean_security_code(self):
        code = self.cleaned_data.get('security_code')
        if code != "NEXUS-ADMIN-2026":
            raise forms.ValidationError("Access Denied: Invalid Security Access Code.")
        return code
