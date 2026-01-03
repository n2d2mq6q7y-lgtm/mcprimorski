from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class Specialty(models.Model):
    name = models.CharField(max_length=200)

    class Meta:
        verbose_name = "Specialty"
        verbose_name_plural = "Specialties"

    def __str__(self):
        return self.name


class Doctor(models.Model):
    name = models.CharField(max_length=200)
    title = models.CharField(max_length=200)
    specialties = models.ManyToManyField(Specialty)
    photo = models.ImageField(upload_to='doctors/', blank=True)
    bio = models.TextField()
    education = models.TextField()
    qualifications = models.TextField()
    experience = models.TextField()

    def __str__(self):
        return self.name


class AppointmentWindow(models.Model):
    doctor = models.ForeignKey('Doctor', on_delete=models.CASCADE)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    slot_minutes = models.PositiveIntegerField(default=30, validators=[MinValueValidator(5), MaxValueValidator(120)])
    is_open = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Appointment window"
        verbose_name_plural = "Appointment windows"
        ordering = ['-date', 'doctor', 'start_time']

    def __str__(self):
        return f"{self.doctor.name} — {self.date} {self.start_time}-{self.end_time}"
