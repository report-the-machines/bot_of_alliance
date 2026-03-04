import os
import re
from googleapiclient.discovery import build

# --- ANTICLANCARIA: BOT OF ALLIANCE (BOA) ---
# UDAAC Technical Engineering Wing
API_KEY = os.environ.get("YT_API_KEY")
VIDEO_ID = os.environ.get("VIDEO_ID")

# The Engineering Disclaimer for GitHub Issue/Summary output
DISCLAIMER = (
    "> [!IMPORTANT]\n"
    "> **Thanks for using REPORT-THE-MACHINES.** Please remember this is not 100% accurate yet, "
    "and always double check users before reporting.\n\n"
    "---"
)

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
        
        # Check for external scam links in bio
        has_link = len(re.findall(r'(https?://[^\s]+|www\.[^\s]+)', bio)) > 0
        
        # Logic Classification
        is_hardcore = (vids == 0 and has_link)  # Classic Grade A Signature
        is_phrase = is_bot_text(comment_text)   # Grade B/C Pattern Match

        if is_hardcore or is_phrase:
            print(f"### [!] NEUTRALIZED: {snippet['title']}")
            print(f"- **Target Grade:** {'Grade A (Scammer)' if is_hardcore else 'Grade B (Persona)'}")
            print(f"- **Logic:** {'Pattern Match' if is_phrase else 'Metadata Signature (Scam Bio)'}")
            print(f"- **Comment:** \"{comment_text}\"")
            print(f"- **Intel:** https://youtube.com/channel/{c_id}\n")

def hunt(youtube, video_id):
    # Print the UDAAC Disclaimer first
    print(DISCLAIMER)
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
                if "authorChannelId" in s:
                    c_id = s["authorChannelId"]["value"]
                    ids.append(c_id)
                    mapping[c_id] = s["textDisplay"]
            
            # Batch process channel metadata in groups of 50 (API Limit)
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
