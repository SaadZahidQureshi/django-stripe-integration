from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from .forms import CustomUserCreationForm
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.forms import AuthenticationForm
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
import json
from django.conf import settings

import stripe
stripe.api_key = settings.STRIPE_SECRET_API_KEY


# Create your views here.

def signup(request):
    
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Account created successfully!")
            return redirect("login") 
        else:
            print(form.errors)
            messages.error(request, "Please correct the error below.")

    return render(request, "signup.html")

def login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                auth_login(request, user)
                messages.success(request, f"Welcome back, {username}!")
                return redirect('home')  
            else:
                messages.error(request, "Invalid username or password.")
        else:
            print(form.errors)
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})


@login_required(login_url="/login/")
def home(request):
    
    if request.method == 'GET':
        stripe_customer_id = request.user.stripe_id
        setup_intent = stripe.SetupIntent.create(
            customer=stripe_customer_id,
        )
        context = {
            'client_secret': setup_intent.client_secret,
            'STRIPE_PUBLISHABLE_KEY': settings.STRIPE_PUBLIC_API_KEY,
        }
        return render(request, "home.html", context)

    
    if request.method == "POST":
        payment_method_id = request.POST['payment_method_id']
        stripe_customer_id = request.user.customer.stripe_customer_id
        stripe.PaymentMethod.attach(
            payment_method_id,
            customer=stripe_customer_id,
        )
        stripe.Customer.modify(
            stripe_customer_id,
            invoice_settings={
                'default_payment_method': payment_method_id,
            },
        )
        return redirect('cards')


def cards(request):
    return render (request, "cards-list.html")

def list_payment_methods(request):
   if request.method == 'GET':
        try:
            stripe_customer_id = request.user.stripe_id
            payment_methods = stripe.PaymentMethod.list(
                customer=stripe_customer_id,
                type='card'
            )
            return JsonResponse({'success': True, 'payment_methods': payment_methods.data})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})

@csrf_exempt
def create_payment_intent(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            amount = data.get('amount')
            payment_method_id = data.get('payment_method_id')
            stripe_customer_id = "cus_QcKspvLjzd3dPf"

            # Create a PaymentIntent
            payment_intent = stripe.PaymentIntent.create(
                amount=amount,  # Amount in cents
                currency='usd',
                customer=stripe_customer_id,
                payment_method=payment_method_id,
                off_session=True,
                confirm=True,
            )

            return JsonResponse({'success': True, 'payment_intent': payment_intent})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})


@csrf_exempt
def delete_card(request):
    payment_method_id = request.POST.get('payment_method_id')
    try:
        # Detach the payment method from the customer
        stripe.PaymentMethod.detach(payment_method_id)
        return JsonResponse({'success': True, 'message': 'Card deleted successfully'})
    except stripe.error.StripeError as e:
        return JsonResponse({'success': False, 'message': str(e)})