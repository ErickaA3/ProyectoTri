from django.urls import path
from . import views

app_name = 'esquemas'

urlpatterns = [
    path('', views.esquemas_home, name='home'),
]
#porque hans es tan despreocupado