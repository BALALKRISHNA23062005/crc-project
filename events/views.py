from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Event, Registration
from members.models import Member

def event_list(request):
    events = Event.objects.all()
    return render(request, 'events/event_list.html', {'events': events})

@login_required(login_url='/members/login/')
def register_for_event(request):
    member = Member.objects.get(user=request.user)
    if request.method == 'POST':
        event_id = request.POST.get('event')
        event = Event.objects.get(id=event_id)
        Registration.objects.create(member=member, event=event)
        return redirect('event_list')
    events = Event.objects.all()
    return render(request, 'events/register.html', {'events': events})