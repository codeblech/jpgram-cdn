import os
import json
import argparse
from datetime import datetime

CDN_RAW_PREFIX = "https://raw.githubusercontent.com/codeblech/jpgram-cdn/main/"
ROOT = "images"

# Add argument parser
parser = argparse.ArgumentParser(description='Process Instagram posts for clubs')
parser.add_argument('clubs', nargs='*', help='List of club names to process')
parser.add_argument('--fresh', action='store_true', help='Create fresh index instead of updating')
args = parser.parse_args()

# Initialize or load existing index
index = {}
if not args.fresh and os.path.exists("index.json"):
    with open("index.json", "r", encoding='utf-8') as f:
        index = json.load(f)
        
# Get latest post datetime for each club
latest_posts = {}
if not args.fresh:
    for club, posts in index.items():
        if posts:
            latest_posts[club] = datetime.strptime(posts[0]['datetime'], "%B %d, %Y")

# Use provided clubs or get all clubs from directory
clubs_to_process = args.clubs if args.clubs else os.listdir(ROOT)

for club in clubs_to_process:
    club_path = os.path.join(ROOT, club)
    if not os.path.isdir(club_path):
        print(f"Skipping {club}: Not a directory")
        continue

    # Initialize club in index if not exists
    if club not in index:
        index[club] = []
    
    previous_caption = None
    current_post = None
    new_posts = []

    for filename in sorted(os.listdir(club_path), reverse=True):
        if filename.endswith((".webp", ".jpg", ".jpeg", ".png")):
            image_path = os.path.join(ROOT, club, filename)
            datetime_str = filename.split("_UTC")[0]
            try:
                image_datetime = datetime.strptime(datetime_str, "%Y-%m-%d_%H-%M-%S")
                # Skip if post is older than latest post (unless fresh)
                if not args.fresh and club in latest_posts:
                    if image_datetime.date() <= latest_posts[club].date():
                        continue
                formatted_datetime = image_datetime.strftime("%B %d, %Y")
            except ValueError:
                formatted_datetime = "Unknown Date/Time"


            filename_without_ext = os.path.splitext(filename)[0]
            if filename_without_ext.endswith("_UTC"):
                caption_filename = filename_without_ext + ".txt"
            else:
                caption_filename = '_'.join(filename_without_ext.split('_')[:-1]) + ".txt"
            
            caption_path = os.path.join(ROOT, club, caption_filename)

            caption = "No caption available"
            url = "No URL available"

            if os.path.exists(caption_path):
                with open(caption_path, encoding='utf-8') as f:
                    lines = f.read().replace('|||', '\n').splitlines()
                    if lines:
                        url = lines[0].strip()
                        caption = "".join(lines[1:]).strip()

            if caption == previous_caption and current_post:
                current_post["images"].append(CDN_RAW_PREFIX + image_path)
            else:
                current_post = {
                    "images": [CDN_RAW_PREFIX + image_path],
                    "caption": caption,
                    "url": url,
                    "datetime": formatted_datetime,
                }
                new_posts.append(current_post)
                previous_caption = caption
    
    # Prepend new posts to existing posts
    if new_posts:
        index[club] = new_posts + index[club]

with open("index.json", "w+", encoding='utf-8') as f:
    json.dump(index, f, indent=4)
