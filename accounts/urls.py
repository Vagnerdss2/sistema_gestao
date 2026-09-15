from django.urls import path
from django.contrib.auth import views as auth_views
from accounts.views import RegisterView

app_name = "accounts"

urlpatterns = [
    # Cadastro de novo usuário
    path("register/", RegisterView.as_view(), name="register"),

    # Autenticação padrão do Django com templates personalizados
    path("login/", auth_views.LoginView.as_view(template_name="registration/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
]
