from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.base_user import BaseUserManager
from django.dispatch import receiver
from django.conf import settings
import stripe
stripe.api_key = settings.STRIPE_SECRET_API_KEY


# Create your models here.
class CustomUserManager(BaseUserManager):

    def create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError('The email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user
    
    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        return self.create_user(email, password, **extra_fields)

class User(AbstractUser):
    USERNAME_FIELD = 'email'    
    REQUIRED_FIELDS = ['first_name']
    username = None
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15, null=True, blank=True)
    stripe_id = models.CharField(max_length=100, blank=True, default='')
    objects = CustomUserManager()
    


@receiver(models.signals.post_save, sender=User, dispatch_uid='create_stripe_customer')
def create_stripe_customer(sender, instance, created, **kwargs):
    if created:
        try:
            name = f'{instance.first_name} {instance.last_name}'
            phone = instance.phone_number
            stripe_customer = stripe.Customer.create(name=name, email=instance.email, phone=phone)
            instance.stripe_id = stripe_customer.id
            instance.save()
        except stripe.error.StripeError as e:
            print("Stripe Error:", str(e))