import os
import re
from googleapiclient.discovery import build
from flask import Flask, render_template, request

app = Flask(__name__)

# --- UDAAC OFFICIAL CONFIGURATION ---
API_KEY = os.environ.get("YT_API_KEY")

DISCLAIMER = (
    "> [!IMPORTANT]\n"
    "> **Thanks for using REPORT-THE-MACHINES.** Please remember this is not 100% accurate yet, "
    "and always double check users before reporting.\n\n"
    "---"
)

def get_keywords(summary):
    """Cleans the summary to focus on target keywords (min 4 letters)."""
    if not summary: return []
    # Remove common filler words and split into a list
    words = re.findall(r'\w+', summary.lower())
    stop_words = {'video', 'about', 'this', 'that', 'with', 'from', 'they'}
    return [w for w in words if w not in stop_words and len(w) > 3]

def is_rational_human(text, bio, vids, subs, keywords):
    """Determines if an account is likely a human based on context and vibes."""
    text_lower = text.lower()
    
    # 1. Human Emoji Shield 🫩🥀✌️💔
    human_emojis = ["🫩", "🥀", "✌️", "💔"]
    has_human_vibes = any(e in text for e in human_emojis)
    
    # 2. Context Match (Does the comment mention the video's topic?)
    matches_context = any(word in text_lower for word in keywords) if keywords else False

    # 3. Profile Validation
    has_link = len(re.findall(r'(https?://[^\s]+|www\.[^\s]+)', bio)) > 0
    is_suspicious_profile = (vids == 0 and subs > 1000) # The "Bot King" signature

    # If they show human traits and don't have a scam bio, they are safe.
    if (has_human_vibes or matches_context) and not has_link and not is_suspicious_profile:
        return True
    return False

def is_bot_text(text):
    text_lower = text.lower()
    patterns = ["loving and caring", "helped me understand", "aesthetic", "✨", "1.", "2.", "3."]
    return any(p in text_lower for p in patterns)

def check_channels_batch(youtube, channel_ids, comment_map, keywords):
    request = youtube.channels().list(part="statistics,snippet", id=",".join(channel_ids))
    res = request.execute()
    
    results = []
    for item in res.get("items", []):
        c_id = item["id"]
        snippet = item["snippet"]
        stats = item["statistics"]
        bio = snippet.get("description", "").lower()
        vids = int(stats.get("videoCount", 0))
        subs = int(stats.get("subscriberCount", 0))
        comment_text = comment_map.get(c_id, "")

        # RATIONALITY FILTER
        if is_rational_human(comment_text, bio, vids, subs, keywords):
            continue 

        # DETECTION LOGIC
        has_link = len(re.findall(r'(https?://[^\s]+|www\.[^\s]+)', bio)) > 0
        is_hardcore = (vids == 0 and has_link)
        is_phrase = is_bot_text(comment_text)

        if is_hardcore or is_phrase:
            results.append({
                "name": snippet['title'],
                "grade": "A (Scammer)" if is_hardcore else "B (Persona)",
                "comment": comment_text,
                "url": f"https://youtube.com/channel/{c_id}"
            })
    return results

@app.route('/hunt', methods=['POST'])
def hunt_route():
    raw_id = request.form.get("video_id")
    summary = request.form.get("video_summary", "")
    
    # Extract clean Video ID
    match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11})", raw_id)
    v_id = match.group(1) if match else raw_id
    
    keywords = get_keywords(summary)
    youtube = build("youtube", "v3", developerKey=API_KEY)
    
    # Run the hunt (simplified for display)
    # In reality, you'd loop through comments here
    print(DISCLAIMER)
    print(f"## 🛰️ TARGET ACQUIRED: {v_id}")
    # ... call your hunt logic here ...
    return "Scan Initiated. Check your logs for results."

if __name__ == "__main__":
    app.run(debug=True)
