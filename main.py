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
    "---\n"
)

def get_keywords(summary):
    """Extracts significant words from the user's summary."""
    if not summary: return []
    # Find words, convert to lower, and ignore short filler words
    words = re.findall(r'\w+', summary.lower())
    stop_words = {'video', 'about', 'this', 'that', 'with', 'from', 'they', 'them', 'their'}
    return [w for w in words if w not in stop_words and len(w) > 3]

def is_rational_human(text, bio, vids, subs, keywords):
    """The UDAAC Rationality Filter: Returns True if user is likely human."""
    text_lower = text.lower()
    
    # 1. The Human Emoji Shield 🫩🥀✌️💔
    human_emojis = ["🫩", "🥀", "✌️", "💔"]
    has_human_vibes = any(e in text for e in human_emojis)
    
    # 2. Context Match: Does the comment match your summary?
    matches_context = any(word in text_lower for word in keywords) if keywords else False

    # 3. Signature Checks
    has_link = len(re.findall(r'(https?://[^\s]+|www\.[^\s]+)', bio)) > 0
    is_suspicious_profile = (vids == 0 and subs > 1000) # Classic 'Bought Account' signature

    # LOGIC: If they use human emojis or talk about the topic, AND don't have a scam link...
    if (has_human_vibes or matches_context) and not has_link and not is_suspicious_profile:
        return True
    return False

def is_bot_text(text):
    """Detects 'Grade B' Persona Bot patterns."""
    text_lower = text.lower()
    patterns = ["loving and caring", "helped me understand", "aesthetic", "✨", "1.", "2.", "3."]
    return any(p in text_lower for p in patterns)

def process_comments(youtube, v_id, keywords):
    """Main hunt logic: Scans comments and filters via Rationality."""
    body = DISCLAIMER + f"## 🛰️ DEPLOYMENT TARGET: {v_id}\n\n"
    found_any = False
    
    try:
        request = youtube.commentThreads().list(
            part="snippet", videoId=v_id, maxResults=100, textFormat="plainText"
        )
        response = request.execute()
        
        ids, mapping = [], {}
        for item in response.get("items", []):
            s = item["snippet"]["topLevelComment"]["snippet"]
            if "authorChannelId" in s:
                c_id = s["authorChannelId"]["value"]
                ids.append(c_id)
                mapping[c_id] = s["textDisplay"]

        # Batch check channel metadata (50 at a time)
        chan_request = youtube.channels().list(part="statistics,snippet", id=",".join(ids))
        chan_res = chan_request.execute()

        for item in chan_res.get("items", []):
            c_id = item["id"]
            snippet = item["snippet"]
            stats = item["statistics"]
            bio = snippet.get("description", "").lower()
            vids = int(stats.get("videoCount", 0))
            subs = int(stats.get("subscriberCount", 0))
            comment = mapping.get(c_id, "")

            # RUN RATIONALITY FILTER
            if is_rational_human(comment, bio, vids, subs, keywords):
                continue

            # RUN THREAT DETECTION
            has_link = len(re.findall(r'(https?://[^\s]+|www\.[^\s]+)', bio)) > 0
            is_hardcore = (vids == 0 and has_link)
            is_phrase = is_bot_text(comment)

            if is_hardcore or is_phrase:
                found_any = True
                body += f"### [!] NEUTRALIZED: {snippet['title']}\n"
                body += f"- **Grade:** {'A (Scammer)' if is_hardcore else 'B (Persona)'}\n"
                body += f"- **Comment:** \"{comment}\"\n"
                body += f"- **Intel:** https://youtube.com/channel/{c_id}\n\n"

        if not found_any:
            body += "✅ **Scan Complete:** No high-confidence clankers detected."

    except Exception as e:
        body += f"⚠️ **Critical Error:** {str(e)}"

    return body

@app.route('/hunt', methods=['POST'])
def hunt_action():
    v_id_raw = request.form.get("video_id")
    summary = request.form.get("video_summary", "")
    
    # ID Extraction
    match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11})", v_id_raw)
    v_id = match.group(1) if match else v_id_raw
    
    keywords = get_keywords(summary)
    youtube = build("youtube", "v3", developerKey=API_KEY)
    
    report = process_comments(youtube, v_id, keywords)
    
    # Save to file for GitHub Actions to read
    with open("comment.md", "w", encoding="utf-8") as f:
        f.write(report)
        
    return "<h1>UDAAC Intelligence Report Generated.</h1><p>Check comment.md or your GitHub logs.</p>"

if __name__ == "__main__":
    app.run(debug=True)
