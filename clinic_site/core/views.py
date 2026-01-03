from django.shortcuts import render
from doctors.models import Doctor, Specialty


def home(request):
    return render(request, 'core/home.html')


def about(request):
    doctors = Doctor.objects.all()
    return render(request, 'core/about.html', {'doctors': doctors})


def services(request):
    return render(request, 'core/services.html')


def online_consultations(request):
    return render(request, 'core/online.html')


def contacts(request):
    return render(request, 'core/contacts.html')


def specialties_list(request):
    specialties = Specialty.objects.all()
    return render(request, 'core/specialties.html', {'specialties': specialties})


def specialty_detail(request, pk):
    specialty = Specialty.objects.get(pk=pk)
    doctors = specialty.doctor_set.all()
    return render(
        request,
        'core/specialty_detail.html',
        {'specialty': specialty, 'doctors': doctors}
    )
