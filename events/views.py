# events/views.py

from django.shortcuts import render, get_object_or_404, redirect
from .models import SpaceWeatherEvent, UserStory
from .forms import UserStoryForm
import requests
from datetime import datetime, timedelta

# --- Views for Event Timeline and Details (No Change) ---

def event_timeline(request):
    events = SpaceWeatherEvent.objects.order_by('-start_time')
    return render(request, 'events/event_timeline.html', {'events': events})

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
    context = {'event': event, 'stories': stories, 'form': form}
    return render(request, 'events/event_detail.html', context)


# --- Updated View for the Live Aurora Forecast ---

def aurora_forecast(request):
    # FINAL CORRECTION: URLs are now plain strings without any extra characters.
    PLASMA_API_URL = "[https://services.swpc.noaa.gov/products/solar-wind/plasma-1-minute.json](https://services.swpc.noaa.gov/products/solar-wind/plasma-1-minute.json)"
    MAG_API_URL = "[https://services.swpc.noaa.gov/products/solar-wind/mag-1-minute.json](https://services.swpc.noaa.gov/products/solar-wind/mag-1-minute.json)"
    
    # NEW: NASA DONKI API for CME alerts (past 7 days)
    end_date = datetime.utcnow().strftime('%Y-%m-%d')
    start_date = (datetime.utcnow() - timedelta(days=7)).strftime('%Y-%m-%d')
    NASA_API_URL = f"[https://api.nasa.gov/DONKI/CME?startDate=](https://api.nasa.gov/DONKI/CME?startDate=){start_date}&endDate={end_date}&api_key=DEMO_KEY"

    # --- Default Context ---
    context = {
        'forecast_level': 'UNKNOWN',
        'forecast_message': 'Could not retrieve live data. Check server logs.',
        'bz_gsm': 'N/A',
        'speed': 'N/A',
        'density': 'N/A',
        'cme_data': [], # To hold NASA CME data
    }

    # --- Fetch NOAA Data ---
    try:
        plasma_response = requests.get(PLASMA_API_URL, timeout=10)
        plasma_response.raise_for_status()
        plasma_data = plasma_response.json()

        mag_response = requests.get(MAG_API_URL, timeout=10)
        mag_response.raise_for_status()
        mag_data = mag_response.json()

        if plasma_data and len(plasma_data) > 1 and mag_data and len(mag_data) > 1:
            latest_plasma = plasma_data[-1]
            latest_mag = mag_data[-1]
            speed = float(latest_plasma[2]) if latest_plasma[2] is not None else 0
            density = float(latest_plasma[1]) if latest_plasma[1] is not None else 0
            bz_gsm = float(latest_mag[3]) if latest_mag[3] is not None else 0

            if bz_gsm < -10 and speed > 400:
                forecast_level = 'HIGH'
                forecast_message = 'Strongly negative Bz and high speed! Excellent aurora potential.'
            elif bz_gsm < -5 and speed > 350:
                forecast_level = 'MODERATE'
                forecast_message = 'Southward Bz and elevated solar wind. Auroral activity is possible.'
            else:
                forecast_level = 'LOW'
                forecast_message = 'Conditions are calm. A visible aurora is not expected.'

            context.update({
                'forecast_level': forecast_level, 'forecast_message': forecast_message,
                'bz_gsm': f"{bz_gsm:.2f} nT", 'speed': f"{speed:.0f} km/s", 'density': f"{density:.2f} p/cm³",
            })
    except requests.exceptions.RequestException as e:
        print(f"Error fetching NOAA data: {e}")

    # --- Fetch NASA CME Data ---
    try:
        nasa_response = requests.get(NASA_API_URL, timeout=15)
        nasa_response.raise_for_status()
        cme_events = nasa_response.json()
        if cme_events:
            # Format the data for the template
            formatted_cmes = []
            for cme in cme_events:
                # Parse the time and format it nicely
                time_str = cme.get('startTime', '')
                if time_str:
                    dt_object = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
                    formatted_time = dt_object.strftime('%B %d, %Y at %H:%M UTC')
                    formatted_cmes.append({
                        'time': formatted_time,
                        'note': cme.get('note', 'No details provided.')
                    })
            context['cme_data'] = formatted_cmes
            
    except requests.exceptions.RequestException as e:
        print(f"Error fetching NASA CME data: {e}")
        context['cme_data'] = [] # Ensure it's an empty list on error

    return render(request, 'events/aurora_forecast.html', context)
