from django.urls import path
from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy
from django.views.generic.base import RedirectView
from . import views

urlpatterns = [
    path('', RedirectView.as_view(url='/user/login', permanent=False)),
    path(
        'login', 
        auth_views.LoginView.as_view(
            template_name='users/login.html', 
        ), 
        name = 'login'
    ),
    path(
        'logout', 
        auth_views.LogoutView.as_view(
            template_name='users/logout.html',
        ),
        name='logout'
    ),
    path(
        'password-change', 
        auth_views.PasswordChangeView.as_view(
            template_name='users/password_change.html',
            success_url=reverse_lazy('password_change_done'),
        ),
        name='password_change'    
    ),
    path(
        'password-change-done', 
        auth_views.PasswordChangeDoneView.as_view(  
            template_name='users/password_change_done.html'
        ),
        name='password_change_done'
    ),
    path(
        'password-reset', 
        auth_views.PasswordResetView.as_view(
            template_name='users/password_reset_form.html',
            email_template_name='users/password_reset_email.html',
            subject_template_name='users/password_reset_subject.txt',
            success_url=reverse_lazy('password_reset_done'),
            from_email='shop@email.com',
        ), 
        name='password_reset'
    ),
    path(
        'password-reset-done',
	    auth_views.PasswordResetDoneView.as_view(
		    template_name='users/password_reset_done.html'  
	    ),
	    name='password_reset_done'
    ),
    path(
        'password-reset-confirm/<str:uidb64>/<str:token>',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='users/password_reset_confirm.html',
            success_url='password_reset_complete',
        ),
        name='password_reset_confirm'
    ),
    path(
        'password-reset-complete',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='users/password_reset_complete.html',
        ),
        name='password_reset_complete'
    ),
    path(
        'signup',
        views.SignUpView.as_view(),
        name='signup'
    ),
    path(
        'signup-success',
        views.SignUpSuccessView.as_view(),
        name='signup_success'
    )
]