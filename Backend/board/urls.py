from django.urls import path
from . import views

urlpatterns = [
    # Authentication
    path('register/', views.register_user, name='register_user'),
    path('login/', views.login_user, name='login_user'),
    path('admin-login/', views.admin_login, name='admin_login'),

    # User profile management
    path('api/change-password/', views.change_password, name='change_password'),
    path('api/update-profile/', views.update_profile, name='update_profile'),
    path('api/get-profile/', views.get_profile, name='get_profile'),

    # Notices
    path('notices/', views.get_notices, name='get_notices'),
    path('notices/create/', views.create_notice, name='create_notice'),
    path('notices/<int:id>/', views.get_notice_detail, name='get_notice_detail'),

    # Feedback
    path('feedback/', views.feedback_list_create, name='feedback_list_create'),

    # Notification preferences
    path('notification-preferences/', views.NotificationPreferenceView.as_view(), name='notification_preferences'),

    # Admin: send notices
    path('send-notice/', views.send_notice, name='send_notice'),
]
