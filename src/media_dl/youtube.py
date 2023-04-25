from pytube import YouTube
import pytube.exceptions as exception
import pytube.extract as extract
import backoff
from telebot import formatting, apihelper
from telebot.types import InputFile, Message
from src import constants, mongo, bot
import urllib.request
import requests
import subprocess
import humanize
from PIL import Image


RESES = '144p', '240p', '360p', '480p', '720p', '1080p', '1440p', '2160p', 'audio', 'cancel'
ME = -847590350

@ bot.message_handler(regexp=r'https?://.*youtu.+')
def youtube_handler(msg: Message):
    chatid = msg.chat.id
    url = msg.text
    try:
        try:
            utube = YouTube(url)
        except:
            return bot.reply_to(msg, 'Invalid URL! Please check the link and then try again.')
        utube.check_availability()
    except Exception as e:
        _, ext_msg = extract.playability_status(utube.watch_html)
        return bot.reply_to(msg, ''.join(ext_msg))
    
    vid_id = utube.video_id
    url1 = f'http://img.youtube.com/vi/{vid_id}/maxresdefault.jpg'
    url2 = f'http://img.youtube.com/vi/{vid_id}/0.jpg'
    thumbnail_url = url1 if requests.get(url1).status_code == 200 else url2
    thumb_ql = thumbnail_url.split('/')[-1][:-4]
    
    avail_reses = {}
    for res in RESES:
        prog = utube.streams.get_by_resolution(res)
        noneprog = utube.streams.filter(mime_type='video/mp4', res=res, progressive=False)
        if not any([prog, noneprog]):
            continue
        if prog:
            vidsize = humanize.naturalsize(prog.filesize)
            sizesplit = vidsize.split(' ')
                
        elif noneprog:
            vid = noneprog[-1]
            aud = utube.streams.filter(mime_type="audio/mp4", adaptive=True)[-1]
            vidsize = humanize.naturalsize(vid.filesize + aud.filesize)
            sizesplit = vidsize.split(' ')
            
        if sizesplit[1] == 'kB' or float(sizesplit[0]) < 50.0:
            avail_reses[f'{res} ({vidsize})'] = f'{res} {vid_id} {thumb_ql}'
                
    avail_reses.update({'mp3 🎵': f'audio {vid_id} {thumb_ql}', f'Cancel ❌': f'cancel {vid_id} {thumb_ql}'})
    
    # send thumbnail + ask for desired resolution
    choose = bot.send_photo(
        chatid, reply_to_message_id=msg.message_id, photo=thumbnail_url,
        reply_markup=constants.inline_markup(avail_reses, 2))

    mongo.DB.users.update_one({'id': chatid}, {
        '$set': {'choose.' + f'{msg.message_id}': choose.message_id}}, upsert=True)


@ bot.callback_query_handler(func=None, validator=RESES, is_sender=True)
@ backoff.on_exception(backoff.expo, (KeyError, exception.PytubeError, ValueError), max_time=60)
def utubelink(call: Message):

    msgid = call.message.reply_to_message.message_id
    chatid = call.message.chat.id
    res, vid_id, thumb_ql = call.data.split()
    chooseid = mongo.reader(chatid, 'choose')[str(msgid)]
        
    utube = YouTube(f'https://www.youtube.com/watch?v={vid_id}')
    title = utube.title
    thumbnail_url = f'http://img.youtube.com/vi/{vid_id}/{thumb_ql}.jpg'

    if res == 'cancel':
        bot.delete_message(chatid, chooseid)
        return
    
    vidata = {'author': utube.author, 'des': utube.description, 'audio': f'{title}.mp3',
    'channel_url': utube.channel_url, 'views': utube.views, 'video': f'{msgid}.mp4', 'thumb': utube.thumbnail_url}
    urllib.request.urlretrieve(thumbnail_url, filename=f'media/{vid_id}.jpg')
    thumb = f'media/{vid_id}.jpg'
    
    author = vidata['author']

    if res == 'audio':
        audio = utube.streams.get_audio_only()
        chars = ['.', '/', '\\', ':', '*', '?', '<', '>']

        for char in chars:
            title = title.replace(char, ' ')
        name = title
        try:
            audio.download(output_path='media/', filename=f'{title}.mp3')
        except Exception as e: #! which except?
            audio.download(output_path='media/', filename=f'{vid_id}.mp3')
            name = vid_id
           
        mongo.DB.users.update_many({'id': chatid}, {'$set':
            {'tuid': vid_id, 'duration': utube.length, 'Utitle': title, 'author': author,
             'filename': name}}, upsert=True)

        size = constants.byteconv(audio.filesize)
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
        

    vid = utube.streams.get_by_resolution(res)
    if vid:
        vid.download(output_path='media/', filename=f'{vid_id}.mp4')
    else:
        vid = utube.streams.filter(
            mime_type="video/mp4", res=res, adaptive=True).last()
        aud = utube.streams.get_audio_only()
        
        vid.download(output_path='media/', filename=f'{msgid}.mp4', timeout=60)
        aud.download(output_path='media/', filename=f'{msgid}.mp3', timeout=60)

        subprocess.run(['ffmpeg', '-i', f'media/{msgid}.mp4', '-i', f'media/{msgid}.mp3', '-c:v',
                    'copy', '-c:a', 'aac', f'media/{vid_id}.mp4'], stdout=subprocess.PIPE)

    with open(f'media/{vid_id}.mp4', 'rb') as video:
        views, duration = humanize.intword(vidata["views"]), utube.length
        caption = f'{title}\n\n👤 {author}\n👁️ {views}'
        with Image.open(thumb) as img:
            try:
                bot.send_chat_action(chatid, 'upload_video')
                bot.send_video(chatid, video, duration, img.width, img.height,
                    InputFile(thumb), caption, reply_to_message_id=msgid,
                    supports_streaming=True, timeout=400)
            except apihelper.ApiTelegramException:
                bot.send_chat_action(chatid, 'upload_video')
                bot.send_video(chatid, video, duration, img.width, img.height,
                    InputFile(thumb), caption, supports_streaming=True, timeout=400)
            except Exception as e:
                bot.send_message(ME, 
                    f'utube exception {e}\n{f"https://www.youtube.com/watch?v={vid_id}"}')
        
    bot.delete_state(vid_id, call.from_user.id)
    constants.clean_folder([msgid, vid_id])
    bot.delete_message(chatid, chooseid)
    mongo.DB.users.update_one({'id': call.from_user.id}, {'$unset': {f'choose.{msgid}': 0}})
    return