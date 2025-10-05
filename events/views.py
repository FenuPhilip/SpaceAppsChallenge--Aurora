# events/views.py

from django.shortcuts import render, get_object_or_404, redirect
from .models import SpaceWeatherEvent, UserStory
from .forms import UserStoryForm
import requests

# View for the main event timeline
def event_timeline(request):
    events = SpaceWeatherEvent.objects.order_by('-start_time')
    return render(request, 'events/event_timeline.html', {'events': events})

# View for a single event's detail page
def event_detail(request, event_id):
    event = get_object_or_404(SpaceWeatherEvent, pk=event_id)
    
    if request.method == 'POST':
        form = UserStoryForm(request.POST)
        if form.is_valid():
            new_story = form.save(commit=False)
            new_story.event = event
            new_story.save()
            return redirect('event_detail', event_id=event.id)
    else:
        form = UserStoryForm()

    stories = event.stories.order_by('-submission_time')
    
    context = {
        'event': event,
        'stories': stories,
        'form': form
    }
    
    return render(request, 'events/event_detail.html', context)

# View for the live aurora forecast
def aurora_forecast(request):
    # CORRECTED: API URLs are now plain strings
    PLASMA_API_URL = "[https://services.swpc.noaa.gov/products/solar-wind/plasma-1-minute.json](https://services.swpc.noaa.gov/products/solar-wind/plasma-1-minute.json)"
    MAG_API_URL = "[https://services.swpc.noaa.gov/products/solar-wind/mag-1-minute.json](https://services.swpc.noaa.gov/products/solar-wind/mag-1-minute.json)"
    
    context = {
        'forecast_level': 'UNKNOWN',
        'forecast_message': 'Could not retrieve live data from NOAA.',
        'bz_gsm': 'N/A',
        'speed': 'N/A',
        'density': 'N/A',
    }

    try:
        # Fetch plasma data (speed, density)
        plasma_response = requests.get(PLASMA_API_URL, timeout=10)
        plasma_response.raise_for_status()
        plasma_data = plasma_response.json()

        # Fetch magnetometer data (Bz)
        mag_response = requests.get(MAG_API_URL, timeout=10)
        mag_response.raise_for_status()
        mag_data = mag_response.json()

        if plasma_data and len(plasma_data) > 1 and mag_data and len(mag_data) > 1:
            latest_plasma = plasma_data[-1]
            latest_mag = mag_data[-1]

            # Extract data, handling potential None values
            speed = float(latest_plasma[2]) if latest_plasma[2] is not None else 0
            density = float(latest_plasma[1]) if latest_plasma[1] is not None else 0
            bz_gsm = float(latest_mag[3]) if latest_mag[3] is not None else 0

            # --- More Accurate Prediction Logic ---
            if bz_gsm < -10 and speed > 400:
                forecast_level = 'HIGH'
                forecast_message = 'Strongly negative Bz and high speed! Excellent aurora potential for high-latitude locations.'
            elif bz_gsm < -5 and speed > 350:
                forecast_level = 'MODERATE'
                forecast_message = 'Southward Bz and elevated solar wind. Auroral activity is possible.'
            else:
                forecast_level = 'LOW'
                forecast_message = 'Conditions are calm. A visible aurora is not expected.'

            context.update({
                'forecast_level': forecast_level,
                'forecast_message': forecast_message,
                'bz_gsm': f"{bz_gsm:.2f} nT",
                'speed': f"{speed:.0f} km/s",
                'density': f"{density:.2f} p/cm³",
            })

    except requests.exceptions.RequestException as e:
        print(f"Error fetching forecast data: {e}") # For debugging

    return render(request, 'events/aurora_forecast.html', context)