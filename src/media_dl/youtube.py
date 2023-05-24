from telebot import apihelper, formatting
from telebot.types import InputFile, Message
from src import constants, mongo, bot
import urllib.request
import yt_dlp
import requests
import humanize
from PIL import Image
import glob
import os


RESES = '144', '240', '360', '480', '720', '1080', '1440', '2160'
ME = -847590350


@ bot.message_handler(regexp=r'https?://.*youtu.+')
def utubelink(msg: Message):
    msgid, chatid, url = msg.message_id, msg.chat.id, msg.text
    try:
        res = mongo.reader(msg.from_user.id, "resolution")
    except KeyError:
        res = '720'

    try:
        info = url_info(url, RESES.index(res))
    except LookupError as e:
        return bot.send_message(chatid, e)

    title, vid_id = info['title'], info['id']
    thumb = f'media/{vid_id}.jpg'
    author = info['uploader']
    
    title = title_changer(title)
    files = glob.glob("./media/*")
    for f in files:
        if title in f:
            extension = f.split('.')[-1]
            break
    else:
        return bot.send_message(ME, f'{title}\n{f}')

    url1 = f'http://img.youtube.com/vi/{vid_id}/maxresdefault.jpg'
    url2 = f'http://img.youtube.com/vi/{vid_id}/0.jpg'
    thumbnail_url = url1 if requests.get(url1).status_code == 200 else url2
    urllib.request.urlretrieve(thumbnail_url, filename=f'media/{vid_id}.jpg')
    
    with open(f'media/{title}.{extension}', 'rb') as video:
        views, duration = humanize.intword(info["view_count"]), info['duration']
        caption = f'{title}\n\n👤 {author}\n👁️ {views}'
        with Image.open(thumb) as img:
            image_size = os.path.getsize(thumb)
            while image_size > 200 * 1024:
                image_size = thumb_resize(thumb)
            try:
                bot.send_chat_action(chatid, 'upload_video')
                vid_msg = bot.send_video(chatid, video, duration, img.width, img.height,
                    InputFile(thumb), caption, reply_to_message_id=msgid,
                    supports_streaming=True, timeout=500)
            except apihelper.ApiTelegramException:
                bot.send_chat_action(chatid, 'upload_video')
                vid_msg = bot.send_video(chatid, video, duration, img.width, img.height,
                    InputFile(thumb), caption, supports_streaming=True, timeout=500)
            except Exception as e:
                bot.send_message(ME, 
                    f'utube exception {e}\n{f"https://www.youtube.com/watch?v={vid_id}"}')
    if info['reduct']:
        bot.send_message(chatid, f"Video resolution lower than requested. Available format within file size limit but resolution is {info['height']} instead of {res}.\
You can change your default resolution with {formatting.hcode('/resolution')} in private chat.")
        
    bot.delete_state(vid_id, msg.from_user.id)
    constants.clean_folder([msgid, vid_id, title])
    return


def title_changer(title):
    chars = {'.': '．', '/': '⧸', '\\': '＼＼', ':': '：', '*': '＊', '?': '？', '<': '＜', '>': '＞', '|': '｜'}

    for k, v in chars.items():
        title = title.replace(k, v)
    return title


def thumb_resize(path):
    image = Image.open(path)
    image.save(path, optimize=True, quality=80)
    return os.path.getsize(path)


def url_info(url, res, reduct=False):
    ydl_opts = {'ext': 'mp4',
                'format': f'bestvideo[height<={RESES[res]}]+bestaudio/best[height<={RESES[res]}]',
                'outtmpl': 'media/%(title)s.%(ext)s'}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        while info['filesize_approx'] > 52000000:
            if res == 0:
                raise apihelper.ApiException("No compatible format found within the file size limit of 50MB.")
            return url_info(url, res - 1, True)
        if info['availability'] != 'public':
            condition = info['availability'] if info['availability'] == 'needs_auth' else f'is {info["availability"]}'
            raise LookupError(f"This video {condition.replace('_', ' ')}")
        ydl.download([url])
        info['reduct'] = reduct
        return info


@bot.message_handler(commands=['resolution'], chat_types=["private"])
def res_change(msg: Message):
    try:
        res = mongo.reader(msg.from_user.id, "resolution")
    except KeyError:
        res = '720'
    bot.send_message(msg.chat.id, f'Please select a preset resolution for downloading YouTube videos.\nCurrent resolution: {res}',
                     reply_markup=constants.keyboard([i for i in RESES], 4))
    bot.set_state(msg.from_user.id, constants.MyStates.res, msg.chat.id)
    

@bot.message_handler(state=constants.MyStates.res)
def res_chosed(msg):
    mongo.DB.users.update_one({"id": msg.from_user.id}, {"$set": {"resolution": msg.text}}, upsert=True)
    bot.send_message(msg.chat.id, f"Your default resolution for downloading YouTube videos succesfully changed to {msg.text}!")