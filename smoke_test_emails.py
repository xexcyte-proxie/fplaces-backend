import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from notifications.services.mail import send_template_email
from django.conf import settings

TARGET_EMAIL = "fplaces26@gmail.com"

templates_to_test = [
    {
        "template_name": "admin_notification.html", 
        "subject": "Smoke Test: Admin Notification",
        "text": "This is a test notification from the admin system.",
        "context": {"message": "This is a test notification from the admin system."}
    },
    {
        "template_name": "password_reset.html", 
        "subject": "Smoke Test: Password Reset",
        "text": "Please reset your password using the link.",
        "context": {"reset_url": "http://localhost/reset", "user_display_name": "Sunday Ajayi"}
    },
    {
        "template_name": "verify_email.html", 
        "subject": "Smoke Test: Verify Email",
        "text": "Your OTP is 123456.",
        "context": {"otp_code": "123456"}
    },
    {
        "template_name": "welcome.html", 
        "subject": "Smoke Test: Welcome to fplaces!",
        "text": "Welcome to fplaces, Sunday Ajayi!",
        "context": {"user_display_name": "Sunday Ajayi"}
    },
]

print(f"Sending email templates smoke test to {TARGET_EMAIL}...\n")
success = True

for test_data in templates_to_test:
    try:
        response = send_template_email(
            to=TARGET_EMAIL,
            subject=test_data["subject"],
            template_name=test_data["template_name"],
            context=test_data["context"],
            text=test_data["text"]
        )
        print(f"✅ {test_data['template_name']} sent successfully.")
    except Exception as e:
        print(f"❌ {test_data['template_name']} failed to send: {e}")
        success = False

print("\nSmoke test finished.")
if not success:
    exit(1)
