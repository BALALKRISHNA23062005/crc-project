from django.shortcuts import render, redirect
from .models import Event
from .forms import RegistrationForm

def event_list(request):
    events = Event.objects.all()
    return render(request, 'events/event_list.html', {'events': events})

def register_for_event(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('event_list')
    else:
        form = RegistrationForm()
    return render(request, 'events/register.html', {'form': form})