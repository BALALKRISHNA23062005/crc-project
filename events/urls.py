from django.urls import path
from . import views

urlpatterns = [
    path('', views.event_list, name='event_list'),
    path('my-registrations/', views.my_registrations, name='my_registrations'),
    path('register/', views.register_for_event, name='register_for_event'),
    path('register/success/<int:registration_id>/', views.registration_success, name='registration_success'),
    path('qr/<int:registration_id>/', views.qr_code_image, name='qr_code_image'),
    path('checkin/<str:qr_code>/', views.checkin, name='checkin'),
    path('pay/<int:registration_id>/', views.initiate_payment, name='initiate_payment'),
    path('payment-success/<int:registration_id>/', views.payment_success, name='payment_success'),
]