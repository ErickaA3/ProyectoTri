from django.urls import path
from . import views

app_name = 'resumenes'

urlpatterns = [
    path('', views.resumenes_home, name='home'),
]