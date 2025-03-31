from django.contrib import admin
from .models import Event
from .models import Profile
from .models import Attendance

admin.site.register(Event)
admin.site.register(Profile)
admin.site.register(Attendance)

# Register your models here.
