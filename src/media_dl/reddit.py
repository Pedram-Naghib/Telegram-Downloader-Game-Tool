import requests
from src import reddit_config, bot
from src.media_tools import vid_dl
import urllib.request
import re


@bot.message_handler(regexp=r"https?://[www.]*reddit\.com/r/.+/comments/.+/.+")
def send_reddit(msg):
    url = re.findall(r"reddit\.com/r/.+/comments/.+/.+/", msg.text)
    url = f"https://oauth.{url[0]}"
    chatid = msg.chat.id

    res = requests.get(url, headers=reddit_config())
    post = res.json()[0]["data"]["children"]
    postid = post[0]["kind"] + "_" + post[0]["data"]["id"]
    data = post[0]["data"]
    title = data["title"]
    duration = data["media"]["reddit_video"]["duration"]

    try:
        dims = dimensions(data, postid)
        dims["duration"] = duration
    except (urllib.error.HTTPError, ValueError):
        dims = None
    
    if (
        data["is_reddit_media_domain"]
        and "video" in data["post_hint"]
    ):
        url4 = data["secure_media"]["reddit_video"]["fallback_url"]
        url3 = re.sub(r"(1080|720|480|360|240)", "audio", url4)

        try:
            vid_dl(url4, url3, chatid, postid, title, dims)
        except Exception as e:
            bot.send_message(chatid, f"Reddit video could not be sent!\n{e}")
    elif data["secure_media"]:
        try:
            url = data["secure_media"]["oembed"]["thumbnail_url"].replace(
                "jpg", "mp4"
            )
            bot.send_message(chatid, f"{title}\n{url}")

        except:
            bot.send_message(chatid, f"Reddit video could not be sent!\n{e}")
    else:
        url = data["url_overridden_by_dest"]
        vid_dl(url, None, chatid, postid, title, dims)


def dimensions(post, postid):
    with open(f'media/{postid}.jpg', 'wb') as f:
        f.write(urllib.request.urlopen(post['thumbnail']).read())
    return {'thumb': f'media/{postid}.jpg',
            'h': post['media']['reddit_video']['height'],
            'w': post['media']['reddit_video']['width']}
