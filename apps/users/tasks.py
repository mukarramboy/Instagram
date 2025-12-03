from celery import shared_task
from django.core.mail import EmailMessage
from django.template.loader import render_to_string


@shared_task
def send_verification_email(email, code):
    html_content = render_to_string('email/activate_account.html', {'code': code})

    email = EmailMessage(
        subject='Your Verification Code',
        body=html_content,
        to=[email],
    )
    email.content_subtype = 'html'
    email.send()

    return True