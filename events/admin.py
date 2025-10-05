from django.contrib import admin
from .models import SpaceWeatherEvent, UserStory

# Register your models here so they appear in the admin site.
admin.site.register(SpaceWeatherEvent)
admin.site.register(UserStory)