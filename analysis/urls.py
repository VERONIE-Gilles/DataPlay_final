from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
urlpatterns = [path('', views.home, name = "home"),
               path("login-required/",views.login_required_page, name = "login_required"),
               path("login/",views.login, name = "connecter"),
               path("logout/", auth_views.LogoutView.as_view(next_page='home'), name="logout"),
               path("register/", views.register, name="register"),
               path("q1/",views.q1,name="q1"),
               path("q2/", views.q2, name = "q2"),
               path("q3/", views.q3, name = "q3"),
               path("reset-password/", auth_views.PasswordResetView.as_view(template_name="registration/password_reset_form.html"), name="password_reset"),
               path("reset-password/done/", auth_views.PasswordResetDoneView.as_view(), name="password_reset_done"),
               path("reset-password-confirm/<uidb64>/<token>/", auth_views.PasswordResetConfirmView.as_view(), name="password_reset_confirm"),
               path("reset-password-complete/", auth_views.PasswordResetCompleteView.as_view(), name="password_reset_complete"),
               path("contact/", views.contact, name = "contact"),
            ]