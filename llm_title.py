import json
import time
import argparse
from datetime import datetime

from groq import Groq
import google.generativeai as genai
from google.ai.generativelanguage_v1beta.types import content
from google.api_core import exceptions

import os
from dotenv import load_dotenv

load_dotenv('secrets.env')

# Check if GROQ_API_KEY is set
if 'GROQ_API_KEY' not in os.environ:
    raise ValueError("GROQ_API_KEY environment variable not set")

# Define the dictionary with Instagram handles and corresponding club names
club_dict = {
    "cice_jiit": "CICE",
    "crescendojiit": "Crescendo",
    "dscjiit": "DSC JIIT",
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

def estimate_tokens(text):
    # Simple estimation: 1 token per 4 characters
    return int(len(text)/4)

def get_titles_from_groqcloud(captions, club_name, client):
    system_message = f'''A series of Instagram posts have been made by "{club_name}". For each caption provided by the user, generate a suitable title that highlights what the post is about. Each title should focus on the primary objective of the post and make it clear what the post is about. Titles should not include the club name, and should not be longer than 5 words (ideally 3/4). Each caption should have it's corresponding caption, regardless of it's duplicate or same.

Provide the titles in a JSON object with key "titles", where each title corresponds to the caption in the same position in the captions list. For example:
{{"titles": ["Title for post 1", "Title for post 2", ...]}}
'''
    tokens_system = estimate_tokens(system_message)
    error_count = 0
    # Split captions into batches of up to 20 posts
    max_captions_per_api_call = 20
    batch = []
    all_titles = []
    i=-1
    while True:
        i+=1
        if(i==len(captions)):
            break
        caption=captions[i]
        batch.append(caption)
        
        # Get remaining tokens
        rate_limit = client.rate_limit if hasattr(client, 'rate_limit') else {}
        remaining_tokens = int(rate_limit.get('x-ratelimit-remaining-tokens', 6000)) #tokens per minute

        if (len(batch) > max_captions_per_api_call) or (tokens_system + estimate_tokens(' '.join(batch)) + 500) > remaining_tokens or i==len(captions)-1:
            if((len(batch) > max_captions_per_api_call) or (tokens_system + estimate_tokens(' '.join(batch)) + 500) > remaining_tokens):
                batch.pop()
                i-=1

            while True:
                try:
                    chat_completion = client.chat.completions.create(
                        messages=[
                            {
                                "role": "system",
                                "content": system_message+". There should be exactly "+str(len(batch))+" titles in the response.",
                            },
                            {
                                "role": "user",
                                "content": json.dumps({"captions": batch}),
                            }
                        ],
                        response_format={"type": "json_object"},
                        model="llama-3.3-70b-versatile",
                    )
                    response = chat_completion.choices[0].message.content

                    titles_json = json.loads(response)
                    if 'titles' in titles_json and len(titles_json['titles']) == len(batch):
                        all_titles.extend(titles_json['titles'])
                        print("Titles generated:", len(titles_json['titles']), "Total:", len(all_titles))
                        error_count = 0
                        batch=[]
                        break
                    else:
                        error_count += 1
                        print("Invalid JSON format or incorrect number of titles. Retrying...", len(titles_json['titles']), len(batch))
                        if error_count > 1:
                            removed_elements = len(batch) // 2
                            batch = batch[:len(batch) - removed_elements]
                            i -= removed_elements
                            error_count = 0
                except Exception as e:
                    if hasattr(e, 'response') and e.response.status_code == 429:
                        retry_after = e.response.headers.get('retry-after')
                        if retry_after is not None:
                            retry_after = int(float(retry_after))
                        else:
                            retry_after = 10  # Default retry after 10 seconds if header is missing
                        print(f"429 Too Many Requests: Retrying after {retry_after} seconds...")
                        time.sleep(retry_after)
                    else:
                        
                        print(e)
                        raise
    return all_titles   

def get_titles_from_genai(captions, club_name, generation_config):
    system_message = f'''A series of Instagram posts have been made by "{club_name}". For each caption provided by the user, you are supposed to write a suitable title that highlights what the post is about. Each title should focus on the primary objective of the post and make it clear what the post is about. Titles should not include the club name, and should not be longer than 5 words (ideally 3/4). Each caption should have it's corresponding caption, regardless of it's duplicate or same.

Provide the titles in a JSON object with key "titles", where each title corresponds to the caption in the same position in the captions list. For example:
{{"titles": ["Title for post 1", "Title for post 2", ...]}}. Each caption is seperated by the identifier '|||=|||'. Ensure that the titles are in the same sequence as the captions.
'''
    model = genai.GenerativeModel(
            model_name="gemini-2.0-flash-exp",
            generation_config=generation_config,
            system_instruction=system_message,
        )

    all_titles = []
    batch_size = 20
    max_retries = 5
    init_retry_delay = 10
    for i in range(0, len(captions), batch_size):
        chat_session = model.start_chat(
            history=[]
        )
        batch = captions[i:i+batch_size]
        batch_prompt = '\n|||=|||\n'.join(batch)
        retries=0
        retry_delay = init_retry_delay
        while retries <= max_retries:
            try:
                batch_response = chat_session.send_message(batch_prompt)
                batch_titles = json.loads(batch_response.text)['titles']
                all_titles.extend(batch_titles)
                print("Titles generated:", len(batch_titles), "Total:", len(all_titles))
                break
            except exceptions.TooManyRequests as e:
                retries += 1
                print(f"Rate limit hit. Retrying in {retry_delay} seconds... (Attempt {retries}/{max_retries})")
                time.sleep(retry_delay)
                retry_delay *= 2 # Exponential backoff
            except Exception as e: # catch other exceptions
                print(f"An unexpected error has occured. {e}")
                raise e
        
        
    return all_titles

def parse_time_to_seconds(time_str):
    # Converts time format like '2m59.56s' to total seconds
    if 'm' in time_str:
        mins, secs = time_str.split('m')
        secs = secs.replace('s', '')
        total_seconds = int(mins) * 60 + float(secs)
    else:
        total_seconds = float(time_str.replace('s', ''))
    return total_seconds

def update_posts_with_titles(date, club, overwrite, api_source):
    API = os.getenv("GROQ_API_KEY")
    if not API:
        raise ValueError("GROQ_API_KEY environment variable not set")
    
    if api_source == "groqcloud":
        client = Groq(api_key=API)
    elif api_source == "genai":
        genai.configure(api_key=os.environ['GENAI_API_KEY'])
        # Create the model
        generation_config = {
        "temperature": 1,
        "top_p": 0.95,
        "top_k": 40,
        "max_output_tokens": 8192,
        "response_schema": content.Schema(
            type = content.Type.OBJECT,
            enum = [],
            required = ["titles"],
            properties = {
            "titles": content.Schema(
                type = content.Type.ARRAY,
                items = content.Schema(
                type = content.Type.STRING,
                ),
            ),
            },
        ),
        "response_mime_type": "application/json",
        }
        
    
    # Load existing data
    with open('index.json', 'r') as f:
        data = json.load(f)
    
    if date in "*":
        all_dates = True
    else:
        all_dates = False
        target_date = datetime.strptime(date, "%d/%m/%y")

    # Process clubs while maintaining all existing data
    for handle, posts in data.items():
        if club == "*" or handle == club:
            print("Working on club:", handle)
            captions_to_update = []
            indices_to_update = []
            
            for idx, post in enumerate(posts):
                post_date = datetime.strptime(post['datetime'], "%B %d, %Y")
                if (all_dates or post_date >= target_date) and (overwrite or "title" not in post):
                    if post['caption'].strip().lower() not in ["no caption available", "", "no caption"]:
                        captions_to_update.append(post['caption'])
                        indices_to_update.append(idx)
            
            if captions_to_update:
                club_name = club_dict.get(handle, "Unknown Club")
                if api_source == "groqcloud":
                    titles = get_titles_from_groqcloud(captions_to_update, club_name, client)
                elif api_source == "genai":
                    titles = get_titles_from_genai(captions_to_update, club_name, generation_config)
                for idx, title in zip(indices_to_update, titles):
                    posts[idx]['title'] = title
                print(f"Total posts updated for {handle}: {len(indices_to_update)}")
                
                # Save after each club update
                with open('index.json', 'w') as f:
                    json.dump(data, f, indent=4)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Update Instagram post titles.")
    parser.add_argument("date", nargs="?", default="*", help="Date in format dd/mm/yy. Use * for all dates.")
    parser.add_argument("club", nargs="?", default="*", help="Instagram handle of the club. Use * for all clubs.")
    parser.add_argument("api_source", default="groqcloud", help="Api source. Supported values: groqcloud, genai")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing titles.")
    args = parser.parse_args()

    update_posts_with_titles(args.date, args.club, args.overwrite, args.api_source)