import stripe
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .models import Order, Payment

stripe.api_key = settings.STRIPE_SECRET_KEY

def index(request):
    return render(request, 'payments/index.html', {
        'stripe_publishable_key': settings.STRIPE_PUBLISHABLE_KEY
    })

def create_checkout_session(request):
    if request.method == 'POST':
        order = Order.objects.create(
            name=request.POST.get('name'),
            email=request.POST.get('email'),
            amount=request.POST.get('amount')
        )
        
        try:
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[
                    {
                        'price_data': {
                            'currency': 'usd',
                            'unit_amount': int(float(order.amount) * 100),
                            'product_data': {
                                'name': f'Order #{order.id}',
                            },
                        },
                        'quantity': 1,
                    },
                ],
                metadata={
                    'order_id': order.id,
                },
                mode='payment',
                success_url=request.build_absolute_uri(reverse('payment_success')) + '?session_id={CHECKOUT_SESSION_ID}',
                cancel_url=request.build_absolute_uri(reverse('payment_cancel')) + f'?order_id={order.id}',
            )
            return redirect(checkout_session.url)
        except Exception as e:
            order.status = Order.OrderStatus.FAILED
            order.save()
            return HttpResponse({'error': str(e)})
    return render(request, 'payments/create_order.html')

def payment_success(request):
    session_id = request.GET.get('session_id')
    if session_id:
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            order_id = session.get('metadata', {}).get('order_id')
            
            if order_id:
                order = get_object_or_404(Order, id=order_id)
                order.status = Order.OrderStatus.PAID
                order.save()
                
                Payment.objects.create(
                    order=order,
                    stripe_payment_id=session.payment_intent,
                    amount=order.amount,
                    status='completed'
                )
                return render(request, 'payments/success.html', {'order': order})
        except Exception as e:
            return HttpResponse({'error': str(e)})
    
    return render(request, 'payments/success.html')

def payment_cancel(request):
    order_id = request.GET.get('order_id')
    print(f"Cancel received with order_id: {order_id}")
    if order_id:
        try:
            order = get_object_or_404(Order, id=order_id)
            order.status = Order.OrderStatus.FAILED
            order.save()
            return render(request, 'payments/cancel.html', {'order': order})
        except Exception as e:
            print(f"Error updating canceled order: {e}")
    
    return render(request, 'payments/cancel.html')
