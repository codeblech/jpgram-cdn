import os
import json
from datetime import datetime

CDN_RAW_PREFIX = "https://raw.githubusercontent.com/codeblech/jpgram-cdn/main/"
ROOT = "images"

index = {}

for club in os.listdir(ROOT):
    club_path = os.path.join(ROOT, club)
    if not os.path.isdir(club_path):
        continue

    index[club] = []
    previous_caption = None
    current_post = None

    for filename in sorted(os.listdir(club_path), reverse=True):
        if filename.endswith((".webp", ".jpg", ".jpeg", ".png")):
            image_path = os.path.join(ROOT, club, filename)
            datetime_str = filename.split("_UTC")[0]
            try:
                image_datetime = datetime.strptime(
                    datetime_str, "%Y-%m-%d_%H-%M-%S"
                )
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
                index[club].append(current_post)
                previous_caption = caption

with open("index.json", "w+", encoding='utf-8') as f:
    json.dump(index, f, indent=4)
