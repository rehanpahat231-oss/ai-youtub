import os
import random
import requests
import json
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter
import imageio.v3 as iio
from datetime import datetime
import sys

# ================= CONFIG =================
OUTPUT_DIR = "outputs"
LOGS_DIR = "logs"
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

TRENDING_NICHES = [
    "cute baby moments", "funny cats", "motivational quotes",
    "amazing facts", "space discoveries", "tech gadgets",
    "cooking hacks", "fitness motivation", "travel destinations",
    "money tips", "psychology facts", "history mysteries"
]

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")
    with open(f"{LOGS_DIR}/agent.log", "a") as f:
        f.write(f"{datetime.now()}: {msg}\n")

# ================= AI CONTENT GENERATION =================
def generate_content_idea():
    """Generate viral content idea using free AI or templates"""
    niche = random.choice(TRENDING_NICHES)
    
    # Free method: Using random templates (100% free, no API needed)
    templates = [
        f"Top 5 shocking facts about {niche} that will blow your mind",
        f"This {niche} changed my life completely",
        f"You won't believe these {niche} secrets",
        f"Amazing {niche} compilation 2026",
        f"Wait for the twist in this {niche} video"
    ]
    
    title = random.choice(templates)
    
    # Generate description with hashtags
    description = f"""{title.title()}

Discover the most amazing {niche} content that everyone is talking about!

🔔 Subscribe for daily updates
👍 Like if you enjoyed
💬 Comment your thoughts

#Shorts #{niche.replace(' ', '')} #Viral #Trending #Amazing"""

    tags = [niche, "shorts", "viral", "trending", "2026", "amazing", "facts"]
    
    return {
        "niche": niche,
        "title": title.title(),
        "description": description,
        "tags": tags,
        "prompt": f"high quality {niche}, cinematic lighting, 4k, professional photography, trending on social media"
    }

def generate_ai_image(prompt, filename):
    """100% Free AI Image Generation (Pollinations)"""
    try:
        log(f"Generating image: {prompt[:50]}...")
        encoded = requests.utils.quote(prompt)
        url = f"https://image.pollinations.ai/prompt/{encoded}?width=1080&height=1920&nologo=true&seed={random.randint(1,9999)}"
        
        r = requests.get(url, timeout=60)
        if r.status_code == 200 and len(r.content) > 5000:
            path = f"{OUTPUT_DIR}/{filename}"
            with open(path, 'wb') as f:
                f.write(r.content)
            log(f"✅ Image saved: {filename} ({len(r.content)//1024}KB)")
            return path
        else:
            log(f"❌ Image failed: HTTP {r.status_code}")
            return None
    except Exception as e:
        log(f"❌ Error: {e}")
        return None

# ================= VIDEO EDITING ENGINE =================
def create_professional_video(image_paths, content_data):
    """Edit video with effects, text, transitions"""
    log("🎬 Starting video edit...")
    
    frames = []
    fps = 30
    duration_per_scene = 3.5  # 7 second total video
    total_frames = int(fps * duration_per_scene)
    
    for idx, img_path in enumerate(image_paths):
        log(f"Processing scene {idx+1}...")
        
        # Load and enhance image
        img = Image.open(img_path).convert('RGB')
        img = img.resize((1080, 1920), Image.Resampling.LANCZOS)
        
        # Professional color grading (viral look)
        enhancer = ImageEnhance.Color(img)
        img = enhancer.enhance(1.4)  # High saturation
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.2)
        enhancer = ImageEnhance.Sharpness(img)
        img = enhancer.enhance(1.3)
        
        # Add text overlay (Title)
        draw = ImageDraw.Draw(img)
        try:
            font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 60)
            font_sub = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 40)
        except:
            font_title = ImageFont.load_default()
            font_sub = font_title
        
        # Title text (center top)
        title = content_data['title'][:40] + "..." if len(content_data['title']) > 40 else content_data['title']
        bbox = draw.textbbox((0,0), title, font=font_title)
        x = (1080 - (bbox[2]-bbox[0])) // 2
        y = 100
        
        # Text shadow
        draw.text((x+2, y+2), title, fill='black', font=font_title)
        draw.text((x, y), title, fill='white', font=font_title)
        
        # Subscribe watermark (bottom)
        sub_text = "🔔 Subscribe for Daily Videos"
        bbox = draw.textbbox((0,0), sub_text, font=font_sub)
        x = (1080 - (bbox[2]-bbox[0])) // 2
        y = 1800
        draw.rectangle([x-10, y-5, x+(bbox[2]-bbox[0])+10, y+50], fill='red')
        draw.text((x, y), sub_text, fill='white', font=font_sub)
        
        # Ken Burns Effect (smooth zoom + pan)
        for i in range(total_frames):
            progress = i / total_frames
            
            # Zoom from 1.0 to 1.2
            scale = 1.0 + (0.2 * progress)
            
            # Pan slightly upward
            new_w = int(1080 / scale)
            new_h = int(1920 / scale)
            left = (1080 - new_w) // 2
            top = int((1920 - new_h) * progress * 0.1)
            
            cropped = img.crop((left, top, left+new_w, top+new_h))
            cropped = cropped.resize((1080, 1920))
            frames.append(np.array(cropped))
    
    # Export video
    output_path = f"{OUTPUT_DIR}/viral_video_{datetime.now().strftime('%H%M')}.mp4"
    log(f"💾 Exporting {len(frames)} frames...")
    
    iio.imwrite(
        output_path,
        frames,
        fps=fps,
        codec="libx264",
        pixelformat="yuv420p",
        quality=8
    )
    
    log(f"✅ Video exported: {output_path}")
    return output_path

# ================= YOUTUBE UPLOAD =================
def upload_to_youtube(video_path, content_data):
    """Upload video with AI-generated metadata"""
    try:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload
        
        # Load credentials from environment
        if not os.environ.get('YT_TOKEN'):
            log("⚠️  No YT_TOKEN found, skipping upload")
            return False
            
        creds_info = json.loads(os.environ['YT_TOKEN'])
        creds = Credentials.from_authorized_user_info(creds_info)
        youtube = build('youtube', 'v3', credentials=creds)
        
        # Prepare metadata
        body = {
            'snippet': {
                'title': content_data['title'][:100],  # YouTube limit
                'description': content_data['description'],
                'tags': content_data['tags'][:15],  # Max 15 tags
                'categoryId': '24',  # Entertainment (change as needed)
                'defaultLanguage': 'en',
                'defaultAudioLanguage': 'en'
            },
            'status': {
                'privacyStatus': 'public',
                'selfDeclaredMadeForKids': False,
                'publishAt': None  # Immediate publish
            }
        }
        
        log(f"📤 Uploading: {content_data['title'][:50]}...")
        
        media = MediaFileUpload(
            video_path,
            mimetype='video/mp4',
            resumable=True
        )
        
        request = youtube.videos().insert(
            part='snippet,status',
            body=body,
            media_body=media
        )
        
        response = request.execute()
        video_id = response['id']
        video_url = f"https://youtube.com/shorts/{video_id}"
        
        log(f"🚀 Upload successful!")
        log(f"🔗 URL: {video_url}")
        
        # Save to file
        with open(f"{LOGS_DIR}/uploaded.txt", "a") as f:
            f.write(f"{datetime.now()} | {video_id} | {content_data['title']}\n")
            
        return video_url
        
    except Exception as e:
        log(f"❌ Upload failed: {e}")
        return False

# ================= MAIN AGENT =================
def main():
    log("🤖 AI Agent Starting...")
    
    try:
        # Step 1: Content Research & Planning
        log("🧠 Generating content strategy...")
        content = generate_content_idea()
        log(f"📌 Niche: {content['niche']}")
        log(f"📝 Title: {content['title'][:60]}...")
        
        # Step 2: Generate Visuals
        img1 = generate_ai_image(content['prompt'] + ", scene 1", "scene1.jpg")
        img2 = generate_ai_image(content['prompt'] + ", scene 2, different angle", "scene2.jpg")
        
        if not img1 or not img2:
            log("❌ Image generation failed")
            return 1
        
        # Step 3: Video Editing
        video_path = create_professional_video([img1, img2], content)
        if not video_path:
            log("❌ Video editing failed")
            return 1
        
        # Step 4: Upload to YouTube
        result = upload_to_youtube(video_path, content)
        
        if result:
            log("✅ Agent completed successfully!")
            # Save metadata for reference
            with open(f"{OUTPUT_DIR}/metadata.txt", "w") as f:
                json.dump(content, f, indent=2)
            return 0
        else:
            log("⚠️  Upload skipped (check YT_TOKEN)")
            return 0
            
    except Exception as e:
        log(f"💥 Agent crashed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
