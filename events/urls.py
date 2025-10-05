# events/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('', views.event_timeline, name='event_timeline'),
    path('events/<int:event_id>/', views.event_detail, name='event_detail'),
    # Add this new line for the forecast page
    path('forecast/', views.aurora_forecast, name='aurora_forecast'),
]