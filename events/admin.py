from django.contrib import admin
from .models import Event, Registration, Attendance, Payment

admin.site.register(Event)
admin.site.register(Registration)
admin.site.register(Attendance)
admin.site.register(Payment)