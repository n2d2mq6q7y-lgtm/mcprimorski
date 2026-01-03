from django.urls import path
from . import views

urlpatterns = [
    path('', views.book_appointment, name='book_appointment'),
    path('success/', views.appointment_success, name='appointment_success'),
    path('ajax/load-doctors/', views.load_doctors, name='ajax_load_doctors'),
    path('ajax/load-available-times/', views.load_available_times, name='ajax_load_available_times'),
]
