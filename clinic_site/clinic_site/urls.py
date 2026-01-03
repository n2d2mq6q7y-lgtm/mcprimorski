from django.contrib import admin
from django.urls import path, include
from django.conf.urls.i18n import i18n_patterns
from appointments import views as appointment_views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('staff/calendar/', appointment_views.staff_calendar, name='staff_calendar'),
    path('staff/calendar/block/', appointment_views.block_slot, name='staff_block_slot'),
    path('staff/calendar/unblock/', appointment_views.unblock_slot, name='staff_unblock_slot'),
]

urlpatterns += i18n_patterns(
    path('i18n/', include('django.conf.urls.i18n')),
    path('', include('core.urls')),
    path('appointments/', include('appointments.urls')),
    path('publications/', include('publications.urls')),
)

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
