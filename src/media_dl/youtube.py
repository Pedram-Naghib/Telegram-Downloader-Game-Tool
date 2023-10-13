from telebot import apihelper, formatting
from telebot.types import InputFile, Message, ReplyKeyboardRemove
from src import constants, mongo, bot
import urllib.request
import yt_dlp
import requests
import humanize
from PIL import Image
import os
import re


RESES = '144', '240', '360', '480', '720', '1080', '1440', '2160'


@bot.message_handler(commands=['a'])
def audio_extract(msg: Message):
    bot.send_chat_action(msg.chat.id, 'upload_document')
    URL = []
    if len(msg.text.split(' ')) > 1:
        URL = re.findall(r'https?://.*youtu\S+', msg.text)
    else:
        try:
            if txt := msg.reply_to_message.text:
                URL = re.findall(r'https?://.*youtu\S+', txt)
        except:
            return bot.send_message(msg.chat.id, f"Wrong command arguments. Correct example: {formatting.hcode('/a <youtube link>')} - or reply the command to a youtube link.")
    if not URL:
        return bot.send_message(msg.chat.id, f"Wrong command arguments. Correct example: {formatting.hcode('/a <youtube link>')} - or reply the command to a youtube link.")
    ydl_opts = {
        'format': 'm4a/bestaudio/best',
        'outtmpl': f'media/%(title)s.%(ext)s',
        # ℹ️ See help(yt_dlp.postprocessor) for a list of available Postprocessors and their arguments
        'postprocessors': [{  # Extract audio using ffmpeg
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3', # m4a
        }]
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        # ydl.download([URL])
        info = ydl.extract_info(URL[0], download=True)
        title, author, vidid = info['title'], info['uploader'], info['id']
        thumb_dl(vidid)
        with open(f"media/{title_changer((title))}.mp3", "rb") as aud:
            bot.send_audio(msg.chat.id, aud, '@HumbanBot', info['duration'], author, title,
                thumb=InputFile(f"media/{vidid}.jpg"))
        # Clean media directory from processed files.
        constants.clean_folder([title, vidid])


@ bot.message_handler(regexp=r'https?://.*youtu\S+')
def utubelink(msg: Message, def_res=None):
    msgid, chatid, url = msg.message_id, msg.chat.id, msg.text
    bot.send_chat_action(chatid, 'upload_video')
    resol = mongo.reader(msg.from_user.id, "resolution", '720')
    res = def_res if def_res else resol
    res_index = RESES.index(res)

    try:
        info = url_info(url, res_index)
    except LookupError as e:
        return bot.send_message(chatid, e)
    except Exception as e:
        return bot.send_message(chatid, e)
    
    bot.send_chat_action(chatid, 'upload_video')

    title, vid_id = info['title'], info['id']
    thumb = f'media/{vid_id}.jpg'
    author = info['uploader']
    
    title = title_changer(title)
    print('changed title')
    thumb_dl(vid_id)
    print('opening...')
    with open(f'media/{title}.mp4', 'rb') as video:
        print('opened!')
        views, duration = humanize.intword(info["view_count"]), info['duration']
        caption = f'{title}\n\n👤 {author}\n👁️ {views}'
        with Image.open(thumb) as img:
            try:
                print('sending...')
                bot.send_chat_action(chatid, 'upload_video')
                bot.send_video(chatid, video, duration, img.width, img.height,
                    InputFile(thumb), caption, supports_streaming=True, timeout=500)
            except Exception as e:
                if res == '144':
                    bot.send_message(chatid, "Your video exceeds the maximum allowed size of 50MB, and no available resolution matches this limit.")
                else:
                    bot.send_message(chatid, "Your video exceeds the maximum allowed size of 50MB. To send the video successfully, please reduce the resolution.")

    if def_res:
        bot.send_message(msg.chat.id, f"Video resolution changed from {resol} to {def_res} because of 50Mb size limit.\
/nYou can change your default resolution with /resolution in bot's chat.")

    bot.delete_state(vid_id, msg.from_user.id)
    constants.clean_folder([msgid, vid_id, title])
    return


def title_changer(title):
    chars = {'/': '⧸', '\\': '＼＼', ':': '：', '*': '＊', '?': '？', '<': '＜', '>': '＞', '|': '｜'} # '.': '．', 

    for k, v in chars.items():
        if k in title:
            title = title.replace(k, v)
    return title


def thumb_resize(path):
    image = Image.open(path)
    image.save(path, optimize=True, quality=70)
    return os.path.getsize(path)


def url_info(url, res_index):
    ydl_opts = {
        'format': f'bestvideo[ext=mp4][height<={RESES[res_index]}]+bestaudio[ext=m4a]/best[ext=mp4][height<={RESES[res_index]}]',
        'outtmpl': 'media/%(title)s.%(ext)s'
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        while info['filesize_approx'] > 52000000:
            if res_index == 0:
                raise apihelper.ApiException("No compatible format found within the file size limit of 50MB.")
            return url_info(url, res_index - 1)
        if info['availability'] != 'public':
            condition = info['availability'] if info['availability'] == 'needs_auth' else f'is {info["availability"]}'
            raise LookupError(f"This video {condition.replace('_', ' ')}")
        ydl.download([url])
        return info


@bot.message_handler(commands=['resolution'], chat_types=["private"])
def res_change(msg: Message):
    res = mongo.reader(msg.from_user.id, "resolution", "720")
    bot.set_state(msg.from_user.id, constants.MyStates.res, msg.chat.id)
    bot.send_message(msg.chat.id, f'Please select a preset resolution for downloading YouTube videos.\nCurrent resolution: {res}',
                     reply_markup=constants.keyboard([i for i in RESES], 4))
    

@bot.message_handler(state=constants.MyStates.res)
def res_chosed(msg):
    mongo.DB.users.update_one({"id": msg.from_user.id}, {"$set": {"resolution": msg.text}}, upsert=True)
    bot.send_message(msg.chat.id, f"Your default resolution for downloading YouTube videos succesfully changed to {msg.text}!",
                     reply_markup=ReplyKeyboardRemove())
    bot.delete_state(msg.from_user.id, msg.chat.id)


def thumb_dl(vid_id):
    url1 = f'http://img.youtube.com/vi/{vid_id}/maxresdefault.jpg'
    url2 = f'http://img.youtube.com/vi/{vid_id}/0.jpg'
    thumbnail_url = url1 if requests.get(url1).status_code == 200 else url2
    urllib.request.urlretrieve(thumbnail_url, filename=f'media/{vid_id}.jpg')
    image_size = os.path.getsize(f'media/{vid_id}.jpg')
    while image_size > 200 * 1024:
        image_size = thumb_resize(f'media/{vid_id}.jpg')