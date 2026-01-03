from django.db import models


class SiteSettings(models.Model):
    site_name = models.CharField(max_length=200, default="МЦ Приморски")

    logo = models.ImageField(upload_to="site/", blank=True)
    logo_width = models.PositiveIntegerField(default=140, help_text="Logo width in pixels")
    primary_color = models.CharField(
        max_length=20,
        default="#0a6ebd",
        help_text="Main theme color (HEX)"
    )

    header_height = models.PositiveIntegerField(default=80)
    sticky_header = models.BooleanField(default=True)

    show_hero = models.BooleanField(default=True)
    show_doctors = models.BooleanField(default=True)
    show_publications = models.BooleanField(default=True)
    show_booking_cta = models.BooleanField(default=True)

    homepage_intro = models.TextField(
        default="Съвременна медицина с грижа за пациента."
    )

    clinic_phone = models.CharField(max_length=50, blank=True)
    clinic_email = models.EmailField(blank=True)
    footer_text = models.TextField(
        default="© Медицински център Приморски"
    )

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def __str__(self):
        return "Site Settings"

    class Meta:
        verbose_name = "Site Settings"
        verbose_name_plural = "Site Settings"
