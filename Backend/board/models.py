from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class Notice(models.Model):
    title = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    attachment = models.FileField(upload_to='attachments/', null=True, blank=True)
    external_link = models.URLField(max_length=500, blank=True, null=True)

    def __str__(self):
        return self.title


class Feedback(models.Model):
    name = models.CharField(max_length=100, blank=True)  # Optional name
    message = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name if self.name else "Anonymous"
    
from django.conf import settings

class NotificationPreference(models.Model):
    CATEGORY_CHOICES = [
        ("ALL", "All Notices"),
        ("PLACEMENT", "Placement"),
        ("DEPARTMENT_MCA", "Department of Computer Applications"),
        ("DEPARTMENT_ECE", "Department of Electronics"),
        # you can add more departments later
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    via_email = models.BooleanField(default=False)
    via_sms = models.BooleanField(default=False)
    via_whatsapp = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - {self.category}"


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=15, blank=True, null=True)

    def __str__(self):
        return self.user.username

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    else:
        # Only save if profile exists, otherwise create it
        if hasattr(instance, 'profile'):
            instance.profile.save()
        else:
            Profile.objects.create(user=instance)