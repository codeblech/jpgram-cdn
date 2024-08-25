# JPGram CDN
Here lies the posts thee shall receive.


## How to update image cache?
Run the `update.sh` script while in root directory of the repository.

You also have to provide a dummy instagram account (to scrape).

Create a file named `secrets.env` as such in the root directory (it is gitignored so you don't need to worry) 
```.env
JPGRAM_IG_ID=username
JPGRAM_IG_PSWD=password
```

Now, you can run the script `bash update.sh`

If you don't want to create a secrets file then you can provide the variable while running the script as such 
```console
JPGRAM_IG_ID=username JPGRAM_IG_PSWD=password bash update.sh
```
but this can be a security concern if your shell saves command history.



After the script is done. The changes have already been staged and commited to the repository. You can push and create a PR (this will be done by the script as well in the future)                                                
