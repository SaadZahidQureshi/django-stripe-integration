from django.urls import path
from .views import signup, login, home, cards, list_payment_methods, create_payment_intent, delete_card

urlpatterns = [
    path("", signup, name="signup" ),
    path("login/", login, name="login" ),
    path("home/", home, name="home" ),
    
    # cards
    path("cards/", cards, name="cards" ),
    path("payment-methods/", list_payment_methods, name="list_payment_methods" ),
    path("create-payment-intent/", create_payment_intent, name="create_payment_intent" ),
    path("delete-card/", delete_card, name="delete_card" ),
]
