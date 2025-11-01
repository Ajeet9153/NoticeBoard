from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status, generics, permissions, mixins
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate, get_user_model
from django.core.mail import send_mail

from utils.notification_utils import send_sms
from .models import Notice, Feedback, NotificationPreference
from .serializers import (
    NoticeSerializer,
    FeedbackSerializer,
    RegisterSerializer,
    NotificationPreferenceSerializer
)

User = get_user_model()

# =====================================================
# -------------------- NOTICE APIs --------------------
# =====================================================

@api_view(['GET'])
def get_notices(request):
    """Fetch all active notices."""
    notices = Notice.objects.filter(is_active=True).order_by('-created_at')
    serializer = NoticeSerializer(notices, many=True, context={'request': request})
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_notice(request):
    """Create a new notice."""
    serializer = NoticeSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def get_notice_detail(request, id):
    """Get single notice detail."""
    try:
        notice = Notice.objects.get(pk=id, is_active=True)
    except Notice.DoesNotExist:
        return Response({"detail": "Notice not found."}, status=status.HTTP_404_NOT_FOUND)
    serializer = NoticeSerializer(notice, context={'request': request})
    return Response(serializer.data, status=status.HTTP_200_OK)


# =====================================================
# -------------------- FEEDBACK APIs -------------------
# =====================================================

@api_view(['GET', 'POST'])
def feedback_list_create(request):
    """Submit or view feedbacks."""
    if request.method == 'GET':
        if not request.user.is_authenticated:
            return Response({"detail": "Login required."}, status=status.HTTP_401_UNAUTHORIZED)
        feedbacks = Feedback.objects.all().order_by('-submitted_at')
        serializer = FeedbackSerializer(feedbacks, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    elif request.method == 'POST':
        serializer = FeedbackSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# =====================================================
# -------------------- AUTH APIs -----------------------
# =====================================================

@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    """User Registration API"""
    name = request.data.get("name") or request.data.get("username")
    email = request.data.get("email")
    password = request.data.get("password")

    if not name or not email or not password:
        return Response({"success": False, "message": "All fields are required."}, status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(username=name).exists():
        return Response({"success": False, "message": "Username already exists."}, status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(email=email).exists():
        return Response({"success": False, "message": "Email already exists."}, status=status.HTTP_400_BAD_REQUEST)

    user = User.objects.create_user(username=name, email=email, password=password)
    refresh = RefreshToken.for_user(user)

    return Response({
        "success": True,
        "message": "Registration successful.",
        "access": str(refresh.access_token),
        "refresh": str(refresh),
        "username": user.username,
        "is_admin": user.is_staff or user.is_superuser
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([AllowAny])
def login_user(request):
    """
    Login endpoint for normal users (email + password).
    Admins should use /admin-login/.
    """
    identifier = request.data.get("email")
    password = request.data.get("password")

    if not identifier or not password:
        return Response({"success": False, "message": "Email and password are required."},
                        status=status.HTTP_400_BAD_REQUEST)

    # Try email, then username
    try:
        user_obj = User.objects.get(email=identifier)
        username_for_auth = user_obj.username
    except User.DoesNotExist:
        username_for_auth = identifier

    user = authenticate(username=username_for_auth, password=password)
    if not user:
        return Response({"success": False, "message": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED)

    refresh = RefreshToken.for_user(user)
    return Response({
        "success": True,
        "message": "Login successful.",
        "access": str(refresh.access_token),
        "refresh": str(refresh),
        "username": user.username,
        "is_admin": user.is_staff or user.is_superuser
    }, status=status.HTTP_200_OK)


# =====================================================
# -------------------- PROFILE APIs --------------------
# =====================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_profile(request):
    """Return logged-in user's profile."""
    user = request.user
    return Response({
        "username": user.username,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "is_admin": user.is_staff or user.is_superuser
    }, status=status.HTTP_200_OK)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_profile(request):
    """Update profile details."""
    user = request.user
    username = request.data.get("username")
    email = request.data.get("email")
    first_name = request.data.get("first_name")
    last_name = request.data.get("last_name")

    if username:
        user.username = username
    if email:
        user.email = email
    if first_name:
        user.first_name = first_name
    if last_name:
        user.last_name = last_name

    user.save()
    return Response({"success": True, "message": "Profile updated successfully."}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    """Allow user to change password."""
    user = request.user
    old_password = request.data.get("old_password")
    new_password = request.data.get("new_password")

    if not old_password or not new_password:
        return Response({"success": False, "message": "Both old and new passwords are required."},
                        status=status.HTTP_400_BAD_REQUEST)

    if not user.check_password(old_password):
        return Response({"success": False, "message": "Current password is incorrect."},
                        status=status.HTTP_400_BAD_REQUEST)

    user.set_password(new_password)
    user.save()
    return Response({"success": True, "message": "Password changed successfully."}, status=status.HTTP_200_OK)


# =====================================================
# --------------- NOTIFICATION PREF APIs ---------------
# =====================================================

class NotificationPreferenceView(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    generics.GenericAPIView
):
    serializer_class = NotificationPreferenceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return NotificationPreference.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)


# =====================================================
# -------------------- SEND NOTICE --------------------
# =====================================================

@api_view(['POST'])
@permission_classes([IsAdminUser])
def send_notice(request):
    """Send notice to users with notification preferences."""
    notice_id = request.data.get("notice_id")

    if not notice_id:
        return Response({"error": "notice_id is required"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        notice = Notice.objects.get(id=notice_id, is_active=True)
    except Notice.DoesNotExist:
        return Response({"error": "Notice not found or inactive"}, status=status.HTTP_404_NOT_FOUND)

    preferences = NotificationPreference.objects.filter(category="ALL")
    sent_to = []

    for pref in preferences:
        user = pref.user
        if pref.via_email:
            send_mail(
                subject=notice.title,
                message=notice.message,
                from_email="sem3mini@gmail.com",
                recipient_list=[user.email],
                fail_silently=True,
            )

        if pref.via_sms and hasattr(user, 'profile') and getattr(user.profile, 'phone_number', None):
            send_sms(user.profile.phone_number, f"{notice.title}: {notice.message}")

        if pref.via_whatsapp:
            print(f"WhatsApp notification for {user.username}: {notice.title}")

        sent_to.append(user.username)

    return Response({
        "success": True,
        "message": "Notice sent successfully.",
        "sent_to": sent_to
    }, status=status.HTTP_200_OK)


# =====================================================
# -------------------- ADMIN LOGIN --------------------
# =====================================================

@api_view(['POST'])
@permission_classes([AllowAny])
def admin_login(request):
    """
    Admin login API: only allows staff or superuser.
    Returns JWT access + refresh tokens if valid.
    """
    username = request.data.get("username")
    password = request.data.get("password")

    if not username or not password:
        return Response({"error": "Username and password are required."}, status=status.HTTP_400_BAD_REQUEST)

    user = authenticate(username=username, password=password)

    if user is None:
        return Response({"error": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED)

    if not user.is_staff and not user.is_superuser:
        return Response({"error": "Access denied. Not an admin user."}, status=status.HTTP_403_FORBIDDEN)

    refresh = RefreshToken.for_user(user)
    return Response({
        "message": "Admin login successful.",
        "access": str(refresh.access_token),
        "refresh": str(refresh),
        "username": user.username,
        "email": user.email,
        "is_superuser": user.is_superuser
    }, status=status.HTTP_200_OK)
