from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    path('', views.data_core, name='data_core'),
]
