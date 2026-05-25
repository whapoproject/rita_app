from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET
from django.utils import timezone
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count
from .models import Profile, ChatRoom, Message
from django.http import HttpResponse
from .models import ChatRoom, Message

# =========================
# REGISTER
# =========================
def register(request):

    if request.method == 'POST':

        username = request.POST['username']
        password = request.POST['password']
        password_confirm = request.POST['password_confirm']

        if password != password_confirm:
            return render(request, 'chat/register.html', {
                'error': 'Passwords do not match'
            })

        if User.objects.filter(username=username).exists():
            return render(request, 'chat/register.html', {
                'error': 'Username already exists'
            })

        User.objects.create_user(
            username=username,
            password=password
        )

        return render(request, 'chat/register.html', {
            'success': 'Account created successfully'
        })

    return render(request, 'chat/register.html')


# =========================
# LOGIN
# =========================
def user_login(request):

    if request.method == 'POST':

        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is None:
            return render(request, 'chat/login.html', {
                'error': 'Invalid username or password'
            })

        login(request, user)

        if user.is_superuser:
            return redirect('chat:admin_dashboard')

        return redirect('chat:dashboard')

    return render(request, 'chat/login.html')
####
# Manuel uses
def manual(request):
    return render(request, 'chat/manual.html')
def welcome(request):
    return render(request, 'chat/welcome.html')


# =========================
# LOGOUT
# =========================
def custom_logout(request):

    logout(request)

    return redirect('chat:login')


# =========================
# USER DASHBOARD
# =========================
@login_required
def dashboard(request):

    rooms = ChatRoom.objects.filter(
        creator=request.user
    ).order_by('-created_at')

    return render(request, 'chat/dashboard.html', {
        'rooms': rooms
    })


# =========================
# ADMIN DASHBOARD
# =========================
@staff_member_required
def admin_dashboard(request):

    users = User.objects.all().order_by('-date_joined')

    rooms = ChatRoom.objects.all().order_by('-created_at')

    return render(request, 'chat/admin_dashboard.html', {
        'users': users,
        'rooms': rooms
    })


# =========================
# CREATE ROOM
# =========================
@login_required
def create_room(request):

    room = ChatRoom.objects.create(
        creator=request.user,
        
        expires_at=timezone.now() + timezone.timedelta(minutes=3)
    )

    return redirect(
        'chat:chat_room',
        room_id=room.room_id
    )

# =========================
# CHAT ROOM
# =========================
def chat_room(request, room_id):

    room = get_object_or_404(
        ChatRoom,
        room_id=room_id,
        active=True
    )

    # EXPIRE ROOM
    if room.is_expired():

        room.messages.all().delete()
        room.delete()

        return render(request, 'chat/expired.html')
    

    # ====================================
    # CREATOR VIEW
    # ====================================
    if request.user.is_authenticated:

        if request.user == room.creator:

            messages = room.messages.all().order_by('timestamp')

            return render(request, 'chat/chat_room.html', {
                'room': room,
                'messages': messages
            })

    # ====================================
    # GUEST VIEW
    # ====================================

    guest_name = request.session.get(
        f'guest_{room.room_id}'
    )

    # FIRST JOIN
    if not guest_name:

        if request.method == 'POST':

            nickname = request.POST.get('nickname')

            if not nickname:

                return render(request, 'chat/join_guest.html', {
                    'room': room,
                    'error': 'Enter nickname'
                })

            request.session[
                f'guest_{room.room_id}'
            ] = nickname

            room.participant_name = nickname
            room.save()

            return redirect(
                'chat:chat_room',
                room_id=room.room_id
            )

        return render(request, 'chat/join_guest.html', {
            'room': room
        })

    # GUEST INSIDE CHAT
    messages = room.messages.all().order_by('timestamp')

    return render(request, 'chat/join_guest.html', {
        'room': room,
        'messages': messages,
        'guest_name': guest_name
    })
# =========================
# FETCH MESSAGES
# =========================
@require_GET
def fetch_messages(request, room_id):

    room = get_object_or_404(
        ChatRoom,
        room_id=room_id
    )

    # delete expired messages
    room.messages.filter(
        auto_delete_at__lte=timezone.now()
    ).delete()
    messages = room.messages.all().order_by('timestamp')

    data = []

    for msg in messages:

        data.append({
            'sender': msg.sender_name,
            'content': msg.content,
            'audio': msg.audio.url if msg.audio else None,
            'image': msg.image.url if msg.image else None,
            'timestamp': msg.timestamp.strftime('%H:%M')
        })

    return JsonResponse({
        'messages': data
    })
# =========================
# SEND MESSAGE
# =========================
@csrf_exempt
def send_message(request, room_id):

    if request.method != 'POST':

        return JsonResponse({
            'error': 'Invalid request'
        }, status=400)

    room = get_object_or_404(
        ChatRoom,
        room_id=room_id
    )

    content = request.POST.get('content', '').strip()

    audio = request.FILES.get('audio')

    image = request.FILES.get('image')

    if not content and not audio and not image:

        return JsonResponse({
            'error': 'Empty message'
        }, status=400)

    # =========================
    # CREATOR MESSAGE
    # =========================
    if request.user.is_authenticated:

        if request.user == room.creator:

            sender_name = request.user.username

        else:

            return JsonResponse({
                'error': 'Unauthorized'
            }, status=403)

    # =========================
    # GUEST MESSAGE
    # =========================
    else:

        guest_name = request.session.get(
            f'guest_{room.room_id}'
        )

        if not guest_name:

            return JsonResponse({
                'error': 'Guest session expired'
            }, status=403)

        sender_name = guest_name

    # =========================
    # SAVE MESSAGE
    # =========================
   
    Message.objects.create(
    room=room,
    sender_name=sender_name,
    content=content,
    audio=audio,
    image=image,
    auto_delete_at=timezone.now() + timezone.timedelta(seconds=10)
    )

    return JsonResponse({
        'status': 'success'
    })

# =========================
# END CHAT
# =========================
@login_required
def end_chat(request, room_id):

    room = get_object_or_404(
        ChatRoom,
        room_id=room_id
    )

    if request.user != room.creator:
        return HttpResponseForbidden("Unauthorized")

    room.messages.all().delete()

    room.delete()

    return redirect('chat:dashboard')




# FOR ADMIN ###

@staff_member_required
def admin_dashboard(request):

    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    # =========================
    # ROOM STATS
    # =========================
    total_rooms = ChatRoom.objects.count()
    active_rooms = ChatRoom.objects.filter(active=True).count()
    expired_rooms = ChatRoom.objects.filter(expires_at__lt=now).count()

    # most active room (by messages)
    top_room = ChatRoom.objects.annotate(
        msg_count=Count('messages')
    ).order_by('-msg_count').first()

    # =========================
    # MESSAGE STATS
    # =========================
    total_messages = Message.objects.count()
    today_messages = Message.objects.filter(timestamp__gte=today_start).count()

    # most active sender (simple grouping)
    top_sender = (
        Message.objects.values('sender_name')
        .annotate(total=Count('id'))
        .order_by('-total')
        .first()
    )

    # =========================
    # USER STATS
    # =========================
    total_users = Profile.objects.count()

    top_users = Profile.objects.order_by('-total_messages_sent')[:5]

    # =========================
    # RECENT ACTIVITY
    # =========================
    recent_messages = Message.objects.order_by('-timestamp')[:20]

    recent_rooms = ChatRoom.objects.order_by('-created_at')[:10]

    # =========================
    # CONTEXT
    # =========================
    context = {

        "total_rooms": total_rooms,
        "active_rooms": active_rooms,
        "expired_rooms": expired_rooms,

        "top_room": top_room,

        "total_messages": total_messages,
        "today_messages": today_messages,

        "top_sender": top_sender,

        "total_users": total_users,
        "top_users": top_users,

        "recent_messages": recent_messages,
        "recent_rooms": recent_rooms,
    }

    return render(request, "chat/admin_dashboard.html", context)




def end_chat(request, room_id):
    room = ChatRoom.objects.filter(room_id=room_id).first()

    # If room already deleted or expired
    if not room:
        return HttpResponse(
            "This chat room has expired or already been deleted.",
            status=200
        )

    # Optional: extra safety check
    if room.is_expired():
        Message.objects.filter(room=room).delete()
        room.delete()
        return HttpResponse(
            "Chat room expired and was cleaned up.",
            status=200
        )

    # Normal cleanup
    Message.objects.filter(room=room).delete()
    room.delete()

    return redirect("chat:dashboard")