from twilio.rest import Client
from django.conf import settings

def send_sms(to_number, message):
    try:
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        
        message = client.messages.create(
            body=message,
            from_=settings.TWILIO_PHONE_NUMBER,
            to=to_number
        )
        print(f"SMS sent successfully to {to_number}")
        return True
    except Exception as e:
        print(f"SMS sending failed to {to_number}: {e}")
        return False
    

def send_whatsapp(to_number, message):
    try:
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        
        # Use the Twilio WhatsApp sandbox number
        whatsapp_to = f"whatsapp:{to_number}"
        whatsapp_from = "whatsapp:+14155238886"  # Twilio WhatsApp sandbox number
        
        message = client.messages.create(
            body=message,
            from_=whatsapp_from,
            to=whatsapp_to
        )
        print(f"WhatsApp sent successfully to {to_number}")
        return True
    except Exception as e:
        print(f"WhatsApp sending failed to {to_number}: {e}")
        return False