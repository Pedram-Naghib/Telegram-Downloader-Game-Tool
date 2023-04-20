from src import mongo, constants, media_tools, bot
import re
from telebot import apihelper, types
import os
from os.path import exists
import time
import mmap

PROC_OPS = 'Process', 'Link', 'Audio', 'Cancel'

#* -------------------------------------------------------------------------------------------------    
#* callback queries

@ bot.callback_query_handler(func=None, validator=PROC_OPS, is_sender=True)
def videcide(call: types.CallbackQuery):
    c_inf = constants.get_video_info(call) # info about call message
    chatid, msgid = c_inf.chatid, c_inf.msgid
    tag, fileid = call.data.split()
    userid = call.message.from_user.id
    
    if tag in ['Link', 'Cancel']:
        if tag == 'Link':
            send_post_link([msgid, chatid, c_inf.vidid], True)

        bot.edit_message_reply_markup(chatid, msgid, reply_markup=None)
        # cleans media folder after using its content
        constants.clean_folder(fileid)
        
    elif tag == 'Audio':
        constants.perf_title(chatid, userid, None, media_tools.vid2mp3, chatid, fileid)
        bot.edit_message_reply_markup(chatid, msgid, reply_markup=None)
        return
        
    else:
        return vid_proc(c_inf, fileid)   


@bot.callback_query_handler(func=None, validator='joined')
def join_check(call: types.CallbackQuery):
    user_id = call.from_user.id
    file_uid = call.data.split()[1]
    if constants.is_channel_member(user_id):
        bot.send_message(user_id, "Thank you for joining ❤️.")
        post_from_link(file_uid, user_id)
        return
    bot.answer_callback_query(call.id, 
        "You are not joined yet. Please first join and then press Done.",True)
    
    
@bot.callback_query_handler(func=None, validator='chudio', is_sender=True)
def name_audio(call):
    """
    Handle callback queries when the callback data starts with "chudio" or "chudioc" and ends with the user's ID
    :param call: callback query object
    """
    chatid = call.message.chat.id
    # Retrieve user's ID and message ID from callback data
    userid = call.from_user.id
    msgid = call.data.split("-")[1]
    # Edit the reply markup of a previous message
    bot.edit_message_reply_markup(
        userid, mongo.reader(userid, "change")[str(msgid)], reply_markup=None
    )
    # Retrieve audio title and author from database
    title = mongo.reader(userid, "Utitle")
    author = mongo.reader(userid, "author")
    cap = '@YourBotNameHere'

    if call.data.split("-")[0] == "chudio c":
        # Retrieve audio duration and thumbnail from database
        duration = mongo.reader(userid, "duration")
        tuid = mongo.reader(userid, "tuid")
        with open(f"media/{title}.mp3", "rb") as aud:
            bot.send_audio(call.message.chat.id, aud, cap, duration, author, title,
                thumb=types.InputFile(f'media/{tuid}.jpg'))
        # Clean up files
        return constants.clean_folder([title, tuid])
    
    constants.perf_title(chatid, userid, None, media_tools.change_audio)

    
#* -------------------------------------------------------------------------------------------------    
#* content types handlers

@bot.message_handler(content_types=["video"], chat_types=["private"])
def video_handler(msg):
    file_uid = msg.video.file_unique_id
    if constants.IsAdmin.check(msg):
        msgdata = constants.get_video_info(msg)
        vid_proc(msgdata, file_uid)
    else:
    # mp4 to mp3
        file_exists(None, msg.video.file_id, file_uid)
        mongo.DB.users.update_one({"id": msg.from_user.id}, {"$set": {"file_unique_id": file_uid}})
        constants.perf_title(msg.chat.id, msg.from_user.id, None, media_tools.vid2mp3)

# ToDo: separate file for handler functions!


@bot.message_handler(content_types=["audio"], chat_types=["private"])
def voice(msg):
    userid = msg.from_user.id
    title = msg.audio.title
    author = msg.audio.performer    #delete?
    duration = msg.audio.duration
    try:
        thumb, thumb_uid = msg.audio.thumb.file_id, msg.audio.thumb.file_unique_id
        file_dl(thumb_uid, thumb, 'jpg')
    # if the file doesnt have thumbnail then:
    except AttributeError:
        pass

    file_dl(title, msg.audio.file_id, 'mp3')

    mongo.DB.users.update_many({"id": msg.chat.id},
        {"$set": {"duration": duration, "Utitle": title, "tuid": thumb_uid,}}
        ,upsert=True,)

    constants.perf_title(msg.chat.id, userid, (title, author), media_tools.change_audio)


#* -------------------------------------------------------------------------------------------------    
#* general commands

@bot.message_handler(commands=["start"], chat_types=["private"])
def start(msg):
    user_id = msg.from_user.id
    # saves user's info into database
    mongo.DB.users.update_one({"id": user_id},{"$set":
        {"first_name": msg.chat.first_name, "username": msg.chat.username}} ,upsert=True)
    msglen = len(msg.text)
    # uploads message if send command contains file id
    if msglen > 7:
        file_uid = msg.text.split(" ")[1]
        if msglen == 39 or constants.is_channel_member(user_id):
            post_from_link(file_uid, user_id)
        else:
            
            markup = types.InlineKeyboardMarkup(row_width=1)
            # Test channel id in telegram (checks if the user is joined in that channel.)
            markup.add(types.InlineKeyboardButton("Join🗿", 'https://t.me/test'))
            markup.add(types.InlineKeyboardButton("Done✅", callback_data=f"joined {file_uid}"))
            
            bot.send_message(user_id, f"Please join our channel and then press Done to continue.👇",
                reply_markup=markup)
    else:
        # ToDo: better echo maybe?
        constants.echo(msg)


@bot.message_handler(commands=["help"])
def help(msg: types.Message):
    bot.send_message(msg.chat.id, constants.help, 'MarkdownV2')


@bot.message_handler(commands=["myid"])
def msgid(msg: types.Message):
    from telebot.formatting import hcode
    bot.send_message(msg.chat.id, f'Your telegram ID is:\n{hcode(msg.from_user.id)}')

#* -------------------------------------------------------------------------------------------------    
#* others functions

def vid_proc(data, _id=None):
    link, chatid, msgid = data.cap, data.chatid, data.msgid
    file_uid = _id if _id else data.viduid
    
    file_exists(_id, data.vidid, file_uid)
    
    mongo.DB.users.update_many(
        {'id': data.userid},
        {'$set': {'duration': data.dur, 'file_unique_id': data.viduid, 'file_id': data.vidid,
            'width': data.width, 'link': link, 'height': data.height}}, upsert=True)
    # extract the username from caption, if no username: assigns a selfmade error as username
    username = re.findall('👤.*', link)[0][1:] if link and '👤' in link else 'error-bf34'
    cdata = f' {username} {file_uid}'
    # prompt user for desired process to be done on video
    try:
        bot.edit_message_reply_markup(chatid, msgid, reply_markup=constants.inline_markup(
            constants.tags_keys(cdata), row_width=3))
    except:
        bot.send_message(chatid, 'What do you want to do with this video?',
            reply_to_message_id=msgid, reply_markup=constants.inline_markup(constants.tags_keys(cdata, False), row_width=3))
        
#! impove this mess of a function!        
def file_exists(_id : str|int, vidid : str|int, file_uid: str|int):
    """looks for the file with the given _id name and if doesnt find it
    then begins to download it, again with the given variables!

    Args:
        _id (str | int): name of the file to be looked for.
        vidid (str | int): video's unique id.
        file_uid (str | int): name of the file to download the video as if it didnt exist.
    """
    
    file_exists = exists(f'media/{_id}.mp4')
    if not file_exists:
        file_info = bot.get_file(vidid)
        # downloads the video to be processed
        temp_file = bot.download_file(file_info.file_path)
        # uploads the video in a file
        with open(f'media/{file_uid}.mp4', 'wb') as video:
            video.write(temp_file)


def send_post_link(msgdata, channel):
    msgid, userid, fileid = msgdata
    length = 31 if channel else 32
    mongo.DB.links.update_one({"id": 123}, {"$push": {"links": fileid}}, upsert=True)
    print(fileid[:length])
    #ToDo: replace your bot name with YourBotNameHere
    bot.send_message(userid, f"https://t.me/YourBotNameHere?start={fileid[:length]}",
                     reply_to_message_id=msgid) 


def read_media(path):
    with open(path, "rb") as f:
        file_size = os.path.getsize(path)
        mmapped_file = mmap.mmap(f.fileno(), file_size, access=mmap.ACCESS_READ)
        media = mmapped_file.read()
    return media


def file_dl(name, fileid, type):
    file_info = bot.get_file(fileid)
    file = bot.download_file(file_info.file_path)
    filepath = f"media/{name}.{type}"
    with open(filepath, "wb") as f:
        f.write(file)    


def post_from_link(file_uid, user_id):
    length = len(file_uid) == 31
    caption = "#\n@🗿" if length else None
    link = mongo.send_link(file_uid)
    if link:
        try:
            viddel = bot.send_video(user_id, link, caption=caption)
        except apihelper.ApiTelegramException as e:
            bot.send_message(user_id, e)
            viddel = bot.send_photo(user_id, link, caption=caption)
        bot.send_message(
            user_id, "You have 15 secounds before this post gets deleted!")
        time.sleep(15)
        bot.delete_message(chat_id=viddel.chat.id, message_id=viddel.message_id)
    else:
        bot.send_message(
            user_id, "The video you are looking for could not be found!")
        
        
def do_trim(msg):
    userid = msg.from_user.id
    # start = msg.text.split('-')[0].strip()
    try:
        float(msg.text)
        if float(msg.text) > mongo.reader(userid, "duration") or len(msg.text.split(".")) == 1:
            bot.send_message(msg.chat.id, "Make sure you entered the number correctly.")
    except ValueError:
        bot.send_message(userid, "You should enter numbers!")

    media_tools.vid_cut(userid, mongo.reader(userid, "file_unique_id"),
        msg.text, mongo.reader(userid, "duration"))
    
    with open(f'media/{userid}${mongo.reader(userid, "file_unique_id")}.mp4', "rb") as video:
        bot.send_video(msg.chat.id, video)
    constants.clean_folder(msg_id=mongo.reader(userid, "file_unique_id"))

#* -------------------------------------------------------------------------------------------------    
#* functions related to admins or super user 
# (the admin filter is removed from functions so they can be accessible for the sake of this project)
 
@ bot.message_handler(commands=["media"], chat_types=["private"]) #, bot_admin=True
def dir_tree(msg):
    if len(msg.text.split(" ")) == 1:
        rootDir = "./media"
        for lists in os.listdir(rootDir):
            path = os.path.join(rootDir, lists)
            bot.send_message(msg.chat.id, path)
            if os.path.isdir(path):
                dir_tree(path)
    else:
        try:
            constants.clean_folder(msg.text.split(" ")[1])
        except:
            bot.send_message(msg.chat.id, "invalid")
            
            
@bot.message_handler(commands=["cut"]) # , bot_admin=True
def trim(msg):
    video = msg.reply_to_message.video
    chatid = msg.chat.id
    if not (msg.reply_to_message and msg.reply_to_message.video):
        bot.send_message(chatid, "Please reply to a video")

    mongo.DB.users.update_many({"id": chatid},{"$set":
        {"duration": video.duration, "file_unique_id": video.file_unique_id}},upsert=True,)

    f_uid = mongo.reader(msg.from_user.id, "file_unique_id")
    file_info = bot.get_file(msg.reply_to_message.video.file_id)

    mongo.DB.users.update_one({"id": msg.from_user.id}, {"$set":
        {"temp_file": bot.download_file(file_info.file_path)}}, upsert=True)

    with open(f"media/{msg.from_user.id}_{f_uid}.mp4", "wb") as video:
        video.write(mongo.reader(msg.from_user.id, "temp_file"))

    mongo.DB.users.update_one(
        {"id": msg.from_user.id}, {"$set": {"temp_file": None}})
    
    ask = bot.send_message(
        msg.chat.id,
        "Please type secounds you want to cut from end\
of the video in S.xxx-S.xxx format(where x is millisecond and S is secounds)")
    bot.register_next_step_handler(ask, do_trim)


@ bot.message_handler(commands=['watermark'])#, bot_admin=True
def watermark(msg: types.Message):
    try:
        fuid = msg.reply_to_message.video.file_unique_id
        duration = msg.reply_to_message.video.duration
        width = msg.reply_to_message.video.width
        cap = msg.reply_to_message.caption
    except:
        return bot.send_message(msg, "Make sure you are replying this command to a video.")
    file_exists(fuid, msg.reply_to_message.video.file_id, fuid)
    media_tools.vid_edit(fuid, duration, width)
    
    with open(f'media/{fuid}_OUTPUT.mp4', 'rb') as video:
        bot.send_video(msg.chat.id, video, duration, width, caption=cap)
    
    constants.clean_folder(fuid)


@bot.message_handler(commands=["link"], chat_types=["private"])
def link_command(msg):
    userid = msg.from_user.id
    try:
        fileid = msg.reply_to_message.video.file_id
        msgid = msg.reply_to_message.message_id
        send_post_link([msgid, userid, fileid], False)
    except AttributeError:
        bot.send_message(userid, 'Please reply this command to a media!')
        
        
@bot.message_handler(commands=["ids"])
def send_all(msg):
    if msg.from_user.id == 247768888:
        arg = msg.text.split(" ")
        action = {"user": mongo.user_ids()[0], "id": mongo.user_ids()[1]}
        result = action.get(
            arg[1], "Wrong command argument! use 'user' or 'id'"
        )
        with open('users.txt', 'w') as f:
            f.write(str(result))
        with open('users.txt', 'r') as f:
            bot.send_document(msg.chat.id, f)
            # bot.reply_to(msg, f"{str(result)}\n{len(result)}")


@ bot.message_handler(commands=['msgid'])
def mid(msg):
    bot.send_message(msg.chat.id, msg.reply_to_message.message_id)
    

@bot.message_handler(regexp="^❌ Cancel$") # , bot_admin=True
def dump(msg):
    file_id = mongo.reader(msg.from_user.id, "file_unique_id")
    title, tuid = mongo.reader(msg.from_user.id, "Utitle"), mongo.reader(msg.from_user.id, "tuid")
    markup = types.ReplyKeyboardRemove()
    bot.send_message(msg.chat.id, "Process was cancelled.", reply_markup=markup)
    bot.delete_state(msg.from_user.id, msg.chat.id)
    constants.clean_folder([file_id, title, tuid])
