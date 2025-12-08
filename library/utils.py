# library/utils.py
from django.core.mail import send_mail
from django.conf import settings

def send_verification_email(user, token):
    subject = "Verify your email"
    message = f"Click this link to verify your email: http://127.0.0.1:8000/verify/?token={token}"
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])

import random
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings
from library.models import ResetCode

def send_reset_code(user):
    code = str(random.randint(100000, 999999))
    ResetCode.objects.update_or_create(user=user, defaults={'code': code})
    
    system_name = "Library System"  # Or fetch dynamically
    subject = f"{system_name} - Password Reset Code"
    html_content = render_to_string('emails/reset_code_email.html', {
        'user': user,
        'code': code,
        'system_name': system_name,
    })

    email = EmailMessage(
        subject=subject,
        body=html_content,
        from_email=f"{system_name} <{settings.EMAIL_HOST_USER}>",
        to=[user.email],
    )
    email.content_subtype = "html"
    email.send(fail_silently=False)
    return code
