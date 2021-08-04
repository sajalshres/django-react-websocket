from django.urls import path

from .views import (
    csrf_view,
    login_view,
    logout_view,
    register_vew,
    SessionView,
    WhoAmIView,
)

urlpatterns = [
    path("csrf/", csrf_view, name="api-csrf"),
    path("register/", register_vew, name="api-register"),
    path("login/", login_view, name="api-login"),
    path("logout/", logout_view, name="api-logout"),
    path("session/", SessionView.as_view(), name="api-session"),
    path("whoami/", WhoAmIView.as_view(), name="api-whoami"),
]
