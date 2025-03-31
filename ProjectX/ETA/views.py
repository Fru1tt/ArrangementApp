from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib import messages
from django.http import HttpResponseForbidden  
from .models import Event, FriendRequest, Profile, Attendance, EventInvite  
from .forms import EventForm, ProfileUpdateForm
from django.contrib.auth import get_user_model
from .models import Notification
from django.shortcuts import redirect
User = get_user_model()


def event_list(request):
    # Get all public events ordered by start date.
    events = Event.objects.filter(is_public=True).order_by('start_date')
    
    if request.user.is_authenticated:
        # Exclude events where the user is the host.
        public_events = events.exclude(host=request.user)
        events_data = [
            {
                'event': event,
                'attendance': Attendance.objects.filter(user=request.user, event=event).first()
            }
            for event in public_events
        ]
    else:
        # For anonymous users, wrap each event in a dictionary with no attendance.
        events_data = [{'event': event, 'attendance': None} for event in events]
    
    context = {'events_data': events_data}
    return render(request, 'ETA/home.html', context)


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
            event.host = request.user
            event.save()

            if event.is_public:
                for friend in request.user.profile.friends.all():
                    Notification.objects.create(
                        user=friend.user,
                        message="Available event for you",
                        link=f"/event/{event.id}/"
                    )
            return redirect('my_events')
    else:
        form = EventForm()
    return render(request, 'ETA/create_event.html', {'form': form})



def my_events(request):
    if not request.user.is_authenticated:
        messages.warning(request, "You have to log in to use this feature.")
        return redirect('login')
    # Retrieve events where the current user is the host.
    hosted_events = Event.objects.filter(host=request.user).order_by('start_date')
    # Build a list of dictionaries for each hosted event, including the user's attendance record.
    hosted_events_data = [
        {
            'event': event,
            'attendance': Attendance.objects.filter(user=request.user, event=event).first()
        }
        for event in hosted_events
    ]
    context = {'hosted_events_data': hosted_events_data}
    return render(request, 'ETA/my_events.html', context)

@login_required
def profile(request):
    return render(request, 'ETA/profile.html')

def logout_view(request):
    logout(request)
    return redirect('home')

def event_detail(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    attendance = Attendance.objects.filter(user=request.user, event=event).first()
    current_friends = request.user.profile.friends.all()
    invited_ids = list(EventInvite.objects.filter(event=event, from_user=request.user).values_list('to_user', flat=True)
    )
    context = {'event': event, 'attendance': attendance,'current_friends': current_friends, 'invited_ids': invited_ids,}
    return render(request, 'ETA/event_detail.html', context)
   

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

#-----------------------------Friend Search----------------------#
def friend_page(request):
    if not request.user.is_authenticated:
         messages.warning(request, "You have to log in to use this feature.")
         return redirect('login')

    query = request.GET.get('q', '')
    results = []
    if query:
        results = User.objects.filter(username__icontains=query).exclude(id=request.user.id)

    friend_requests = request.user.friend_requests_received.all()
    current_friends = request.user.profile.friends.all()

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
    # Prevent sending a request to yourself
    if to_user != request.user:
        FriendRequest.objects.get_or_create(from_user=request.user, to_user=to_user)
    return redirect('friend_page')  # Or redirect to the user's profile

@login_required
def accept_friend_request(request, request_id):
    friend_request = get_object_or_404(FriendRequest, id=request_id)
    # Ensure the current user is the recipient of the friend request
    if friend_request.to_user == request.user:
        # Add the sender's profile to the current user's friends.
        request.user.profile.friends.add(friend_request.from_user.profile)
        # With a symmetrical ManyToManyField, this relationship is automatically reciprocated.
        friend_request.delete()  # Remove the friend request once accepted.
    return redirect('friend_page')

@login_required
def decline_friend_request(request, request_id):
    friend_request = get_object_or_404(FriendRequest, id=request_id)
    # Ensure the current user is the recipient
    if friend_request.to_user == request.user:
        friend_request.delete()  # Simply delete the request.
    return redirect('friend_page')


#-----------------------------Attendance----------------------#
@login_required
def update_attendance(request):
    if request.method == 'POST':
        event_id = request.POST.get('event_id')
        new_status = request.POST.get('status')
        
        # Validate new_status if desired
        
        event = get_object_or_404(Event, id=event_id)
        attendance, created = Attendance.objects.get_or_create(user=request.user, event=event)
        attendance.status = new_status
        attendance.save()
        
        return redirect('event_detail', event_id=event.id)
    
    # If it's not a POST request, redirect or show an error
    return redirect('home')

 #-----------------------------Manage account----------------------#
@login_required
def manage_account(request):
    # Ensure a profile exists for the user; create one if it doesn't.
    profile, created = Profile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)
        if profile_form.is_valid():
            profile_form.save()
            messages.success(request, 'Your profile picture has been updated successfully!')
            return redirect('manage_account')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        profile_form = ProfileUpdateForm(instance=profile)
    
    return render(request, 'ETA/manage_account.html', {'profile_form': profile_form})

#-----------------------------Event invite----------------------#
@login_required
def send_event_invite(request, event_id, profile_id):
    event = get_object_or_404(Event, id=event_id)
    friend_profile = get_object_or_404(request.user.profile.friends.all(), id=profile_id)

    if not event.is_public and request.user != event.host:
        return redirect('event_detail', event_id=event.id)

    invite, created = EventInvite.objects.get_or_create(
        event=event,
        from_user=request.user,
        to_user=friend_profile.user,
        defaults={'status': 'pending'}
    )

    if not created:
        invite.status = 'pending'
        invite.save()

    # 🔔 Always notify if it's a private event, even if invite already exists
    if not event.is_public:
        Notification.objects.create(
            user=friend_profile.user,
            message="You have been invited",
            link=f"/event/{event.id}/"
        )

    return redirect('event_detail', event_id=event.id)



@login_required
def mark_all_notifications_read(request):
    request.user.notifications.filter(is_read=False).update(is_read=True)
    return redirect('event_list')


@login_required
def view_notification(request, notif_id):
    notif = get_object_or_404(Notification, id=notif_id, user=request.user)
    notif.is_read = True
    notif.save()
    return redirect(notif.link or 'event_list')  # fallback in case link is blank
