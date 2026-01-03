from django.urls import path
from .views import article_list, article_detail

urlpatterns = [
    path('', article_list, name='articles'),
    path('<int:pk>/', article_detail, name='article_detail'),
]
