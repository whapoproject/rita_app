import time
import requests

# Configuration
CLEAR_URL = 'http://localhost:5050/clear_messages/'  # Replace with your actual endpoint
CSRF_TOKEN = 'your_csrf_token_here'  # Optional: If CSRF token is needed
HEADERS = {
    'X-CSRFToken': CSRF_TOKEN
}

def clear_messages():
    try:
        response = requests.post(CLEAR_URL, headers=HEADERS)
        if response.status_code == 200:
            print("✅ Chat messages cleared.")
        else:
            print(f"⚠️ Failed to clear messages. Status: {response.status_code}")
    except Exception as e:
        print(f"❌ Error clearing messages: {e}")

def run_clear_loop(interval_seconds=60):
    print("🔁 Starting message clear loop every 3 minutes...")
    while True:
        clear_messages()
        time.sleep(interval_seconds)

