# accounts/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.views.generic import CreateView
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.contrib.auth.views import PasswordResetView, PasswordResetDoneView, PasswordChangeView
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from .forms import CyberLoginForm, CyberRegistrationForm
from .models import User


class CustomPasswordChangeView(PasswordChangeView):
    template_name = 'registration/password_change_form.html'
    success_url = reverse_lazy('inventory:systems')

    def form_valid(self, form):
        messages.success(self.request, "Portal Access Credentials Updated Successfully.")
        return super().form_valid(form)


class CustomPasswordResetView(PasswordResetView):
    """
    Override send_mail to capture the reset link and store it in the session
    so it can be shown directly on the 'done' page (dev convenience).
    """
    template_name = 'registration/password_reset_form.html'
    success_url = reverse_lazy('accounts:password_reset_done_custom')

    def form_valid(self, form):
        # Find the matching user(s) for the submitted email
        email = form.cleaned_data['email']
        users = list(User._default_manager.filter(
            email__iexact=email, is_active=True
        ))

        if users:
            user = users[0]
            uid   = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            # Build the full reset URL
            reset_path = reverse('password_reset_confirm', kwargs={'uidb64': uid, 'token': token})
            protocol   = 'https' if self.request.is_secure() else 'http'
            domain     = self.request.get_host()
            reset_url  = f"{protocol}://{domain}{reset_path}"
            # Store in session so the 'done' view can read it
            self.request.session['password_reset_url'] = reset_url

        return super().form_valid(form)


class CustomPasswordResetDoneView(PasswordResetDoneView):
    """Read the reset URL out of the session and pass it to the template."""
    template_name = 'registration/password_reset_done.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['reset_url'] = self.request.session.pop('password_reset_url', None)
        return ctx

def login_view(request):
    # Customer Marketplace Login
    if request.user.is_authenticated:
        if request.user.role == 'customer':
            return redirect('inventory:inventory_bay')
        return redirect('inventory:command_center')
    
    if request.method == 'POST':
        form = CyberLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}! You are now logged in.")
            if user.role == 'customer':
                return redirect('inventory:inventory_bay')
            return redirect('inventory:command_center')
    else:
        form = CyberLoginForm()
    
    return render(request, 'accounts/login.html', {'form': form, 'title': 'Nexus Marketplace'})

def admin_login_view(request):
    # Operations Staff Login
    if request.user.is_authenticated:
        if request.user.role != 'customer':
            return redirect('inventory:command_center')
        return redirect('inventory:inventory_bay')
    
    if request.method == 'POST':
        form = CyberLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if user.role == 'customer':
                messages.error(request, "Access Denied: High-level clearance required for this terminal.")
                return redirect('accounts:admin_login')
            login(request, user)
            messages.success(request, f"Command Link Established. Welcome, {user.username}.")
            return redirect('inventory:command_center')
    else:
        form = CyberLoginForm()
    
    return render(request, 'accounts/admin_login.html', {'form': form, 'title': 'Operations Command'})

from .forms import CyberLoginForm, CyberRegistrationForm, CyberAdminRegistrationForm

class RegisterView(CreateView):
    model = User
    form_class = CyberRegistrationForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('accounts:login')
    
    def form_valid(self, form):
        user = form.save(commit=False)
        user.role = 'customer'
        user.avatar = user.username[0:2].upper()
        user.save()
        messages.success(self.request, "Welcome, Citizen! Your account has been initialized. Please log in.")
        return redirect('accounts:login')

class AdminRegisterView(CreateView):
    model = User
    form_class = CyberAdminRegistrationForm
    template_name = 'accounts/admin_register.html'
    success_url = reverse_lazy('accounts:admin_login')
    
    def form_valid(self, form):
        user = form.save(commit=False)
        user.role = 'admin'
        user.avatar = user.username[0:2].upper()
        user.save()
        messages.success(self.request, "Command Clearance Granted. Use your terminal to access Ops Control.")
        return redirect('accounts:admin_login')

@login_required
def logout_view(request):
    logout(request)
    messages.info(request, "Session Terminated. You have been safely logged out.")
    return redirect('accounts:login')