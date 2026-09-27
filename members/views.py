from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import login
from .models import Member
from .forms import SignUpForm

def member_list(request):
    members = Member.objects.all()
    return render(request, 'members/member_list.html', {'members': members})

def signup(request):
    error = None
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            if User.objects.filter(username=username).exists():
                error = "That username is already taken. Please choose another."
            else:
                user = User.objects.create_user(
                    username=username,
                    password=form.cleaned_data['password']
                )
                Member.objects.create(
                    user=user,
                    name=form.cleaned_data['name'],
                    email=form.cleaned_data['email'],
                    phone=form.cleaned_data['phone']
                )
                login(request, user)
                return redirect('event_list')
    else:
        form = SignUpForm()
    return render(request, 'members/signup.html', {'form': form, 'error': error})