from django.db import models

class SpaceWeatherEvent(models.Model):
    EVENT_TYPES = [
        ('GEOMAGNETIC_STORM', 'Geomagnetic Storm'),
        ('SOLAR_FLARE', 'Solar Flare'),
        ('OTHER', 'Other'),
    ]

    event_type = models.CharField(max_length=50, choices=EVENT_TYPES)
    start_time = models.DateTimeField()
    max_kp_index = models.FloatField(null=True, blank=True)
    solar_wind_speed = models.FloatField(null=True, blank=True)
    bz_gsm = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"{self.get_event_type_display()} - {self.start_time}"


class UserStory(models.Model):
    event = models.ForeignKey(SpaceWeatherEvent, on_delete=models.CASCADE, related_name='stories')
    author_name = models.CharField(max_length=100, default="Anonymous")  # ✅ REQUIRED
    story_text = models.TextField()
    submission_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Story by {self.author_name} on {self.submission_time:%Y-%m-%d}"
