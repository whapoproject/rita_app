from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

import uuid



# =========================
# USER PROFILE
# =========================
class Profile(models.Model):

    user = models.OneToOneField(User, on_delete=models.CASCADE)

    # 🔥 admin analytics
    total_messages_sent = models.PositiveIntegerField(default=0)
    total_rooms_created = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.user.username


# =========================
# AUTO CREATE PROFILE
# =========================
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):

    if created:
        Profile.objects.create(user=instance)


# =========================
# CHAT ROOM
# =========================
class ChatRoom(models.Model):

    # unique private room id
    room_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False
    )

    # creator account
    creator = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_rooms'
    )

    # guest joins using nickname only
    participant_name = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    # room active state
    active = models.BooleanField(default=True)

    # prevent second guest joining
    locked = models.BooleanField(default=False)

    # timestamps
    created_at = models.DateTimeField(auto_now_add=True)

    expires_at = models.DateTimeField()

    # detect expiration
    def is_expired(self):

        from django.utils import timezone

        return timezone.now() > self.expires_at

    # auto expire remaining time
    def time_left(self):

        from django.utils import timezone

        remaining = self.expires_at - timezone.now()

        return remaining.total_seconds()

    # string display
    def __str__(self):

        return f"Room {self.room_id}"

# =========================
# MESSAGE MODEL
# =========================
class Message(models.Model):

    room = models.ForeignKey(
        ChatRoom,
        on_delete=models.CASCADE,
        related_name='messages'
    )

    sender_name = models.CharField(max_length=100)

    content = models.TextField(blank=True)

    audio = models.FileField(
        upload_to='chat_audio/',
        blank=True,
        null=True
    )

    image = models.ImageField(
        upload_to='chat_images/',
        blank=True,
        null=True
    )

    timestamp = models.DateTimeField(auto_now_add=True)

    # 🔥 AUTO DELETE AFTER VIEW
    auto_delete_at = models.DateTimeField(
        blank=True,
        null=True
    )

    def __str__(self):

        return f'{self.sender_name} in {self.room.room_id}'