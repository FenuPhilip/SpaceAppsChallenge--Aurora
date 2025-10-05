import requests
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime
from events.models import SpaceWeatherEvent

# Correct NOAA endpoint
API_URL = "https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json"

# We'll consider a Kp-index of 5 or higher to be a significant geomagnetic storm.
STORM_KP_THRESHOLD = 5

class Command(BaseCommand):
    help = 'Fetches the latest Kp-index from NOAA and creates a new event if a storm is detected.'

    def handle(self, *args, **kwargs):
        self.stdout.write("Attempting to fetch latest space weather data...")

        try:
            response = requests.get(API_URL, timeout=10)
            response.raise_for_status()
            data = response.json()

            if not data or len(data) < 2:
                self.stdout.write(self.style.WARNING("No data returned from NOAA."))
                return

            # Skip the first row (header)
            readings = data[1:]

            latest_observed_reading = None
            for reading in reversed(readings):
                # NOAA columns: ["time_tag", "kp_index", "a_index", "station_count", "source"]
                # The last value indicates if it's 'observed' or 'predicted'
                if reading[-1] == 'observed':
                    latest_observed_reading = reading
                    break

            # Fallback: use latest predicted if no observed data exists
            if not latest_observed_reading:
                self.stdout.write(self.style.WARNING("No recent observed Kp-index data found — using latest predicted value."))
                latest_observed_reading = readings[-1]

            timestamp_str = latest_observed_reading[0]
            kp_value = float(latest_observed_reading[1])

            # Convert timestamp string to timezone-aware datetime
            timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))

            self.stdout.write(f"Latest reading: Kp-index of {kp_value} at {timestamp_str}")

            if kp_value >= STORM_KP_THRESHOLD:
                self.stdout.write(self.style.SUCCESS(f"Storm detected! Kp-index is {kp_value}."))

                event, created = SpaceWeatherEvent.objects.get_or_create(
                    event_type='GEOMAGNETIC_STORM',
                    start_time=timestamp,
                    defaults={'max_kp_index': kp_value}
                )

                if created:
                    self.stdout.write(self.style.SUCCESS("✅ Successfully created a new SpaceWeatherEvent."))
                else:
                    self.stdout.write(self.style.WARNING("ℹ️  An event for this time already exists."))
            else:
                self.stdout.write("Conditions are calm. No new event created.")

        except requests.exceptions.RequestException as e:
            self.stderr.write(self.style.ERROR(f"Error fetching data: {e}"))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"An unexpected error occurred: {e}"))
