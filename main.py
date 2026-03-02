import os
import re
from googleapiclient.discovery import build

# --- ANTICLANCARIA: BOT OF ALLIANCE ---
# Pulling secrets from the GitHub Vault
API_KEY = os.environ.get("YT_API_KEY")
VIDEO_ID = os.environ.get("VIDEO_ID")

def is_bot_text(text):
    text_lower = text.lower()
    # Patterns for Sleeper Bots & Aesthetic Script clusters
    patterns = ["loving and caring", "helped me understand", "aesthetic", "✨", "1.", "2.", "3."]
    return any(p in text_lower for p in patterns)

def check_channels_batch(youtube, channel_ids, comment_map):
    request = youtube.channels().list(
        part="statistics,snippet",
        id=",".join(channel_ids)
    )
    res = request.execute()
    
    for item in res.get("items", []):
        c_id = item["id"]
        snippet = item["snippet"]
        channel_stats = item["statistics"]
        bio = snippet.get("description", "").lower()
        
        vids = int(channel_stats.get("videoCount", 0))
        comment_text = comment_map.get(c_id, "")
        
        has_link = len(re.findall(r'(https?://[^\s]+|www\.[^\s]+)', bio)) > 0
        is_hardcore = (vids == 0 and has_link)
        is_phrase = is_bot_text(comment_text)

        if is_hardcore or is_phrase:
            print(f"### [!] NEUTRALIZED: {snippet['title']}")
            print(f"- **Logic:** {'Pattern Match' if is_phrase else 'Metadata Signature'}")
            print(f"- **Comment:** \"{comment_text}\"")
            print(f"- **Intel:** https://youtube.com/channel/{c_id}\n")

def hunt(youtube, video_id):
    print(f"## 🛰️ DEPLOYING TO TARGET: {video_id}\n")
    try:
        request = youtube.commentThreads().list(
            part="snippet", videoId=video_id, maxResults=100, textFormat="plainText"
        )
        
        while request:
            response = request.execute()
            ids, mapping = [], {}
            
            for item in response.get("items", []):
                s = item["snippet"]["topLevelComment"]["snippet"]
                c_id = s["authorChannelId"]["value"]
                ids.append(c_id)
                mapping[c_id] = s["textDisplay"]
            
            for i in range(0, len(ids), 50):
                check_channels_batch(youtube, ids[i:i+50], mapping)
            
            request = youtube.commentThreads().list_next(request, response)
            
    except Exception as e:
        print(f"\n[!] ERROR IN DEPLOYMENT: {e}")

if __name__ == "__main__":
    if not API_KEY:
        print("CRITICAL: API Key missing from Vault.")
    elif VIDEO_ID:
        # Clean the ID in case the Scout pasted a full URL
        match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11})", VIDEO_ID)
        v_id = match.group(1) if match else VIDEO_ID
        
        if len(v_id) == 11:
            youtube_service = build("youtube", "v3", developerKey=API_KEY)
            hunt(youtube_service, v_id)
        else:
            print("Invalid Target ID format.")
    else:
        print("No target acquired. Standing by.")
