from django.shortcuts import render, redirect, get_object_or_404
from .models import Event
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from .forms import EventForm
from django.contrib.auth import logout
from django.contrib import messages
from django.http import HttpResponse, HttpResponseForbidden

def event_list(request):
    events = Event.objects.filter(is_public=True).order_by('start_date')
    return render(request, 'ETA/event_list.html', {'events': events})

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            # After successful registration, redirect to login
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'ETA/register.html', {'form': form})

@login_required
def create_event(request):
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES)
        if form.is_valid():
            event = form.save(commit=False)
            event.host = request.user  # Assign the logged-in user as the host
            event.save()
            return redirect('my_events')  # redirect to My Events page after creation
    else:
        form = EventForm()
    return render(request, 'ETA/create_event.html', {'form': form})

def my_events(request):
    if not request.user.is_authenticated:
         messages.warning(request, "You have to log in to use this feature.")
         return redirect('login')
    events = Event.objects.filter(host=request.user).order_by('start_date')
    return render(request, 'ETA/my_events.html', {'events': events})

@login_required
def profile(request):
    return render(request, 'ETA/profile.html')

def logout_view(request):
    logout(request)
    return redirect('event_list')

def event_detail(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    return render(request, 'ETA/event_detail.html', {'event': event})

@login_required
def event_edit(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    
    # Only allow the event host to edit the event
    if request.user != event.host:
        return HttpResponseForbidden("You are not allowed to edit this event.")
    
    if request.method == 'POST':
        # Include request.FILES in case there are file fields (e.g., image uploads)
        form = EventForm(request.POST, request.FILES, instance=event)
        if form.is_valid():
            form.save()
            return redirect('event_detail', event_id=event.id)
    else:
        form = EventForm(instance=event)
    
    return render(request, 'ETA/event_edit.html', {'form': form, 'event': event})
