from django.db import models
from django.conf import settings
#----------------------#
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from django.utils import timezone
from datetime import timedelta

User = get_user_model()

# Create your models here.

#--------------Helper for event to see if an event is past its end date or not----
class EventQuerySet(models.QuerySet):
    def upcomingEvent(self):
        return self.filter(end_date__gte=timezone.now())

    def pastEvent(self):
        return self.filter(end_date__lt=timezone.now())
    
#-------------------------------------------Event Model-----------------------------------------------
class Event(models.Model):
    title = models.CharField(max_length=200, help_text ="Enter a title")
    description = models.TextField(blank=True)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    is_public = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    host = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    image = models.ImageField(upload_to='event_images/', null=True, blank=True)
    location = models.CharField(max_length=255, blank=True, help_text="Enter a street address or place name")
    objects = EventQuerySet.as_manager()

#----Small logic that makes sure the start date is before the end date
    def clean(self):
        super().clean()
        if self.start_date > self.end_date:
            raise ValidationError("Start date cannot be after end date.")
    
#--- callable variable that returns true if end date is before now
    @property
    def is_past(self):
        return self.end_date < timezone.now()

#---Counts attendances---
    @property
    def going_count(self):
        return self.attendance_set.filter(status='going').count()
    
    def friends_going_count(self, user):
        friend_ids = user.profile.friends.values_list('id', flat=True)
        return self.attendance_set.filter(
            status='going',
            user_id__in=friend_ids
        ).count()

    def __str__(self):
        return self.title
    
    #---------------------------Extending the User Model with a Profile--------------------------------#
class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    # Self-referential ManyToManyField for friend relationships.
    friends = models.ManyToManyField("self", blank=True, symmetrical=True)
    bio = models.TextField(blank=True, max_length=250)
    image = models.ImageField(upload_to='profile_images/', null=True, blank=True)

    def __str__(self):
        return self.user.username
    
#---------------------------Friend request model--------------------------------#
class FriendRequest(models.Model):
    from_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='friend_requests_sent')
    to_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='friend_requests_received')
    timestamp = models.DateTimeField(auto_now_add=True)
    class Meta:
        unique_together = ('from_user', 'to_user')

    def __str__(self):
        return f"Friend request from {self.from_user} to {self.to_user}"
    
    
    #-----------------------------------Auto-Creation of Profiles via Signals-----------------------#
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        # Create a Profile for the new user
        Profile.objects.create(user=instance)


#-----------------------------------Attendance buttons-----------------------#
class Attendance(models.Model):
    status_choices = (
        ('going', 'Going'),
        ('can_go', 'Can Go'),
        ('not_going', 'Not Going'),
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    status = models.CharField(max_length=15, choices=status_choices, default='neutral')

    class Meta:
        unique_together = ('user', 'event')
    
    def __str__(self):
        # Display something meaningful, e.g., "carlgrude1 -> Sluttsfjell (Going)"
        return f"{self.user.username} -> {self.event.title} ({self.status})"


#-----------------------------------Event invite----------------------------#
class EventInvite(models.Model):
    event = models.ForeignKey('Event', on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    from_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='event_invite_sent')
    to_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='event_invite_received')
    
    INVITE_STATUS_CHOICES = (
        ('accepted', 'Accepted'),
        ('pending', 'Pending'),
        ('declined', 'Declined'),
    )
    status = models.CharField(max_length=15, choices=INVITE_STATUS_CHOICES, default='pending')
    
    class Meta:
        unique_together = ('event', 'from_user', 'to_user')
    
    def __str__(self):
        return f"Invite from {self.from_user} to {self.to_user} for event {self.event.title}"
    
#---------------------------------------Request friend invitation------------------------------
class InviteRequest(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='invite_requests')
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_invite_requests')
    requested_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_invite_requests')
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('event','requested_by','requested_user')

#-----------------------------------Notifications----------------------------#
class Notification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    message = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    link = models.URLField(blank=True)

    def __str__(self):
        return f"Notification for {self.user.username}: {self.message}"

