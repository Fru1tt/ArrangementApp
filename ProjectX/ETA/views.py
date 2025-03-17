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
            return redirect('login')# After successful registration, redirect to login
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
        form = EventForm(request.POST, request.FILES, instance=event)# Include request.FILES in case there are file fields (e.g., image uploads)
        if form.is_valid():
            form.save()
            return redirect('event_detail', event_id=event.id)
    else:
        form = EventForm(instance=event)
    
    return render(request, 'ETA/event_edit.html', {'form': form, 'event': event})

#-----------------------------Friend Search----------------------#
from django.contrib.auth import get_user_model

User = get_user_model()

@login_required
def friend_page(request):
    query = request.GET.get('q', '')
    results = []
    if query:
        results = User.objects.filter(username__icontains=query).exclude(id=request.user.id) # Filter users by username (case-insensitive), excluding the current user.
    
    friend_requests = request.user.friend_requests_received.all() # Get incoming friend requests for the current user.
    
    current_friends = request.user.profile.friends.all()# Get current friends from the user's profile.
    
    context = {
        'query': query,
        'results': results,
        'friend_requests': friend_requests,
        'current_friends': current_friends,
    }
    return render(request, 'ETA/friend_page.html', context)

#-----------------------------Friend request----------------------#
from .models import FriendRequest
@login_required
def send_friend_request(request, to_user_id):
    to_user = get_object_or_404(User, id=to_user_id)
    if to_user != request.user:# Prevent sending a request to yourself
        FriendRequest.objects.get_or_create(from_user=request.user, to_user=to_user)
    return redirect('friend_page')  # Or redirect to the user's profile

@login_required
def accept_friend_request(request, request_id):
    friend_request = get_object_or_404(FriendRequest, id=request_id) # Ensure the current user is the recipient of the friend request
   
    if friend_request.to_user == request.user: # Add the sender's profile to the current user's friends.
        request.user.profile.friends.add(friend_request.from_user.profile) # With a symmetrical ManyToManyField, this relationship is automatically reciprocated.
        friend_request.delete()  # Remove the friend request once accepted.
    return redirect('friend_page')

@login_required
def decline_friend_request(request, request_id):
    friend_request = get_object_or_404(FriendRequest, id=request_id)# Ensure the current user is the recipient
    if friend_request.to_user == request.user:
        friend_request.delete()  # Simply delete the request.
    return redirect('friend_page')
