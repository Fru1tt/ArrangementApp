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
from django.views.decorators.http import require_POST
from .algorithm import compute_aura_score
from datetime import datetime
from .models import Profile
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash


User = get_user_model()

#--------------------------------------------------Home page view--------------------------------------------#
def event_list(request):
    user = request.user

    #---------------------- Fetch Public Events ----------------------#
    events = Event.objects.filter(is_public=True).order_by('start_date')

    #---------------------- Upcoming Events Data ----------------------#
    public_events = events.exclude(host=user) if user.is_authenticated else events
    events_data = []
    for event in public_events:
        attendance = (
            Attendance.objects.filter(user=user, event=event).first()
            if user.is_authenticated
            else None
        )

        event.total_going   = event.going_count
        event.friends_going = (
            event.friends_going_count(user)
            if user.is_authenticated
            else 0
        )

        events_data.append({
            'event':      event,
        'attendance': attendance,
        })

    #---------------------- Preparing Friend IDs ----------------------#
    if user.is_authenticated:
        friend_ids = list(user.profile.friends.values_list('id', flat=True))
    else:
        friend_ids = []

    #---------------------- Computing Trending Events ----------------------#
    trending_events = []
    for event in events:
        # Days until the event
        T = (event.start_date.date() - datetime.now().date()).days

        # Friend interactions
        friend_going       = Attendance.objects.filter(event=event, user__in=friend_ids, status='going').count()
        friend_interested  = Attendance.objects.filter(event=event, user__in=friend_ids, status='can go').count()
        friend_not_going   = Attendance.objects.filter(event=event, user__in=friend_ids, status='not going').count()

        # Public interactions
        total_going        = Attendance.objects.filter(event=event, status='going').count()
        total_interested   = Attendance.objects.filter(event=event, status='can go').count()
        total_not_going    = Attendance.objects.filter(event=event, status='not going').count()

        public_going       = total_going - (friend_going if friend_ids else 0)
        public_interested  = total_interested - (friend_interested if friend_ids else 0)
        public_not_going   = total_not_going - (friend_not_going if friend_ids else 0)

        # Compute aura score
        aura_score = compute_aura_score(
            friend_going, friend_interested, friend_not_going,
            public_going, public_interested, public_not_going,
            T
        )
        #-------- Badges-------
        #Users attendance
        attendance = None
        if user.is_authenticated:
            attendance = Attendance.objects.filter(user=user, event=event).first()

        #------ public and friend counter-----
        event.total_going   = event.going_count
        event.friends_going = event.friends_going_count(user) if user.is_authenticated else 0

        trending_events.append({
            'event':      event,
            'aura_score': aura_score,
            'attendance': attendance,
        })

    #---------------------- Sort Trending Events ----------------------#
    trending_events.sort(key=lambda x: x['aura_score'], reverse=True)

    #---------------------- Render Context ----------------------#
    context = {
        'events_with_attendance': events_data,
        'trending_events':        trending_events,
    }
    return render(request, 'ETA/home.html', context)

#---------------------------------------------------------Register account--------------------------------------------------#
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

#---------------------------------------------------------Create event--------------------------------------------------#
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
            for err in form.non_field_errors():
                messages.warning(request, err)
    else:
        form = EventForm()
    return render(request, 'ETA/create_event.html', {'form': form})


#--------------------------------------------------My Events view filter logic--------------------------------------------#
def my_events(request):
    if not request.user.is_authenticated:
        messages.warning(request, "You have to log in to use this feature.")
        return redirect('login')
    
    user = request.user

    # -------------------------------- Hosted Events --------------------------------
    hosted_events = Event.objects.filter(host=user).order_by('start_date')
    hosted_events_data = []
    for event in hosted_events:
        event.total_going   = event.going_count
        event.friends_going = event.friends_going_count(user)

        # your attendance (always None for hosted)
        attendance = None

        hosted_events_data.append({
            'event':      event,
            'attendance': attendance,
        })

    # ---------------------------- Attending Events -------------------------------
    attendance_records = Attendance.objects.filter(
        user=user,
        status__in=['going', 'can go']
    ).exclude(event__host=user)

    attending_events_data = []
    for attendance in attendance_records:
        event = attendance.event
        # promote counts
        event.total_going   = event.going_count
        event.friends_going = event.friends_going_count(user)

        attending_events_data.append({
            'event':      event,
            'attendance': attendance,
        })

    # ---------------------------- Pending Invites --------------------------------
    pending_invites = EventInvite.objects.filter(
        to_user=user,
        status='pending'
    ).exclude(event__host=user)

    # Exclude events user has already attended/responded to
    responded_ids = Attendance.objects.filter(user=user).values_list('event', flat=True)
    pending_invites = pending_invites.exclude(event__in=responded_ids)

    pending_invite_events_data = []
    for invite in pending_invites:
        event = invite.event
        # promote counts
        event.total_going   = event.going_count
        event.friends_going = event.friends_going_count(user)

        pending_invite_events_data.append({
            'event': event,
            'invite': invite,
        })

    context = {
        'hosted_events_data':         hosted_events_data,
        'attending_events_data':      attending_events_data,
        'pending_invite_events_data': pending_invite_events_data,
    }
    return render(request, 'ETA/my_events.html', context)


#---------------------------------------------------------Profile and logout--------------------------------------------------#
@login_required
def profile(request):
    return render(request, 'ETA/profile.html')

def logout_view(request):
    logout(request)
    return redirect('home')

#---------------------------------------------------------Event detail--------------------------------------------------#
def event_detail(request, event_id):
    user = request.user

    if not user.is_authenticated:
        messages.warning(request, "You have to log in to use this feature.")
        return redirect('login')
    
    event = get_object_or_404(Event, id=event_id)

    #-------------------------- RSVP Counts ---------------------------#
    event.total_going   = event.going_count
    event.friends_going = (
        event.friends_going_count(user)
        if user.is_authenticated
        else 0
    )
    #-------------------------- Attendance -----------------------------#
    attendance = Attendance.objects.filter(user=user, event=event).first()
    #----------------------- Current Friends --------------------------#
    current_friends = user.profile.friends.all()
    #------------------------- Invited IDs ----------------------------#
    invited_ids = list(
        EventInvite.objects
                   .filter(event=event, from_user=user)
                   .values_list('to_user', flat=True)
    )

    #----------- Friends Going vs Inviteable Friends -----------------#
    friends_list_going   = []
    inviteable_friends   = []
    for friend in current_friends:
        if friend.user == user:
            continue
        if Attendance.objects.filter(
            user=friend.user,
            event=event,
            status='going'
        ).exists():
            friends_list_going.append(friend)
        else:
            inviteable_friends.append(friend)

    #------------------------ Render Context -------------------------#
    context = {
        'event':              event,
        'attendance':         attendance,
        'invited_ids':        invited_ids,
        'friends_list_going': friends_list_going,
        'inviteable_friends': inviteable_friends,
    }
    return render(request, 'ETA/event_detail.html', context)
   
#---------------------------------------------------------Edit event--------------------------------------------------#
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

#---------------------------------------------------------Friend related--------------------------------------------------#
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


#-----------------------------Send Friend request----------------------#
from .models import FriendRequest
@login_required
def send_friend_request(request, to_user_id):
    to_user = get_object_or_404(User, id=to_user_id)
    if to_user != request.user:
        fr, created = FriendRequest.objects.get_or_create(from_user=request.user, to_user=to_user)
        if created:
            messages.success(request, "Friendrequest sent successfully.")
        else:
            messages.warning(request, "You have already sent a friend request to this user.")
    return redirect('friend_page')

#-----------------------------Accept Friend request----------------------#
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

#-----------------------------Decline Friend request----------------------#
@login_required
def decline_friend_request(request, request_id):
    friend_request = get_object_or_404(FriendRequest, id=request_id)
    # Ensure the current user is the recipient
    if friend_request.to_user == request.user:
        friend_request.delete()
    return redirect('friend_page')


#-----------------------------Attendance----------------------#
@require_POST
@login_required
def update_attendance(request):
    event_id = request.POST.get("event_id")
    status = request.POST.get("status")
    event = get_object_or_404(Event, id=event_id)

    attendance, created = Attendance.objects.get_or_create(user=request.user, event=event)
    attendance.status = status
    attendance.save()

    return redirect('event_detail', event_id=event.id)

 #-----------------------------Manage account----------------------#

@login_required
def manage_account(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)

    form = ProfileUpdateForm(
        request.POST or None,
        request.FILES or None,
        instance=profile
    )

    password_form = PasswordChangeForm(user=request.user, data=request.POST or None)

    if request.method == 'POST':
        action = request.POST.get("action")

        if 'image-clear' in request.POST:
            profile.image.delete(save=False)
            profile.image = None

        if action == "update_profile" and form.is_valid():
            form.save()
            messages.success(request, "Your profile was updated")
            return redirect('manage_account')

        elif action == "update_password" and password_form.is_valid():
            password_form.save()
            update_session_auth_hash(request, password_form.user)
            messages.success(request, "Your password was updated")
            return redirect('manage_account')

        else:
            for field, errs in form.errors.items():
                for e in errs:
                    messages.error(request, f"{field}: {e}")
            for field, errs in password_form.errors.items():
                for e in errs:
                    messages.error(request, f"{field}: {e}")

    return render(request, 'ETA/manage_account.html', {
        'form': form,
        'password_form': password_form,
    })



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

    # Always notify if it's a private event, even if invite already exists
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


#---------------------------------------------------------Profilepage--------------------------------------------------#
@login_required
def profilepage(request, username):
    profile_user = get_object_or_404(User, username=username)
    hosted_events = Event.objects.filter(host=profile_user)

    for event in hosted_events:
        event.total_going = event.going_count
        event.friends_going = (
            event.friends_going_count(request.user)
            if request.user.is_authenticated
            else 0
        )
    

    context = {
        'profile_user': profile_user,
        'hosted_events': hosted_events
    }
    return render(request, 'ETA/profilepage.html', context)
