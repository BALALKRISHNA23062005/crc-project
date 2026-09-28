import qrcode
import razorpay
from io import BytesIO

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404

from members.models import Member
from .models import Event, Registration, Attendance, Payment


def event_list(request):
    events = Event.objects.all()
    event_data = []
    for event in events:
        registered_count = Registration.objects.filter(event=event).count()
        spots_left = event.max_participants - registered_count
        event_data.append({'event': event, 'spots_left': spots_left})
    return render(request, 'events/event_list.html', {'event_data': event_data})


@login_required(login_url='/members/login/')
def register_for_event(request):
    member = Member.objects.filter(user=request.user).first()
    if member is None:
        return HttpResponse(
            "This account has no member profile. Please sign up with a member account to register.",
            status=403,
        )
    if request.method == 'POST':
        event = get_object_or_404(Event, id=request.POST.get('event'))
        registration = Registration.objects.create(member=member, event=event)
        return redirect('registration_success', registration_id=registration.id)
    events = Event.objects.all()
    return render(request, 'events/register.html', {'events': events})


@login_required(login_url='/members/login/')
def registration_success(request, registration_id):
    registration = get_object_or_404(Registration, id=registration_id, member__user=request.user)
    return render(request, 'events/registration_success.html', {'registration': registration})


@login_required(login_url='/members/login/')
def qr_code_image(request, registration_id):
    registration = get_object_or_404(Registration, id=registration_id, member__user=request.user)
    checkin_url = request.build_absolute_uri(f'/events/checkin/{registration.qr_code}/')
    qr = qrcode.make(checkin_url)
    buffer = BytesIO()
    qr.save(buffer, format='PNG')
    return HttpResponse(buffer.getvalue(), content_type='image/png')


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
        'already_checked_in': already_checked_in,
    })


@login_required(login_url='/members/login/')
def initiate_payment(request, registration_id):
    registration = get_object_or_404(Registration, id=registration_id, member__user=request.user)
    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
    amount_in_paise = 10000
    order = client.order.create({
        'amount': amount_in_paise,
        'currency': 'INR',
        'payment_capture': 1,
    })
    registration.razorpay_order_id = order['id']
    registration.save()
    return render(request, 'events/payment.html', {
        'registration': registration,
        'order_id': order['id'],
        'amount': amount_in_paise,
        'razorpay_key': settings.RAZORPAY_KEY_ID,
    })


@login_required(login_url='/members/login/')
def register_for_event(request):
    member = Member.objects.filter(user=request.user).first()
    if member is None:
        return HttpResponse(
            "This account has no member profile. Please sign up with a member account to register.",
            status=403,
        )
    error = None
    if request.method == 'POST':
        event = get_object_or_404(Event, id=request.POST.get('event'))
        if Registration.objects.filter(member=member, event=event).exists():
            error = "You're already registered for this event."
        elif Registration.objects.filter(event=event).count() >= event.max_participants:
            error = "Sorry, this event is full."
        else:
            registration = Registration.objects.create(member=member, event=event)
            return redirect('registration_success', registration_id=registration.id)
    events = Event.objects.all()
    return render(request, 'events/register.html', {'events': events, 'error': error})