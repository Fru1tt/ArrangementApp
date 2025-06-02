from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib import messages
from django.http import HttpResponseForbidden  
from .models import Event, FriendRequest, Profile, Attendance, EventInvite, InviteRequest, TagCategory, Tag
from .forms import EventForm, ProfileUpdateForm
from django.contrib.auth import get_user_model
from django.views.decorators.http import require_POST
from django.db.models import Count, Q
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
    events = Event.objects.upcomingEvent().filter(is_public=True).order_by('start_date')
    categories = (TagCategory.objects.annotate(num_tags=Count('tags')).order_by('num_tags', 'name').prefetch_related('tags'))

    #---------------------- Upcoming Events Data with Tag Filter ----------------------#
    selected_tag_ids = request.GET.getlist('tags') #Read selected tag IDs from GET parameters
    try:
        selected_tag_ids = [int(pk) for pk in selected_tag_ids]
    except ValueError:
        selected_tag_ids = []

    filtered_events = events
    if selected_tag_ids:
        filtered_events = filtered_events.filter(tags__id__in=selected_tag_ids).distinct() # Filter by tags

    #----------Date filter-----------#
    filter_date = request.GET.get('filter_date')
    if filter_date:
        filtered_events = filtered_events.filter(
         Q(start_date__date__gte=filter_date)
        |Q(start_date__date__lte=filter_date, end_date__date__gte=filter_date)
    )

    public_events = filtered_events.exclude(host=user) if user.is_authenticated else filtered_events  # Exclude events hosted by the logged-in user


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
            'event': event,
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
    trending_events = trending_events[:10]
    

    #---------------------- Render Context ----------------------#
    context = {
        'events_with_attendance': events_data,
        'trending_events':        trending_events,
        'categories':             categories,
        'selected_tag_ids':       selected_tag_ids,
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
            form.save_m2m()
            return redirect('my_events')
        else:
            for err in form.non_field_errors():
                messages.warning(request, err)
    else:
        form = EventForm()

    categories = (
        TagCategory.objects.annotate(num_tags=Count('tags')).order_by('num_tags', 'name').prefetch_related('tags'))

    return render(request, 'ETA/create_event.html', {
        'form':       form,
        'categories': categories,
    })

#--------------------------------------------------My Events view filter logic--------------------------------------------#
def my_events(request):
    if not request.user.is_authenticated:
        messages.warning(request, "You have to log in to use this feature.")
        return redirect('login')
    
    user = request.user

    # -------------------------------- Hosted Events --------------------------------
    hosted_events = Event.objects.upcomingEvent().filter(host=user).order_by('start_date')
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
        status__in=['going', 'can go'],
        event__in=Event.objects.upcomingEvent()
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
        status='pending',
         event__in=Event.objects.upcomingEvent()
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
       .filter(event=event)
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

    # Compute which inviteable friends already have a pending request from current user
    pending_req_ids = InviteRequest.objects.filter(
        event=event,
        requested_by=user,
        requested_user__in=[f.user for f in inviteable_friends]
    ).values_list('requested_user__id', flat=True)

    # Determine if current user can request invites (only on private events if host or already invited)
    can_request = False
    if not event.is_public and (
        event.host == user or
        EventInvite.objects.filter(event=event, to_user=user).exists()
    ):
        can_request = True

    invite_requests = InviteRequest.objects.filter(event=event, requested_by=user)

    #--------------------Pending invite requests-------------------------#
    if user == event.host:
        # “invite_requests_for_host” will be a QuerySet of InviteRequest objects
        invite_requests_for_host = InviteRequest.objects.filter(event=event)
    else:
        # not the host, so give an empty list
        invite_requests_for_host = InviteRequest.objects.none()

    #------------------------ Render Context -------------------------#
    context = {
        'event':              event,
        'attendance':         attendance,
        'invited_ids':        invited_ids,
        'friends_list_going': friends_list_going,
        'inviteable_friends': inviteable_friends,
        'invite_requests':    invite_requests,
        'pending_req_ids':    set(pending_req_ids),
        'can_request':        can_request,
        'invite_requests_for_host': invite_requests_for_host,
    }
    return render(request, 'ETA/event_detail.html', context)
   
#---------------------------------------------------------Edit event--------------------------------------------------#
@login_required
def event_edit(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    # Only allow the event host to edit
    if request.user != event.host:
        return HttpResponseForbidden("You are not allowed to edit this event.")

    categories = (
        TagCategory.objects
        .annotate(num_tags=Count("tags"))
        .order_by("num_tags", "name")
        .prefetch_related("tags")
    )

    selected_tags = list(event.tags.values_list("id", flat=True))

    if request.method == "POST":
        form = EventForm(request.POST, request.FILES, instance=event)
        if form.is_valid():
            event = form.save(commit=False)
            event.save()

            posted_tag_ids = request.POST.getlist("tags")
            try:
               
                posted_tag_ids = [int(pk) for pk in posted_tag_ids]
            except ValueError:
                posted_tag_ids = []

            event.tags.set(posted_tag_ids)
            return redirect("event_detail", event_id=event.id)
    else:
        form = EventForm(instance=event)

    context = {
        "form":          form,
        "event":         event,
        "categories":    categories,
        "selected_tags": [str(pk) for pk in selected_tags],
    }
    return render(request, "ETA/event_edit.html", context)

#---------------------------------------------------------Friend related--------------------------------------------------#
#-----------------------------Friend Search----------------------#
def friend_page(request):
    if not request.user.is_authenticated:
         messages.warning(request, "You have to log in to use this feature.")
         return redirect('login')

    query = request.GET.get('q', '')
    results = []
    #Check length
    if query and len(query) < 3:
        messages.warning(request, "Please enter at least 3 characters to search.")
    elif len(query) >= 3:
        results = User.objects.filter(
            username__icontains=query
        ).exclude(id=request.user.id)

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
        created = FriendRequest.objects.get_or_create(from_user=request.user, to_user=to_user)
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
        messages.warning(request, "Only hosts can invite to private events.")
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
    return redirect('event_detail', event_id=event.id)

#----------------------Request event invite------------------------#
@login_required
@require_POST
def request_event_invite(request, event_id, friend_id):
    event = get_object_or_404(Event, id=event_id)
    me = request.user
    friend = get_object_or_404(me.profile.friends, id=friend_id).user

    #You must already be invited (or the host)
    if not (event.host == me or EventInvite.objects.filter(event=event, to_user=me).exists()):
        messages.error(request, "Only invited users can request more invites.")
        return redirect('event_detail', event_id)

    #Dont request if friend already invited
    if EventInvite.objects.filter(event=event, to_user=friend).exists():
        messages.info(request, f"{friend.username} is already invited.")
        return redirect('event_detail', event_id)

    #Dont re-request if you already asked
    if InviteRequest.objects.filter(event=event,requested_by=me,requested_user=friend).exists():
        messages.info(request, "You've already requested this invite.")
        return redirect('event_detail', event_id)

    #All is ok, then create request
    InviteRequest.objects.create(
        event=event,
        requested_by=me,
        requested_user=friend
    )
    messages.success(request, f"Invite request for {friend.username} sent to host.")
    return redirect('event_detail', event_id)


#---------------------------Accept / Decline invite request -----------------#
#---------Accept---------#
@login_required
@require_POST
def accept_invite_request(request, event_id, req_id):
    req = get_object_or_404(InviteRequest, id=req_id, event__id=event_id)
    EventInvite.objects.get_or_create(
        event=req.event,
        from_user=request.user,
        to_user=req.requested_user,
        defaults={'status': 'pending'}
    )
    req.delete()
    messages.success(request, f"{req.requested_user.username} has been invited.")
    return redirect('event_detail', event_id=event_id)

#-------Decline------#
@login_required
@require_POST
def decline_invite_request(request, event_id, req_id):
    inv_req = get_object_or_404(
        InviteRequest,
        id=req_id,
        event__id=event_id
    )

    #Not strictly needed since we only have the list pop up for hosts, but creates extra protection in backend
    if request.user != inv_req.event.host:
        messages.error(request, "Only the host can decline invitation requests.")
        return redirect('event_detail', event_id=event_id)

    inv_req.delete()
    messages.success(request, f"Invitation request from {inv_req.requested_by.username} declined.")
    return redirect('event_detail', event_id=event_id)

#---------------------------------------------------------Profilepage--------------------------------------------------#
#---------------------------------------------------------Profilepage--------------------------------------------------#
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.models import User
from .models import Event, Attendance

@login_required
def profilepage(request, username):
    profile_user = get_object_or_404(User, username=username)

    # ---------------------------- Upcoming Events Hosted by Profile User ----------------------------
    hosted_events = Event.objects.upcomingEvent().filter(host=profile_user).order_by('start_date')

    hosted_events_data = []
    for event in hosted_events:
        try:
            attendance = Attendance.objects.get(user=request.user, event=event)
        except Attendance.DoesNotExist:
            attendance = None

        event.total_going = event.going_count
        event.friends_going = event.friends_going_count(request.user)

        hosted_events_data.append({
            'event': event,
            'attendance': attendance,
        })

    # ---------------------------- Past Events Hosted by Profile User ----------------------------
    past_events = Event.objects.pastEvent().filter(host=profile_user).order_by('-end_date')

    past_events_data = []
    for event in past_events:
        try:
            attendance = Attendance.objects.get(user=request.user, event=event)
        except Attendance.DoesNotExist:
            attendance = None

        event.total_going = event.going_count
        event.friends_going = event.friends_going_count(request.user)

        past_events_data.append({
            'event': event,
            'attendance': attendance,
        })

    context = {
        'profile_user': profile_user,
        'hosted_events': hosted_events_data,
        'pastEvent': past_events_data,  # renamed to stay consistent with attendance-based structure
    }

    return render(request, 'ETA/profilepage.html', context)

#------------------Delete-event---------------------------#
@login_required
def delete_event(request, event_id):
    event = get_object_or_404(Event, id=event_id, host=request.user)

    if request.method == 'POST':
        event.delete()
        messages.success(request, "Event deleted successfully.")
        return redirect('my_events')  # Go to list of your events

    messages.error(request, "Invalid request method.")
    return redirect('event_detail', event_id=event.id)  # Not 'event_edit'

@login_required
def remove_friend(request, user_id):
    to_user = get_object_or_404(User, id=user_id)

    if request.method == 'POST':
        if to_user.profile in request.user.profile.friends.all():
            request.user.profile.friends.remove(to_user.profile)
            to_user.profile.friends.remove(request.user.profile)
            messages.success(request, f"{to_user.username} has been removed from your friends.")
        else:
            messages.warning(request, f"{to_user.username} is not your friend.")
    else:
        messages.error(request, "Invalid request method.")

    return redirect('friend_page')



