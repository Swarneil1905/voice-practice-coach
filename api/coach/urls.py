from django.urls import path
from . import views
from .provider import provider

urlpatterns = [
    path("api/provider/<path:operation>", provider),
    path("api/health", views.health),
    path("api/capabilities", views.capabilities),
    path("api/practice/review", views.review),
    path("api/voice/token", views.voice_token),
]
