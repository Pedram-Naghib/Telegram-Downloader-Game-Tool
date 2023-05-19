from telebot import formatting, apihelper
from telebot.types import InputFile, Message
from src import constants, mongo, bot
import urllib.request
import yt_dlp
import requests
import subprocess
import humanize
from PIL import Image
import os.path


RESES = '144p', '240p', '360p', '480p', '720p', '1080p', '1440p', '2160p', 'audio', 'cancel'
ME = -847590350

@ bot.message_handler(regexp=r'https?://.*youtu.+')
def youtube_handler(msg: Message):
    chatid = msg.chat.id
    url = msg.text
    ydl_opts = {'paths': {'home': 'media/'}, 'ext': 'mp4'}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        # ℹ️ ydl.sanitize_info makes the info json-serializable
        # data: dict = json.dumps(ydl.sanitize_info(info))

        if info['availability'] != 'public':
            condition = info['availability'] if info['availability'] == 'needs_auth' else f'is {info["availability"]}'
            return bot.send_message(chatid, f"This video {condition.replace('_', ' ')}")
    vid_id = info['id']
    url1 = f'http://img.youtube.com/vi/{vid_id}/maxresdefault.jpg'
    url2 = f'http://img.youtube.com/vi/{vid_id}/0.jpg'
    thumbnail_url = url1 if requests.get(url1).status_code == 200 else url2
    thumb_ql = thumbnail_url.split('/')[-1][:-4]
    
    avail_reses = {}
    w_audio = set()
    no_audio = set()
    for i in info.get('formats', None):
        if i.get('filesize', None) and i['video_ext']  == 'mp4' and i['format_note'] in RESES:
            # print(f'{i} \n\n')
            if i['acodec'] != 'none':
                w_audio.add(f"{i['format_note']} {i['filesize']} {i['format_id']}")
            else:
                no_audio.add(f"{i['format_note']} {i['filesize']} {i['format_id']}")
    # no_audio = no_audio.union(w_audio)
    for i in w_audio:
        res, format_id = i.split(' ')[0], i.split(' ')[2]
        vidsize = humanize.naturalsize(i.split(' ')[1])
        if int(i.split(' ')[1]) + aud < 50000000:
            avail_reses[f'{res} ({vidsize})'] = f'{res} {vid_id} {thumb_ql} {format_id} {True}'

    for i in no_audio:
        res, format_id = i.split(' ')[0], i.split(' ')[2]
        aud = audio_extract([url], title_changer(info['title']))
        vidsize = humanize.naturalsize(int(i.split(' ')[1]) + aud)
        if int(i.split(' ')[1]) + aud < 50000000:
            avail_reses[f'{res} ({vidsize})'] = f'{res} {vid_id} {thumb_ql} {format_id} {False}'

    avail_reses = {k: avail_reses[k] for k in sorted(avail_reses, key=lambda x: int((x.split(' ')[0]).rstrip('p')))}
    value_dta = f'{vid_id} {thumb_ql} None None'
    avail_reses.update({'Audio 🎵': f'audio {value_dta}', f'Cancel ❌': f'cancel {value_dta}'})
    
    # send thumbnail + ask for desired resolution
    choose = bot.send_photo(
        chatid, reply_to_message_id=msg.message_id, photo=thumbnail_url,
        reply_markup=constants.inline_markup(avail_reses, 2))

    mongo.DB.users.update_one({'id': chatid}, {
        '$set': {'choose.' + f'{msg.message_id}': choose.message_id}}, upsert=True)


@ bot.callback_query_handler(func=None, validator=RESES, is_sender=True)
def utubelink(call: Message):
    print(call.data)
    msgid = call.message.reply_to_message.message_id
    chatid = call.message.chat.id
    res, vid_id, thumb_ql, format_id, acodec = call.data.split()
    chooseid = mongo.reader(chatid, 'choose')[str(msgid)]
    
    url = f'https://www.youtube.com/watch?v={vid_id}'
    ydl_opts = {'paths': {'home': 'media/'}, 'ext': 'mp4'}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
    title = info['title']
    thumbnail_url = f'http://img.youtube.com/vi/{vid_id}/{thumb_ql}.jpg'

    if res == 'cancel':
        bot.delete_message(chatid, chooseid)
        constants.clean_folder(title_changer(title))
        return
    urllib.request.urlretrieve(thumbnail_url, filename=f'media/{vid_id}.jpg')
    thumb = f'media/{vid_id}.jpg'
    author = info['uploader']
    name = title_changer(title)
    if res == 'audio':
        if not os.path.exists(f'media/{title}.m4a'):
            audio_size = audio_extract([url], title_changer(info['title']))
        else:
            audio_size = os.path.getsize(f'media/{title}.m4a')

        mongo.DB.users.update_many({'id': chatid}, {'$set':
            {'tuid': vid_id, 'duration': info['duration'], 'Utitle': title, 'author': author,
             'filename': name}}, upsert=True)

        size = constants.byteconv(audio_size)
        hcode = formatting.hcode
        caption = constants.audio_cc(hcode(title), hcode(author), hcode(size))
        
        change = bot.edit_message_caption(caption, chatid, chooseid,
        reply_markup=constants.inline_markup(
            {'Get the audio': f'chudio c-{msgid}',
                "Change audio's name/artist": f'chudio-{msgid}'}, 1))

        msgid2 = change.message_id

        mongo.DB.users.update_one(
            {'id': call.from_user.id}, {'$set': {'change.' + f'{msgid}': msgid2}}, upsert=True)
        return

    subprocess.run(['yt-dlp', '-f', format_id, '-o', f'media/{msgid}.mp4', url], stdout=subprocess.PIPE)
    f_name = msgid
    if acodec == 'False':
        if not os.path.exists(f'media/{name}.m4a'):
            audio_extract([url], name)
        subprocess.run(['ffmpeg', '-i', f'media/{msgid}.mp4', '-i', f'media/{name}.m4a', '-c:v',
                    'copy', '-c:a', 'aac', f'media/{vid_id}.mp4'], stdout=subprocess.PIPE)
        f_name = vid_id
    
    with open(f'media/{f_name}.mp4', 'rb') as video:
        views, duration = humanize.intword(info["view_count"]), info['duration']
        caption = f'{title}\n\n👤 {author}\n👁️ {views}'
        with Image.open(thumb) as img:
            try:
                bot.send_chat_action(chatid, 'upload_video')
                bot.send_video(chatid, video, duration, img.width, img.height,
                    InputFile(thumb), caption, reply_to_message_id=msgid,
                    supports_streaming=True, timeout=500)
            except apihelper.ApiTelegramException:
                bot.send_chat_action(chatid, 'upload_video')
                bot.send_video(chatid, video, duration, img.width, img.height,
                    InputFile(thumb), caption, supports_streaming=True, timeout=500)
            except Exception as e:
                bot.send_message(ME, 
                    f'utube exception {e}\n{f"https://www.youtube.com/watch?v={vid_id}"}')
        
    bot.delete_state(vid_id, call.from_user.id)
    constants.clean_folder([msgid, vid_id, name])
    bot.delete_message(chatid, chooseid)
    mongo.DB.users.update_one({'id': call.from_user.id}, {'$unset': {f'choose.{msgid}': 0}})
    return


def audio_extract(URL: list, title):
    ydl_opts = {
        'format': 'm4a/bestaudio/best',
        'outtmpl': f'media/{title}',
        # ℹ️ See help(yt_dlp.postprocessor) for a list of available Postprocessors and their arguments
        'postprocessors': [{  # Extract audio using ffmpeg
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'm4a',
        }]
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        return ydl.extract_info(URL[0], download=True)['filesize']
    
def title_changer(title):
    chars = ['.', '/', '\\', ':', '*', '?', '<', '>']

    for char in chars:
        title = title.replace(char, ' ')
    return title