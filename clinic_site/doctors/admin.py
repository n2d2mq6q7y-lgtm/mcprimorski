from datetime import timedelta

from django.contrib import admin, messages
from django import forms
from django.shortcuts import render, redirect
from django.urls import path

from .models import Doctor, Specialty, AppointmentWindow


@admin.register(Specialty)
class SpecialtyAdmin(admin.ModelAdmin):
    list_display = ('name',)


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ('name',)
    filter_horizontal = ('specialties',)


@admin.register(AppointmentWindow)
class AppointmentWindowAdmin(admin.ModelAdmin):
    change_list_template = "admin/doctors/appointmentwindow/change_list.html"
    list_display = ('doctor', 'date', 'start_time', 'end_time', 'slot_minutes', 'is_open')
    list_filter = ('doctor', 'date', 'is_open')
    search_fields = ('doctor__name',)

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                'bulk-open/',
                self.admin_site.admin_view(self.bulk_open_view),
                name='doctors_appointmentwindow_bulk_open'
            ),
        ]
        return custom + urls

    def bulk_open_view(self, request):
        if request.method == 'POST':
            form = BulkOpenForm(request.POST)
            if form.is_valid():
                doctor = form.cleaned_data['doctor']
                start_date = form.cleaned_data['start_date']
                end_date = form.cleaned_data['end_date']
                weekdays = set(int(x) for x in form.cleaned_data['weekdays'])
                start_time = form.cleaned_data['start_time']
                end_time = form.cleaned_data['end_time']
                slot_minutes = form.cleaned_data['slot_minutes']
                is_open = form.cleaned_data['is_open']

                if end_date < start_date:
                    messages.error(request, "End date must be after start date.")
                    return redirect(request.path)

                if end_time <= start_time:
                    messages.error(request, "End time must be after start time.")
                    return redirect(request.path)

                created_count = 0
                day = start_date
                while day <= end_date:
                    if day.weekday() in weekdays:
                        obj, created = AppointmentWindow.objects.get_or_create(
                            doctor=doctor,
                            date=day,
                            start_time=start_time,
                            end_time=end_time,
                            defaults={'slot_minutes': slot_minutes, 'is_open': is_open}
                        )
                        if not created:
                            obj.slot_minutes = slot_minutes
                            obj.is_open = is_open
                            obj.save()
                        else:
                            created_count += 1
                    day += timedelta(days=1)

                messages.success(request, f"Bulk opening complete. Created {created_count} new windows.")
                return redirect('/admin/doctors/appointmentwindow/')

        else:
            form = BulkOpenForm()

        context = {
            **self.admin_site.each_context(request),
            'form': form,
            'title': 'Bulk Open Appointment Windows',
        }
        return render(request, 'admin/doctors/bulk_open.html', context)


class BulkOpenForm(forms.Form):
    doctor = forms.ModelChoiceField(queryset=Doctor.objects.all())
    start_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    end_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))

    WEEKDAYS = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    ]
    weekdays = forms.MultipleChoiceField(
        choices=WEEKDAYS,
        widget=forms.CheckboxSelectMultiple
    )

    start_time = forms.TimeField(widget=forms.TimeInput(attrs={'type': 'time'}))
    end_time = forms.TimeField(widget=forms.TimeInput(attrs={'type': 'time'}))
    slot_minutes = forms.IntegerField(min_value=5, max_value=120, initial=30)
    is_open = forms.BooleanField(initial=True, required=False)
