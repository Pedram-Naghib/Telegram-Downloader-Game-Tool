import urllib.request
from telebot import types
import subprocess
from src import mongo, constants, responses, bot
from os.path import exists

TAGS = "#1", "#2", "#3", "#4", "#5", "#6", "#7", 'Back'
ME = '' # Your telegram account id (Not username) for logging errors only.


def vid_dl(url4, url3, chatid, postid, title, data=None):
    thumb, w, h, duration = None, None, None, None
    if data:
        thumb, w, h, duration = data.values()
        thumb = types.InputFile(thumb)
    if not url3:
        mp4 = f'media/{chatid}_{postid}.gif'
        urllib.request.urlretrieve(url4, filename=mp4)
        send = bot.send_animation

    elif url3 == 'image':
        mp4 = f'media/@_{chatid}_{postid}.jpg'
        urllib.request.urlretrieve(url4, filename=mp4)
        send = bot.send_photo

    elif url3 == 'video':
        mp4 = f'media/@_{chatid}_{postid}.mp4'
        urllib.request.urlretrieve(url4, filename=mp4)
        send = bot.send_video

    else:
        urllib.request.urlretrieve(url4, filename=f'media/{chatid}_{postid}_mp4')
        mp4 = f'media/@_{chatid}_{postid}.mp4'
        urllib.request.urlretrieve(
            url3, filename=f'media/{chatid}_{postid}_mp3')
        subprocess.run(['ffmpeg', '-i', f'media/{chatid}_{postid}_mp4', '-i', f'media/{chatid}_{postid}_mp3', '-c:v',
                       'copy', '-c:a', 'aac', mp4], stdout=subprocess.PIPE)
        send = bot.send_video


    with open(mp4, 'rb') as media:
        bot.send_chat_action(chatid, 'upload_video')
        send(chatid, media, duration, w, h, thumb, title)
        constants.clean_folder(msg_id=postid)


def vid_edit(msg_id, d, w):
    t = 1.34 * (w / d)
    subprocess.run(['ffmpeg', '-i', f'media/{msg_id}.mp4', '-threads', '8', '-filter_threads', '4', '-i', 'stuff/logo.png', '-filter_complex',
                    f"[0:v][1:v] overlay=x='if(gte(t,1), -w+(t-1)*{t}, NAN)':y=H/2:enable='between(t,1,{d})'", f'media/{msg_id}_OUTPUT.mp4'], stdout=subprocess.PIPE)
    return None



def vid_cut(msgid, postid, sec, d):
    t1 = str(int(d) - float(sec)).split('.')
    t, ms = str(t1[0]).zfill(2), str(t1[1]).zfill(3)

    subprocess.run(['ffmpeg', '-ss', '00:00:00.00', '-to', f'00:00:{t}.{ms}', '-i',
                    f'media/{msgid}_{postid}.mp4', '-c', 'copy', f'media/{msgid}${postid}.mp4'], stdout=subprocess.PIPE)
    

@bot.message_handler(state=constants.MyStates.vid2mp3)
def vid2mp3(msg):
    chat = msg.chat.id
    fileid = mongo.reader(msg.from_user.id, "file_unique_id")
    title, performer = msg.text.split('\n')
    subprocess.run(['ffmpeg', '-i', f'media/{fileid}.mp4', '-b:a', '320K', '-vn', f'media/{title}.mp3'])
    with open(f'media/{title}.mp3', 'rb') as aud:
        bot.send_audio(chat, aud, performer=performer, title=title)
    bot.delete_state(msg.from_user.id, chat)
    constants.clean_folder([fileid, title])
    
    
def comp(name, chat):
    subprocess.run(['ffmpeg', '-i', f'media/{name}.mp4', 'output.mp4'])
    with open('output.mp4', 'rb') as video:
        bot.send_video(chat, video)
        
        
def get_length(filename):
    result = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                             "format=duration", "-of",
                             "default=noprint_wrappers=1:nokey=1", filename],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT)
    return float(result.stdout)


@bot.callback_query_handler(func=None, validator=TAGS, is_sender=True)
def vidproc(call):
    c_inf = constants.get_video_info(call)
    chatid, cdata =c_inf.chatid, call.data.split
    tag, username, file_uid = cdata()[0], cdata()[1], cdata()[2]
    duration, height, width = c_inf.dur, c_inf.height, c_inf.width
    msgid = c_inf.msgid
    
    if tag == "Back":
        return constants.proc_keys(chatid, file_uid, msgid)

    if tag == "Audio":
        constants.perf_title(chatid, None, vid2mp3, file_uid, chatid)
        bot.edit_message_reply_markup(c_inf.chatid, msgid, reply_markup=None)
        return

    else:
        bot.send_chat_action(chatid, 'upload_video')
        # 'make it ready for post'!
        vid_edit(file_uid, duration, width)
        try:
            thumb_data = responses.read_media(f"media/{file_uid}.jpg")
        except FileNotFoundError:
            thumb_data = None
        # opening the video file and sending it to he user
        try:
            with open(f"media/{file_uid}_OUTPUT.mp4", "rb") as video:
                bot.send_video(call.message.chat.id, video, duration, width, height, thumb_data,
                    constants.caption(username, tag), supports_streaming=True,)
        except FileNotFoundError:
            bot.send_message(call.message.chat.id, "Please send me the link or the video again.")

    bot.edit_message_reply_markup(c_inf.chatid, msgid, reply_markup=None)
    # cleans media folder after using its content
    constants.clean_folder(file_uid)
    
@bot.message_handler(state=constants.MyStates.change_audio)
def change_audio(msg):
    print('change audio triggered...!')
    userid = msg.from_user.id  # ?msgid = msg.chat.id remove?
    orgtitle = mongo.reader(userid, "Utitle")
    data = msg.text.split("\n")
    tuid, duration = mongo.reader(userid, "tuid"), mongo.reader(userid, "duration")
    cap = '@HumbanBot'
    file_exists = exists(f'media/{tuid}.jpg')
    thumb = f"media/{tuid}.jpg" if file_exists else None
    
    if len(data) == 2:
        title, author = data
        with open(f"media/{orgtitle}.mp3", "rb") as aud:
            bot.send_audio(msg.chat.id, aud, cap, duration, author, title,
                thumb=types.InputFile(thumb))
        # Clean media directory from processed files!
        constants.clean_folder([orgtitle, tuid])
    else:
        bot.reply_to(userid,
            "Please make sure you entered audio's name and artist correct and in separate lines!")
    bot.delete_state(userid, msg.chat.id)