import os
import random
import requests
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
import imageio.v3 as iio
from datetime import datetime
import json
import sys
import time

# Setup folders
os.makedirs('outputs', exist_ok=True)
os.makedirs('logs', exist_ok=True)

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")
    with open(f"logs/agent.log", "a") as f:
        f.write(f"{datetime.now()}: {msg}\n")

# Content ideas
NICHES = [
    "cute baby moments", "funny cats", "amazing facts", 
    "space discoveries", "motivational quotes", "tech gadgets"
]

def get_content():
    niche = random.choice(NICHES)
    titles = [
        f"You won't believe these {niche}!",
        f"Amazing {niche} that will blow your mind",
        f"Wait for it... {niche} #shorts",
        f"This {niche} changed everything"
    ]
    return {
        "niche": niche,
        "title": random.choice(titles),
        "description": f"🔔 Daily {niche} content!\n\n#Shorts #Viral #{niche.replace(' ', '')}",
        "tags": [niche, "shorts", "viral", "trending"],
        "prompt": f"high quality {niche}, cinematic, 4k, trending on social media"
    }

def generate_image(prompt, filename, max_retries=3):
    """Generate with retry logic"""
    for attempt in range(max_retries):
        try:
            log(f"Generating image... (attempt {attempt + 1}/{max_retries})")
            
            # Different seed for each retry
            seed = random.randint(1, 99999)
            encoded = requests.utils.quote(prompt)
            url = f"https://image.pollinations.ai/prompt/{encoded}?width=1080&height=1920&nologo=true&seed={seed}"
            
            # Increased timeout to 120 seconds
            r = requests.get(url, timeout=120)
            
            if r.status_code == 200 and len(r.content) > 5000:
                path = f"outputs/{filename}"
                with open(path, 'wb') as f:
                    f.write(r.content)
                log(f"✅ Image saved: {filename} ({len(r.content)//1024}KB)")
                return path
            
            log(f"❌ Attempt {attempt + 1} failed: Status {r.status_code}")
            
        except requests.exceptions.Timeout:
            log(f"⏱️ Timeout on attempt {attempt + 1}, retrying...")
        except Exception as e:
            log(f"❌ Error on attempt {attempt + 1}: {str(e)[:50]}")
        
        # Wait before retry
        if attempt < max_retries - 1:
            wait_time = 5 * (attempt + 1)  # 5s, 10s, 15s
            log(f"⏳ Waiting {wait_time}s before retry...")
            time.sleep(wait_time)
    
    log(f"❌ All {max_retries} attempts failed for {filename}")
    return None

def create_video(img1, img2, content):
    try:
        log("Creating video...")
        frames = []
        fps = 30
        duration = 3.5
        
        for idx, img_path in enumerate([img1, img2]):
            log(f"Processing image {idx + 1}...")
            img = Image.open(img_path).convert('RGB')
            img = img.resize((1080, 1920))
            
            # Enhance colors
            enhancer = ImageEnhance.Color(img)
            img = enhancer.enhance(1.3)
            
            # Add text
            draw = ImageDraw.Draw(img)
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 60)
            except:
                font = ImageFont.load_default()
            
            text = content['title'][:40]
            bbox = draw.textbbox((0,0), text, font=font)
            x = (1080 - (bbox[2]-bbox[0]))//2
            y = 100
            
            draw.rectangle([x-10, y-5, x+(bbox[2]-bbox[0])+10, y+70], fill='black')
            draw.text((x, y), text, fill='white', font=font)
            
            # Ken Burns effect
            for i in range(int(fps * duration)):
                progress = i / (fps * duration)
                scale = 1.0 + (0.15 * progress)
                new_w = int(1080 / scale)
                new_h = int(1920 / scale)
                left = (1080 - new_w)//2
                top = (1920 - new_h)//2
                
                cropped = img.crop((left, top, left+new_w, top+new_h))
                cropped = cropped.resize((1080, 1920))
                frames.append(np.array(cropped))
            
            log(f"✅ Image {idx + 1} processed")
        
        output = "outputs/video.mp4"
        log(f"Saving video ({len(frames)} frames)...")
        iio.imwrite(output, frames, fps=fps, codec="libx264", quality=8)
        log(f"✅ Video created: {output}")
        return output
        
    except Exception as e:
        log(f"❌ Video error: {e}")
        import traceback
        traceback.print_exc()
        return None

def upload_to_youtube(video_path, content):
    try:
        if not os.environ.get('YT_TOKEN'):
            log("⚠️ No YT_TOKEN found")
            return False
            
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload
        
        creds_info = json.loads(os.environ['YT_TOKEN'])
        creds = Credentials.from_authorized_user_info(creds_info)
        youtube = build('youtube', 'v3', credentials=creds)
        
        body = {
            'snippet': {
                'title': content['title'][:100],
                'description': content['description'],
                'tags': content['tags'][:15],
                'categoryId': '24'
            },
            'status': {
                'privacyStatus': 'public',
                'selfDeclaredMadeForKids': False
            }
        }
        
        log(f"Uploading: {content['title'][:50]}...")
        media = MediaFileUpload(video_path, mimetype='video/mp4')
        request = youtube.videos().insert(part='snippet,status', body=body, media_body=media)
        response = request.execute()
        
        video_id = response['id']
        log(f"🚀 Uploaded! https://youtube.com/shorts/{video_id}")
        
        with open(f"logs/uploads.txt", "a") as f:
            f.write(f"{datetime.now()} | {video_id} | {content['title']}\n")
        return True
        
    except Exception as e:
        log(f"❌ Upload failed: {e}")
        return False

def main():
    log("🤖 Agent Starting...")
    
    content = get_content()
    log(f"Niche: {content['niche']}")
    log(f"Title: {content['title'][:60]}")
    
    # Generate images with retry
    img1 = generate_image(content['prompt'], "img1.jpg")
    
    # Small delay between requests
    time.sleep(2)
    
    img2 = generate_image(content['prompt'] + " different angle", "img2.jpg")
    
    if not img1 or not img2:
        log("❌ Images failed - trying fallback prompts...")
        # Try simpler prompts as fallback
        if not img1:
            img1 = generate_image("cute baby", "img1.jpg", max_retries=2)
        if not img2:
            img2 = generate_image("adorable baby", "img2.jpg", max_retries=2)
    
    if not img1 or not img2:
        log("❌ All image attempts failed")
        return 1
    
    video = create_video(img1, img2, content)
    if not video:
        log("❌ Video failed")
        return 1
    
    # Try to upload
    upload_to_youtube(video, content)
    
    # Save metadata
    with open(f"outputs/metadata.txt", "w") as f:
        f.write(f"Title: {content['title']}\n")
        f.write(f"Desc: {content['description']}\n")
    
    log("✅ Done!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
