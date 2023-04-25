from telebot.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    CallbackQuery
)
import glob
import os
from types import SimpleNamespace
from telebot import custom_filters
from telebot.formatting import hbold, hcode
import re
from src import bot


SUPER_USER = 0 # insert your telegram ID (You can find out yours by using /myid command in bot)

def keyboard(keys, row_width=3, resize_keyboard=True):
    markup = ReplyKeyboardMarkup(row_width=row_width, resize_keyboard=resize_keyboard)
    buttons = map(KeyboardButton, keys)
    markup.add(*buttons)

    return markup


keys = SimpleNamespace(
    cancel="❌ Cancel",
    dump="💃",
    home="🏠",
    link="Post Link",
)
keyboards = SimpleNamespace(
    main=keyboard([keys.home]),
    hashtag=keyboard([keys.link]),
    defult=keyboard([keys.dump]),
    cancel=keyboard([keys.cancel]),
)

def proc_keys(chatid, vidid, msgid):
    keyboard = {'Process': f'Process {vidid}', 'Link': f'Link {vidid}',
            'Audio 🎵': f'Audio {vidid}', '❌': f'Cancel {vidid}'}
    bot.edit_message_reply_markup(chatid, msgid,
    reply_markup=inline_markup(keyboard, 2))
    
def tags_keys(cdata, back=True):
    mydict = {'a': f'a{cdata}', 'b': f'b{cdata}', 'c': f'c{cdata}',
        'd': f'd{cdata}', 'e': f'e{cdata}', 'f': f'f{cdata}'}
    if back:
        mydict.update({'⬅️': f'Back{cdata}'})
        return mydict
    return mydict
    

def inline_markup(keys, row_width=3):
    buttons = []
    markup = InlineKeyboardMarkup(row_width=row_width)
    for key, value in keys.items():
        button = InlineKeyboardButton(key, callback_data=value)
        buttons.append(button)
    markup.add(*buttons)

    return markup


def inline_url(keys, row_width=1):
    buttons = []
    markup = InlineKeyboardMarkup(row_width=row_width)
    for i in keys.items():
        button = InlineKeyboardButton(i[0], i[1])
        buttons.append(button)
    markup.add(*buttons)

    return markup


def clean_folder(msg_id=None):
    files = glob.glob("./media/*")
    if msg_id == None:
        for f in files:
            os.remove(f)
    elif type(msg_id) == list:
        print(f"files: {list(files)}\npostids: {msg_id}")
        for f in files:
            for i in msg_id:
                if str(i) in f:
                    print(f"found {i} in {f}")
                    os.remove(f)
    else:
        for f in files:
            if str(msg_id) in f:
                os.remove(f)
    return None


def byteconv(byte):
    ibyte = byte
    suf = ["MB", "GB"]
    if len(str(byte)) < 8:
        ibyte /= 10**6
        return f"{ibyte:.2f} {suf[0]}"
    ibyte /= 10**9
    return f"{ibyte:.2f} {suf[1]}"


def caption(user, hash):
    if user != "error-bf34":
        return f"{hash}\n{user}\n@🗿"
    try:
        user = re.findall("https://www.tiktok.com/(@.*?/)", user)
        try:
            usern = user[0][1:-1]
            return f"{hash}\n{usern}\n@🗿"
        except:
            return f"{hash}\n@🗿"
    except:
        return f"{hash}\n@🗿"


def echo(msg):
    name = msg.chat.first_name
    text = f"Hey <strong>{name}</strong>!\nDownload media (up to 50Mb) from Youtube, Tiktok, Reddit by sending me their links.\
\nUse /help command to findout more about bot game features!"
    if IsAdmin.check(msg) and msg.chat.type == "private":
        text += "\n/cut S.xxx - Cut S seconds and xxx miliseconds from end of the video.\
\n/watermark - Wtermark the video which the command was replied to.\
\n/link - Get a link for the replied media to send with a time limit.\
\n/users id and /users user - Get all of bot user usernames(user) or ids(id)"
    bot.send_message(
        msg.chat.id, text)



from telebot.handler_backends import State, StatesGroup


class MyStates(StatesGroup):
    vid2mp3 = State()
    change_audio = State()


bot.add_custom_filter(custom_filters.StateFilter(bot))

def perf_title(chatid, userid, info, func, *args):
    if info:
        title, author = info
        # Send the current title and artist of the audio
        bot.send_message(chatid,
                         f"👇Current information:\n\n{hbold('Title')}: {hcode(title)}\n{hbold('Artist')}: {hcode(author)}")
    # Send a message asking user to send audio name and artist
    bot.send_message(chatid, "Please send the audio's \
name and artist in one message and 2 lines\n\naudio name\naudio artist", reply_markup=keyboards.cancel)
    # Register next step handler to change the audio
    if func.__name__ == 'vid2mp3':
        return bot.set_state(userid, MyStates.vid2mp3, chatid)
    elif func.__name__ == 'change_audio':
        return bot.set_state(userid, MyStates.change_audio, chatid)
    raise NameError(f"No state hass been implemented for {func.__name__}")



def audio_cc(title, perf, size):
    audio_cc = f"""💾 {hbold('File name')}: {title}
👤 {hbold('File performer')}: {perf}
📥 {hbold('File size')}: {size}
    """
    return audio_cc


def get_video_info(msg: Message):
    try:
        msg.data
        msg = msg.message
    except AttributeError:
        pass
    if video := msg.video or msg.reply_to_message.video:
        return SimpleNamespace(viduid=video.file_unique_id, vidid=video.file_id,
                     dur=video.duration, width=video.width, height=video.height,
                     chatid=msg.chat.id, msgid=msg.message_id, cap=msg.caption,
                     userid=msg.from_user.id)

    return SimpleNamespace(chatid=msg.chat.id, msgid=msg.message_id, cap=msg.caption,
                           userid=msg.from_user.id)
    
    
def is_channel_member(user_id):
    try: #ToDo: check validity of the comment bellow.
        join = bot.get_chat_member(000, int(user_id)) # 000 is the id of the test channel made (check response.py line 141)
    except Exception as e:
        if "user not found" in str(e):
            return False

    if (join.status == "kicked") or (join.status == "left"):
        return False
    return True


help = '''
*Blackjack with economy:*
/blackjack or /bj \- Start a blackjack game in the private or group chat\.
/roulette \- Play roulette game in the private or group chat\.
/ballance or /bal \- Check your ballance\.
/leaderboard or /lb \- Compare your ballance with your friends in a group chat\.
/updateuser \- Change your name in leaderboard to your new name in telegram\.
/collect or /col \- Collect 300💵 every hour\.
/withdraw or /wid \- Withdraw money from your bank account\.
/deposit or /dep \- Deposit money to your bank account\.
/send \<amount\> \- Reply this command to someone to send them \<amount\>💵\.
/broke \- Use this to findout about ways of making money if you ran out\. spoiler: ||only /col is available at the moment\.||
'''


#* -------------------------------------------------------------------------------------------------------------
#* custom filters

ADMINS = 000, 000, SUPER_USER # isert other admins user id if any.


class IsAdmin(custom_filters.SimpleCustomFilter):
    key='bot_admin'
    @staticmethod
    def check(message: Message):
        return message.chat.id in ADMINS


class ValidCall(custom_filters.AdvancedCustomFilter):
    key='validator'
    @staticmethod
    def check(message: Message, iterator: tuple|str):
        if isinstance(iterator, str):
            return iterator in message.data
        for i in iterator:
            if i in message.data:
                return True
        return False
    

class IsSender(custom_filters.SimpleCustomFilter):
    key='is_sender'
    @staticmethod
    def check(call: CallbackQuery):
        sender = call.message.reply_to_message.from_user.id
        presser = call.from_user.id
        return sender == presser or (str(presser) in call.data)

    
class IsGame(custom_filters.SimpleCustomFilter):
    key='is_game'
    @staticmethod
    def check(call: CallbackQuery):
        game = call.message.reply_to_message.message_id
        callmsg = call.data.split()[1]
        return game == int(callmsg)


bot.add_custom_filter(ValidCall())
bot.add_custom_filter(IsSender())
bot.add_custom_filter(IsGame())