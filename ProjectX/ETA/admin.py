from django.contrib import admin
from .models import Event
from .models import Profile
from .models import Attendance
from .models import Tag
from .models import TagCategory
from .models import InviteRequest
from .models import EventInvite

admin.site.register(Event)
admin.site.register(Profile)
admin.site.register(Attendance)
admin.site.register(Tag)
admin.site.register(TagCategory)
admin.site.register(InviteRequest)
admin.site.register(EventInvite)

# Register your models here.
