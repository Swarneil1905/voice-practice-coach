from django.urls import path
from . import views

urlpatterns = [
    path("api/health", views.health),
    path("api/capabilities", views.capabilities),
    path("api/practice/review", views.review),
    path("api/voice/token", views.voice_token),
]
