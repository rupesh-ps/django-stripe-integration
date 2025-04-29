from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('create-checkout-session/', views.create_checkout_session, name='create_checkout_session'),
    path('success/', views.payment_success, name='payment_success'),
    path('cancel/', views.payment_cancel, name='payment_cancel'),
]