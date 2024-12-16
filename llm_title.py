import json
import os
import time
from datetime import datetime
from groq import Groq
import argparse

# Define the dictionary with Instagram handles and corresponding club names
club_dict = {
    "cice_jiit": "CICE",
    "crescendojiit": "Crescendo",
    "gdscjiit": "GDSC JIIT",
    "jaypee.photo.enthusiasts.guild": "Jaypee Photo Enthusiasts Guild",
    "jhankaarjiit": "Jhankaar",
    "jiit.impressions": "Impressions",
    "jiityouthclub": "JIIT Youth Club",
    "knuth_jiit": "Knuth",
    "nssjiit62": "NSS JIIT",
    "osdcjiit": "OSDC JIIT",
    "parola.literaryhub": "Parola Literary Hub",
    "radiance.hub": "Radiance Hub",
    "thejaypeedebsoc": "The Jaypee DebSoc",
    "thepageturnersociety": "The Page Turner Society",
    "thethespiancircle": "The Thespian Circle",
    "ucrjiit": "UCR JIIT",
}

def get_title_from_groqcloud(caption, club_name):
    API = "generate from console.groq.com"
    client = Groq(api_key=API)
    
    system_message = f'An instagram post has been made by the "{club_name}". The caption will be provided by the user. You will make a suitable title for the post highlighting what it is about. (Example: Fest 2k24 Intro, New CS Session, Farewell 2023, Rakshabandhan Wishes, Important Announcement, Winners Announced, etc.). It should focus on the primary objective of the post, and should make it clear what the post is about. No need to mention the club name. Give single output in JSON within header "title" for every post. It shouldn\'t be longer than 5 words (ideally 3/4). No need to mention {club_name}.'
    
    while True:
        try:
            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": system_message,
                    },
                    {
                        "role": "user",
                        "content": caption,
                    }
                ],
                response_format={"type": "json_object"},
                model="llama-3.3-70b-versatile",
            )
            response = chat_completion.choices[0].message.content
            title_json = json.loads(response)
            return title_json.get("title")
        except Exception as e:
            if hasattr(e, 'response') and e.response.status_code == 429:
                print("429 Too Many Requests: Retrying after 10 seconds...")
                time.sleep(10)
            else:
                raise

def update_posts_with_titles(date, club, overwrite):
    if date == "*":
        all_dates = True
    else:
        all_dates = False
        target_date = datetime.strptime(date, "%d/%m/%y")
    updated_data = {}

    with open('index.json', 'r') as f:
        data = json.load(f)
        for handle, posts in data.items():
            if club == "*" or handle == club:
                count = 0
                print("working on club: ", handle)
                updated_posts = []
                for post in posts:
                    post_date = datetime.strptime(post['datetime'], "%B %d, %Y")
                    if (all_dates or post_date >= target_date) and (overwrite or "title" not in post.keys()):
                        caption = post['caption']
                        club_name = club_dict.get(handle, "Unknown Club")
                        title = get_title_from_groqcloud(caption, club_name)
                        count += 1
                        post['title'] = title
                        print("posts updated: ", count)
                    updated_posts.append(post)
                print("Total posts updated of ", handle, ": ", count)
                updated_data[handle] = updated_posts

                # Write the updated data to index.json after processing each club
                with open('index.json', 'w') as f:
                    json.dump(updated_data, f, indent=4)
            else:
                updated_data[handle] = posts

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Update Instagram post titles.")
    parser.add_argument("date", nargs="?", default="*", help="Date in format dd/mm/yy. Use * for all dates.")
    parser.add_argument("club", nargs="?", default="*", help="Instagram handle of the club. Use * for all clubs.")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing titles.")
    args = parser.parse_args()

    update_posts_with_titles(args.date, args.club, args.overwrite)