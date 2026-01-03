from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('services/', views.services, name='services'),
    path('online/', views.online_consultations, name='online'),
    path('contacts/', views.contacts, name='contacts'),
    path('specialties/', views.specialties_list, name='specialties'),
    path('specialties/<int:pk>/', views.specialty_detail, name='specialty_detail'),
]
