from django.shortcuts import render
from .models import Event

def event_list(request):
    events = Event.objects.all().order_by('date')
    return render(request, 'ETA/event_list.html', {'events': events})
