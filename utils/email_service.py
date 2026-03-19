from django.core.mail import EmailMultiAlternatives
from django.conf import settings


def send_shift_email(recipient_email: str, subject: str, text_body: str, html_body: str = None) -> dict:
    """
    Sends an email using Django SMTP settings.
    Returns:
    {"success": True}
    or {"success": False, "error": "..."}
    """
    try:
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[recipient_email],
        )

        if html_body:
            msg.attach_alternative(html_body, "text/html")

        msg.send()
        print(f"[EMAIL] SENT -> {recipient_email} | subject={subject}")
        return {"success": True}

    except Exception as e:
        print(f"[EMAIL][ERROR] FAILED -> {recipient_email} | error={e}")
        return {"success": False, "error": str(e)}