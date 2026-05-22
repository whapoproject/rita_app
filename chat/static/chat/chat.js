// ✅ chat.js
const messageForm = document.getElementById("message-form");
const messageInput = document.getElementById("message-input");
const chatLog = document.getElementById("chat-log");
const recordButton = document.getElementById("record-button");

// Read these from hidden inputs set in template
const selectedUser = document.getElementById("selected-user")?.value || "";
const currentUsername = document.getElementById("current-username")?.value || "";

// 🔄 Auto Fetch new messages every 5 seconds
let lastMessageCount = 0;
function fetchNewMessages() {
    if (!selectedUser) return;

    fetch(`/fetch_messages/?user=${selectedUser}`)
        .then(response => response.json())
        .then(data => {
            const currentCount = data.messages.length;
            if (currentCount > lastMessageCount) {
                renderMessages(data.messages);
                lastMessageCount = currentCount;
                const lastMsg = data.messages[data.messages.length - 1];
                if (lastMsg.sender !== currentUsername) playNotificationSound();
            }
        })
        .catch(console.error);
}
setInterval(fetchNewMessages, 5000);

// Render messages in the chat log
function renderMessages(messages) {
    chatLog.innerHTML = "";
    messages.forEach(msg => {
        const div = document.createElement("div");
        div.className = `message-container ${msg.sender === currentUsername ? "sent" : "received"}`;
        div.innerHTML = `
            <div class="message">
                <strong>${msg.sender}:</strong>
                ${msg.image ? `<img src="${msg.image}" style="max-width: 200px;">` :
                    msg.audio ? `<audio controls src="${msg.audio}"></audio>` :
                    msg.content}
            </div>
            <div class="timestamp">${msg.timestamp}</div>
        `;
        chatLog.appendChild(div);
    });
    chatLog.scrollTop = chatLog.scrollHeight;
}

// 📤 Send text message
messageForm.addEventListener("submit", function (e) {
    e.preventDefault();
    const msg = messageInput.value.trim();
    if (!msg || !selectedUser) return;

    const formData = new FormData(messageForm);
    formData.set("content", msg);
    formData.set("user", selectedUser);
    messageInput.value = "";

    fetch("/send_message/", {
        method: "POST",
        headers: { "X-CSRFToken": getCSRFToken() },
        body: formData,
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === "success") {
            // Redirect to reload chat page with selected user
            window.location.href = `/chat/?user=${selectedUser}`;
        }
    });
});

// 🖼️ Upload image + preview
const imageInput = document.getElementById("image-upload");
const imageButton = document.getElementById("upload-image-btn");
imageButton.addEventListener("click", () => imageInput.click());

imageInput.addEventListener("change", () => {
    const file = imageInput.files[0];
    if (!file || !selectedUser) return;

    const formData = new FormData();
    formData.append("user", selectedUser);
    formData.append("image", file);

    fetch("/send_message/", {
        method: "POST",
        headers: { "X-CSRFToken": getCSRFToken() },
        body: formData,
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === "success") {
            // Reload page with selected user
            window.location.href = `/chat/?user=${selectedUser}`;
        }
    });
});

// 🔊 Notification sound
const notificationSound = new Audio("/static/chat/notify.mp3");
function playNotificationSound() {
    notificationSound.play().catch(err => console.warn("Sound blocked", err));
}

// 🔐 CSRF token helper
function getCSRFToken() {
    const name = "csrftoken";
    return document.cookie.split(";").map(c => c.trim()).find(c => c.startsWith(name + "="))?.split("=")[1];
}
