from django.contrib import admin
from .models import Appointment, BlockedSlot


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('patient_name', 'specialty', 'doctor', 'date', 'time', 'status')
    list_filter = ('specialty', 'doctor', 'status', 'date')
    search_fields = ('patient_name', 'phone', 'email')


@admin.register(BlockedSlot)
class BlockedSlotAdmin(admin.ModelAdmin):
    list_display = ('doctor', 'date', 'time', 'reason')
    list_filter = ('doctor', 'date')
    search_fields = ('doctor__name', 'reason')
