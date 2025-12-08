# library/utils.py
from django.core.mail import send_mail
from django.conf import settings

def send_verification_email(user, token):
    subject = "Verify your email"
    message = f"Click this link to verify your email: http://127.0.0.1:8000/verify/?token={token}"
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])
