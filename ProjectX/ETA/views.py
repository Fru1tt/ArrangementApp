from django.shortcuts import render, redirect
from .models import Event
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from .forms import EventForm
from django.contrib.auth import logout




def event_list(request):
    events = Event.objects.all().order_by('start_date')
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
        form = EventForm(request.POST)
        if form.is_valid():
            event = form.save(commit=False)
            event.host = request.user  # Assign the logged-in user as the host
            event.save()
            return redirect('my_events')  # redirect to My Events page after creation
    else:
        form = EventForm()
    return render(request, 'ETA/create_event.html', {'form': form})

@login_required
def my_events(request):
    events = Event.objects.filter(host=request.user).order_by('start_date')
    return render(request, 'ETA/my_events.html', {'events': events})

@login_required
def profile(request):
    return render(request, 'ETA/profile.html')

def logout_view(request):
    logout(request)
    return redirect('event_list')