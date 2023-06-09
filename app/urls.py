from django.urls import path
from . import views

urlpatterns = [
    path('phsays/', views.phsays, name='phsays'),
]