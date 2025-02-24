from django.shortcuts import render, redirect
from .models import Event
from django.contrib.auth.forms import UserCreationForm

def event_list(request):
    events = Event.objects.all().order_by('date')
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