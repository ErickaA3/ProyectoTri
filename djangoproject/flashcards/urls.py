from django.urls import path
from . import views

app_name = 'flashcards'

urlpatterns = [
    path('', views.flashcards_home, name='home'),
]