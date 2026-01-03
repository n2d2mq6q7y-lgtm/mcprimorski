from django.db import models
from doctors.models import Doctor, Specialty


class Appointment(models.Model):
    STATUS_CHOICES = [
        ('new', 'Ново'),
        ('confirmed', 'Потвърдено'),
        ('cancelled', 'Отказано'),
    ]

    specialty = models.ForeignKey(Specialty, on_delete=models.CASCADE, null=True, blank=True)
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    patient_name = models.CharField(max_length=200)
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    date = models.DateField()
    time = models.TimeField()
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.patient_name} – {self.date} – {self.doctor.name}"


class BlockedSlot(models.Model):
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    date = models.DateField()
    time = models.TimeField()
    reason = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('doctor', 'date', 'time')
        ordering = ['-date', 'time']

    def __str__(self):
        return f"{self.doctor.name} — {self.date} {self.time}"
