from django.contrib import admin
from .models import Event
from .models import Profile
from .models import Attendance
from .models import Tag
from .models import TagCategory

admin.site.register(Event)
admin.site.register(Profile)
admin.site.register(Attendance)
admin.site.register(Tag)
admin.site.register(TagCategory)

# Register your models here.
