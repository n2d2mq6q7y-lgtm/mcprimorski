from datetime import datetime, timedelta, date
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.conf import settings
from django.core.mail import send_mail
from django.templatetags.static import static
from django.core.cache import cache
from .forms import AppointmentForm
from doctors.models import Doctor, AppointmentWindow
from .models import Appointment, BlockedSlot


def book_appointment(request):
    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        ip = _get_ip(request)
        key = f"appt_rl:{ip}"
        count = cache.get(key, 0)

        if count >= 10:
            form.add_error(None, "Too many requests. Please wait a few minutes and try again.")
            return render(request, 'appointments/book.html', {'form': form})

        cache.set(key, count + 1, timeout=600)
        if form.is_valid():
            appointment = form.save()

            logo_url = request.build_absolute_uri(static('core/logo.png'))

            patient_subject = "Заявка за преглед – МЦ Приморски"
            patient_message = (
                f"Здравейте, {appointment.patient_name},\n\n"
                f"Получихме Вашата заявка за преглед в МЦ Приморски.\n"
                f"⚠️ Това НЕ е потвърждение на час. Екипът ни ще се свърже с Вас за потвърждение.\n\n"
                f"Детайли на заявката:\n"
                f"- Специалност: {appointment.specialty}\n"
                f"- Лекар: {appointment.doctor.name}\n"
                f"- Дата: {appointment.date}\n"
                f"- Час: {appointment.time}\n"
                f"- Телефон: {appointment.phone}\n"
                f"- Email: {appointment.email}\n"
                f"- Причина: {appointment.reason}\n\n"
                f"Благодарим Ви,\n"
                f"МЦ Приморски"
            )
            patient_html = f"""
            <div style="font-family:Arial, sans-serif; color:#0f172a;">
                <img src="{logo_url}" alt="МЦ Приморски" style="height:80px; display:block; margin-bottom:16px;">
                <p>Здравейте, {appointment.patient_name},</p>
                <p>Получихме Вашата заявка за преглед в МЦ Приморски.</p>
                <p><strong>⚠️ Това НЕ е потвърждение на час.</strong> Екипът ни ще се свърже с Вас за потвърждение.</p>
                <p><strong>Детайли на заявката:</strong></p>
                <ul>
                    <li>Специалност: {appointment.specialty}</li>
                    <li>Лекар: {appointment.doctor.name}</li>
                    <li>Дата: {appointment.date}</li>
                    <li>Час: {appointment.time}</li>
                    <li>Телефон: {appointment.phone}</li>
                    <li>Email: {appointment.email}</li>
                    <li>Причина: {appointment.reason}</li>
                </ul>
                <p>Благодарим Ви,<br>МЦ Приморски</p>
            </div>
            """

            send_mail(
                subject=patient_subject,
                message=patient_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[appointment.email],
                fail_silently=False,
                html_message=patient_html,
            )

            clinic_subject = f"Нова заявка за час – {appointment.date} {appointment.time}"
            clinic_message = (
                f"Нова заявка за преглед:\n\n"
                f"Пациент: {appointment.patient_name}\n"
                f"Телефон: {appointment.phone}\n"
                f"Email: {appointment.email}\n"
                f"Специалност: {appointment.specialty}\n"
                f"Лекар: {appointment.doctor.name}\n"
                f"Дата/час: {appointment.date} {appointment.time}\n"
                f"Причина: {appointment.reason}\n\n"
                f"Статус в системата: {appointment.status}\n"
            )
            clinic_html = f"""
            <div style="font-family:Arial, sans-serif; color:#0f172a;">
                <img src="{logo_url}" alt="МЦ Приморски" style="height:80px; display:block; margin-bottom:16px;">
                <p><strong>Нова заявка за преглед:</strong></p>
                <ul>
                    <li>Пациент: {appointment.patient_name}</li>
                    <li>Телефон: {appointment.phone}</li>
                    <li>Email: {appointment.email}</li>
                    <li>Специалност: {appointment.specialty}</li>
                    <li>Лекар: {appointment.doctor.name}</li>
                    <li>Дата/час: {appointment.date} {appointment.time}</li>
                    <li>Причина: {appointment.reason}</li>
                    <li>Статус в системата: {appointment.status}</li>
                </ul>
            </div>
            """

            clinic_recipient = getattr(settings, "CLINIC_APPOINTMENTS_EMAIL", "")
            if clinic_recipient:
                send_mail(
                    subject=clinic_subject,
                    message=clinic_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[clinic_recipient],
                    fail_silently=False,
                    html_message=clinic_html,
                )

            return redirect('appointment_success')
    else:
        specialty_id = request.GET.get('specialty')
        if specialty_id:
            form = AppointmentForm(initial={'specialty': specialty_id})
        else:
            form = AppointmentForm()

    return render(request, 'appointments/book.html', {'form': form})


def appointment_success(request):
    return render(request, 'appointments/success.html')


def load_doctors(request):
    specialty_id = request.GET.get('specialty')
    doctors = Doctor.objects.filter(specialties__id=specialty_id)

    data = []
    for doctor in doctors:
        data.append({
            'id': doctor.id,
            'name': doctor.name
        })

    return JsonResponse(data, safe=False)


def load_available_times(request):
    doctor_id = request.GET.get('doctor')
    date_str = request.GET.get('date')

    if not doctor_id or not date_str:
        return JsonResponse([], safe=False)

    date = datetime.strptime(date_str, "%Y-%m-%d").date()

    windows = AppointmentWindow.objects.filter(
        doctor_id=doctor_id,
        date=date,
        is_open=True
    )

    taken = set(
        Appointment.objects.filter(
            doctor_id=doctor_id,
            date=date
        ).exclude(status='cancelled').values_list('time', flat=True)
    )
    blocked = set(
        BlockedSlot.objects.filter(
            doctor_id=doctor_id,
            date=date
        ).values_list('time', flat=True)
    )

    slots = []

    for w in windows:
        start = datetime.combine(date, w.start_time)
        end = datetime.combine(date, w.end_time)
        step = timedelta(minutes=w.slot_minutes)

        while start + step <= end:
            t = start.time()
            if t not in taken and t not in blocked:
                slots.append(t.strftime("%H:%M"))
            start += step

    return JsonResponse(slots, safe=False)


def _is_staff(user):
    return user.is_authenticated and user.is_staff


def _get_ip(request):
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "unknown")


@login_required
@user_passes_test(_is_staff)
def block_slot(request):
    if request.method != "POST":
        return HttpResponseForbidden("POST only")

    doctor_id = request.POST.get("doctor_id")
    date_str = request.POST.get("date")
    time_str = request.POST.get("time")
    next_url = request.POST.get("next", "/staff/calendar/")

    try:
        d = datetime.strptime(date_str, "%Y-%m-%d").date()
        t = datetime.strptime(time_str, "%H:%M").time()
    except ValueError:
        messages.error(request, "Invalid date/time.")
        return redirect(next_url)

    BlockedSlot.objects.get_or_create(
        doctor_id=doctor_id,
        date=d,
        time=t,
        defaults={"reason": "Blocked by staff"}
    )
    messages.success(request, f"Blocked {date_str} {time_str}.")
    return redirect(next_url)


@login_required
@user_passes_test(_is_staff)
def unblock_slot(request):
    if request.method != "POST":
        return HttpResponseForbidden("POST only")

    doctor_id = request.POST.get("doctor_id")
    date_str = request.POST.get("date")
    time_str = request.POST.get("time")
    next_url = request.POST.get("next", "/staff/calendar/")

    try:
        d = datetime.strptime(date_str, "%Y-%m-%d").date()
        t = datetime.strptime(time_str, "%H:%M").time()
    except ValueError:
        messages.error(request, "Invalid date/time.")
        return redirect(next_url)

    BlockedSlot.objects.filter(doctor_id=doctor_id, date=d, time=t).delete()
    messages.success(request, f"Unblocked {date_str} {time_str}.")
    return redirect(next_url)


@login_required
@user_passes_test(_is_staff)
def staff_calendar(request):
    doctors = Doctor.objects.all().order_by('name')
    doctor_id = request.GET.get('doctor')

    doctor = None
    if doctor_id:
        doctor = doctors.filter(id=doctor_id).first()
    if doctor is None:
        doctor = doctors.first()

    week_str = request.GET.get('week')
    if week_str:
        try:
            week_date = datetime.strptime(week_str, "%Y-%m-%d").date()
        except ValueError:
            week_date = date.today()
    else:
        week_date = date.today()

    week_start = week_date - timedelta(days=week_date.weekday())
    week_days = [week_start + timedelta(days=i) for i in range(7)]
    week_end = week_start + timedelta(days=7)

    if doctor is None:
        return render(request, "appointments/staff_calendar.html", {
            "doctors": doctors,
            "doctor": None,
            "week_start": week_start,
            "week_days": week_days,
            "calendar": {},
            "prev_week": (week_start - timedelta(days=7)).isoformat(),
            "next_week": (week_start + timedelta(days=7)).isoformat(),
        })

    windows = AppointmentWindow.objects.filter(
        doctor=doctor,
        date__gte=week_start,
        date__lt=week_end,
        is_open=True
    ).order_by('date', 'start_time')

    appts = Appointment.objects.filter(
        doctor=doctor,
        date__gte=week_start,
        date__lt=week_end
    ).exclude(status='cancelled').order_by('date', 'time')

    appt_map = {(a.date, a.time.strftime("%H:%M")): a for a in appts}
    calendar = {d: [] for d in week_days}

    for w in windows:
        start_dt = datetime.combine(w.date, w.start_time)
        end_dt = datetime.combine(w.date, w.end_time)
        step = timedelta(minutes=w.slot_minutes)

        cur = start_dt
        while cur + step <= end_dt:
            t = cur.time().strftime("%H:%M")
            a = appt_map.get((w.date, t))

            calendar[w.date].append({
                "time": t,
                "appointment": a,
            })

            cur += step

    blocked_qs = BlockedSlot.objects.filter(
        doctor=doctor,
        date__gte=week_start,
        date__lt=week_end
    )
    blocked_set = {(b.date, b.time.strftime("%H:%M")) for b in blocked_qs}

    days = []
    for d in week_days:
        slots = []
        for item in calendar.get(d, []):
            t = item["time"]
            a = item["appointment"]
            is_blocked = (d, t) in blocked_set
            slots.append({
                "time": t,
                "appointment": a,
                "blocked": is_blocked,
            })
        days.append({"date": d, "slots": slots})

    context = {
        "doctors": doctors,
        "doctor": doctor,
        "week_start": week_start,
        "week_days": week_days,
        "calendar": calendar,
        "days": days,
        "prev_week": (week_start - timedelta(days=7)).isoformat(),
        "next_week": (week_start + timedelta(days=7)).isoformat(),
    }
    return render(request, "appointments/staff_calendar.html", context)
