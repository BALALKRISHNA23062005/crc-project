from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Event, Registration
from members.models import Member
from .models import Event, Registration, Attendance, Payment   
from django.shortcuts import render, redirect, get_object_or_404 
from django.http import HttpResponse, HttpResponseForbidden
from django.contrib.auth.decorators import login_required

def event_list(request):
    events = Event.objects.all()
    return render(request, 'events/event_list.html', {'events': events})

@login_required(login_url='/members/login/')
def checkin(request, qr_code):
    if not request.user.is_staff:
        return HttpResponseForbidden("Only organizers can check members in.")
    registration = get_object_or_404(Registration, qr_code=qr_code)
    already_checked_in = Attendance.objects.filter(registration=registration).exists()
    if not already_checked_in:
        Attendance.objects.create(registration=registration)
    return render(request, 'events/checkin_result.html', {
        'registration': registration,
        'already_checked_in': already_checked_in
    })

def registration_success(request, registration_id):
    registration = Registration.objects.get(id=registration_id)
    return render(request, 'events/registration_success.html', {'registration': registration})

import qrcode
from io import BytesIO
from django.http import HttpResponse
from .models import Event, Registration

def qr_code_image(request, registration_id):
    registration = Registration.objects.get(id=registration_id)
    checkin_url = request.build_absolute_uri(f'/events/checkin/{registration.qr_code}/')
    qr = qrcode.make(checkin_url)
    buffer = BytesIO()
    qr.save(buffer, format='PNG')
    return HttpResponse(buffer.getvalue(), content_type='image/png')

from django.utils import timezone
from .models import Event, Registration, Attendance

def checkin(request, qr_code):
    registration = Registration.objects.get(qr_code=qr_code)
    already_checked_in = Attendance.objects.filter(registration=registration).exists()
    if not already_checked_in:
        Attendance.objects.create(registration=registration)
    return render(request, 'events/checkin_result.html', {
        'registration': registration,
        'already_checked_in': already_checked_in
    })

import razorpay
from django.conf import settings

def initiate_payment(request, registration_id):
    registration = Registration.objects.get(id=registration_id)
    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

    amount_in_paise = 10000  # ₹100.00 — Razorpay uses paise, so multiply rupees by 100
    order = client.order.create({
        'amount': amount_in_paise,
        'currency': 'INR',
        'payment_capture': 1
    })

    registration.razorpay_order_id = order['id']
    registration.save()

    return render(request, 'events/payment.html', {
        'registration': registration,
        'order_id': order['id'],
        'amount': amount_in_paise,
        'razorpay_key': settings.RAZORPAY_KEY_ID,
    })

def payment_success(request, registration_id):
    registration = Registration.objects.get(id=registration_id)
    payment_id = request.GET.get('razorpay_payment_id', '')
    order_id = request.GET.get('razorpay_order_id', '')
    signature = request.GET.get('razorpay_signature', '')

    if not order_id or order_id != registration.razorpay_order_id:
        return HttpResponse("Invalid payment.", status=400)

    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
    try:
        client.utility.verify_payment_signature({
            'razorpay_order_id': order_id,
            'razorpay_payment_id': payment_id,
            'razorpay_signature': signature,
        })
    except razorpay.errors.SignatureVerificationError:
        return HttpResponse("Payment verification failed.", status=400)

    if registration.payment_status != 'paid':
        Payment.objects.create(
            registration=registration,
            amount=100.00,
            transaction_id=payment_id
        )
        registration.payment_status = 'paid'
        registration.save()

    return render(request, 'events/payment_success.html', {'registration': registration})

def event_list(request):
    events = Event.objects.all()
    event_data = []
    for event in events:
        registered_count = Registration.objects.filter(event=event).count()
        spots_left = event.max_participants - registered_count
        event_data.append({
            'event': event,
            'spots_left': spots_left
        })
    return render(request, 'events/event_list.html', {'event_data': event_data})

