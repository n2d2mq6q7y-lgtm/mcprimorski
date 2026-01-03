from django import forms
from datetime import datetime, timedelta

from .models import Appointment, BlockedSlot
from doctors.models import AppointmentWindow


class AppointmentForm(forms.ModelForm):
    # Honeypot: real humans won't fill this
    website = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                "autocomplete": "off",
                "tabindex": "-1",
                "style": "display:none",
            }
        ),
    )

    class Meta:
        model = Appointment
        fields = [
            'specialty',
            'doctor',
            'patient_name',
            'phone',
            'email',
            'date',
            'time',
            'reason'
        ]
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'placeholder': 'дд.мм.гггг'}),
            'time': forms.TimeInput(attrs={'type': 'time', 'placeholder': '--:--'}),
        }
        labels = {
            'specialty': 'Специалност',
            'doctor': 'Лекар',
            'patient_name': 'Име на пациент',
            'phone': 'Телефон',
            'email': 'Имейл',
            'date': 'Дата',
            'time': 'Час',
            'reason': 'Причина',
        }

    def clean(self):
        cleaned = super().clean()

        # Honeypot check
        if cleaned.get("website"):
            raise forms.ValidationError("Spam detected.")

        specialty = cleaned.get('specialty')
        doctor = cleaned.get('doctor')
        date = cleaned.get('date')
        time_val = cleaned.get('time')

        # If any are missing, let Django field validators handle it
        if not specialty or not doctor or not date or not time_val:
            return cleaned

        # 1) Doctor must belong to specialty
        if not doctor.specialties.filter(id=specialty.id).exists():
            raise forms.ValidationError("Selected doctor does not belong to the chosen specialty.")

        # 2) Time must be inside an OPEN window for that doctor & date
        windows = AppointmentWindow.objects.filter(
            doctor=doctor,
            date=date,
            is_open=True
        )

        if not windows.exists():
            raise forms.ValidationError("No appointment times are available for this doctor on this date.")

        # Normalize time (sometimes it can arrive as a string "HH:MM")
        if isinstance(time_val, str):
            try:
                time_val = datetime.strptime(time_val, "%H:%M").time()
                cleaned['time'] = time_val
            except ValueError:
                raise forms.ValidationError("Invalid time format.")

        # Check if time fits ANY window
        ok = False
        for w in windows:
            # must be within bounds
            if not (w.start_time <= time_val < w.end_time):
                continue

            # must match slot grid: (time - start) is multiple of slot_minutes
            start_dt = datetime.combine(date, w.start_time)
            chosen_dt = datetime.combine(date, time_val)
            diff_minutes = int((chosen_dt - start_dt).total_seconds() // 60)

            if diff_minutes < 0:
                continue

            if diff_minutes % w.slot_minutes != 0:
                continue

            # also ensure chosen slot doesn't run past end_time
            slot_end = chosen_dt + timedelta(minutes=w.slot_minutes)
            end_dt = datetime.combine(date, w.end_time)
            if slot_end > end_dt:
                continue

            ok = True
            break

        if not ok:
            raise forms.ValidationError("Selected time is not available (outside opened windows).")

        # 3) Prevent double booking (new + confirmed)
        taken = Appointment.objects.filter(
            doctor=doctor,
            date=date,
            time=time_val
        ).exclude(status='cancelled').exists()

        if taken:
            raise forms.ValidationError("This time slot is already taken. Please choose another time.")

        # 4) Respect blocked slots
        if BlockedSlot.objects.filter(doctor=doctor, date=date, time=time_val).exists():
            raise forms.ValidationError("This time is not available. Please choose another slot.")

        return cleaned

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Bulgarian empty labels for selects
        if 'specialty' in self.fields:
            self.fields['specialty'].empty_label = '---------'
        if 'doctor' in self.fields:
            self.fields['doctor'].empty_label = '---------'
