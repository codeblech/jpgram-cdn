#!/usr/bin/bash

PWD="$(pwd)"
RED='\033[1;31m'
NC='\033[0m'
LOGIN=0

if [ "$1" = "login" ];
then
  LOGIN=1
fi


cd "$(dirname "$0")"

if [ -f secrets.env ]; then
  source secrets.env
else
  printf "${RED}ERROR${NC}: secrets.env file not found.\n" >&2
  read -p "Press any key to exit..."
  exit 1
fi

if [ $LOGIN -eq 1 ];
then
 if [ -z "${JPGRAM_IG_ID}" ] || [ -z "${JPGRAM_IG_PSWD}" ];
  then
    printf "${RED}ERROR${NC}: JPGRAM_IG_ID or JPGRAM_IG_PSWD env are not provided.\n" >&2
    exit 1
  fi
fi

printf "Pulling remote changes from github...\n"
git pull

mkdir -p images && cd images

printf "Caching images... (this will take a few minutes)\n(To check instaloader output enter 'tail -f images/instaloader.log' in a seperate terminal)\n"

if [ $LOGIN -eq 1 ];
then
  python3 -m instaloader +../clubs.txt --latest-stamps latest-stamps.ini --no-videos --no-metadata-json --post-metadata-txt="https://www.instagram.com/p/{shortcode}/|||{caption}" --login $JPGRAM_IG_ID --password $JPGRAM_IG_PSWD 2> instaloader.log >&2
else
  python3 -m instaloader +../clubs.txt --latest-stamps latest-stamps.ini --no-videos --no-metadata-json --post-metadata-txt="https://www.instagram.com/p/{shortcode}/|||{caption}" 2> instaloader.log >&2
fi

# Generating indices
cd ..
printf "Generating indices... "
python3 ./index.py
printf "Index generated.\n"
printf "Adding LLM title to the index...\n"
python3 ./llm_title.py
printf "Added LLM title\n"

if [ $? -ne 0 ]
then
  printf "${RED}ERROR${NC}: Cache Updation was unsuccessful. Any changes were not commited and left as it is. Check instaloader.log for furthur details.\n" >&2
  read -p "Do you still want to commit the changes? " -n 1 -r
  echo    # (optional) move to a new line
  if [[ ! $REPLY =~ ^[Yy]$ ]]
  then
    exit 1
  fi
fi

printf "Commiting changes... "
git add images/ index.json
git commit -m "chore: update image cache ($(date "+%Y-%m-%d--%H-%M-%S"))"
git push

printf "done.\n"
read -p "Press any key to exit..."
