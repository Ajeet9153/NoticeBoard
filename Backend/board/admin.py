from django.contrib import admin
from .models import Notice, Feedback, NotificationPreference

@admin.register(Notice)
class NoticeAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_at', 'is_active')
    search_fields = ('title', 'message')
    list_filter = ('is_active', 'created_at')

@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('name', 'message', 'submitted_at')
    search_fields = ('name', 'message')
    list_filter = ('submitted_at',)

@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = ('user', 'category', 'via_email', 'via_sms', 'via_whatsapp')
    list_filter = ('category', 'via_email', 'via_sms', 'via_whatsapp')
    search_fields = ('user__username',)