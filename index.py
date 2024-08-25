import os
import json
from datetime import datetime

ROOT = "images"

index = {}

for club in os.listdir(ROOT):
    club_path = os.path.join(ROOT, club)
    if not os.path.isdir(club_path):
        continue

    index[club] = []
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

            if os.path.exists(caption_path):
                with open(caption_path) as f:
                    caption = f.read().strip()


            index[club].append(
                    {
                        "image": image_path,
                        "caption": caption,
                        "datetime": formatted_datetime,
                    }
            )




with open("index.json", "w+") as f:
    json.dump(index, f)
