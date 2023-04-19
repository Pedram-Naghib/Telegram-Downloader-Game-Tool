from src import bot
from src.mongo import ecReader, DB, new_player
from src.constants import inline_markup
from telebot.formatting import hcode, hbold
from telebot.types import Message, CallbackQuery
from src.games.black_jack import eco_up
import datetime
import humanize



ecoComs = ['lb', 'leaderboard']


@ bot.message_handler(commands=['bal', 'ballance'])
def ballance(msg):
    chatid = msg.chat.id
    userid = msg.from_user.id
    try:
        info = ecReader(chatid, userid)
    except KeyError:
        bot.reply_to(msg, '❌ You have not played any game yet.')
        return
    bank, cash = info['bank'], info['cash']

    hint = f"Use the {hcode('/leaderboard')} or {hcode('/lb')} command to view your rank.\n\n"
    header = f"Cash: {cash}💵\nBank: {bank}💵\nTotal: {cash + bank}💵"
    bot.reply_to(msg, hint + header)
    
    
@ bot.message_handler(commands=['lb', 'leaderboard'])
def leaderboard(msg: Message):
    players: dict = list(DB.economy.find({"_id": msg.chat.id}))[0]
    del players['_id']
    del players['group']
    try:
        del players['lb']
    except KeyError:
        pass
    lb = [(v.get('name', k), v['bank'] + v['cash']) for k, v in players.items()]
    lb = sorted(lb, key=lambda item: item[1], reverse=True)
    result = ''
    i = 1
    for name, value in lb:
        result += f'{i}. {name} . {value}💵\n'
        if i == 10:
            break
        i += 1
    markup = inline_markup({'Next ➡️': 'Next'})
    if len(lb) == i - 1:
        markup = None
    eco_up({"_id": msg.chat.id}, {"$set": {'lb': lb}} ,upsert=True)
    bot.reply_to(msg, result, reply_markup=markup)
    

@ bot.callback_query_handler(func= lambda call: call.data == 'Next')
def lb_next(call: CallbackQuery):
    text = call.message.text.split('\n')[-1]
    last_num = int(text.split('.')[0])
    lb = ecReader(call.message.chat.id, key='lb')
    this_lb = lb[last_num: last_num + 10]
    print(lb)
    result = ''
    i = last_num + 10
    for name, value in this_lb:
        result += f'{last_num + 1}. {name} . {value}💵\n'
        if last_num == i:
            break
        last_num += 1
    # print(f'total: {len(lb)}===last printed: {last_num}')
    data = {'⬅️ Prev': 'Previous'}
    if len(lb) != last_num:
        data.update({'➡️': 'Next'})
    bot.edit_message_text(result, call.message.chat.id, call.message.message_id, reply_markup=inline_markup(data, 2))
    

@ bot.callback_query_handler(func= lambda call: call.data == 'Previous')
def lb_previous(call: CallbackQuery):
    text = call.message.text.split('\n')[0]
    first_num = int(text.split('.')[0])
    lb = ecReader(call.message.chat.id, key='lb') #! change chat.id
    this_lb = lb[first_num - 11: first_num - 1]
    print(lb)
    result = ''
    i = first_num - 10
    for name, value in this_lb:
        result += f'{i}. {name} . {value}💵\n'
        if first_num == i:
            break
        i += 1
    # print(f'total: {len(lb)}===last printed: {last_num}')
    data = {'Next ➡️': 'Next'}
    first_num = int(result.split('.')[0])
    if first_num != 1:
        data = {'⬅️ Prev': 'Previous', 'Next ➡️': 'Next'}
    bot.edit_message_text(result, call.message.chat.id, call.message.message_id, reply_markup=inline_markup(data, 2))


@ bot.message_handler(commands=['updateuser'])
def username(msg):
    userid = str(msg.from_user.id)
    try:
        ex = ecReader(msg.chat.id, userid)['name']
        new = msg.from_user.first_name
    except:
        bot.reply_to(msg, '❌ You are not in the players list.')
        return
    if ex != new:
        eco_up({"_id": msg.chat.id}, {"$set": {f'{userid}.name': new}} ,upsert=True)
        bot.reply_to(msg, f'✅ Username updated from {ex} to {new}')
        return
    bot.reply_to(msg, "Your account's username is the same as before.")
    

@ bot.message_handler(commands=['col', 'collect'])
def collect(msg):
    userid = msg.from_user.id
    amount = 300
    try:
        inf: dict = ecReader(msg.chat.id, userid)
        bank, last = inf['bank'], inf.get('time', 0)
    except KeyError:
        new_player(msg)
        bank, last = 0, 0
    # if Bot.is_channel_member(userid):
    #     amount = 800
    now = datetime.datetime.utcnow()
    four_h = last + datetime.timedelta(hours=1) if last else None
    if not last or now > four_h:
        eco_up({"_id": msg.chat.id}, {"$set": {f'{userid}.bank': bank + amount, f'{userid}.time': now}})
        bot.reply_to(msg, f"✅ {amount}💵 has been added to your bank.")
        return
    bot.reply_to(msg, f"❌ You can next collect income in {humanize.naturaldelta(four_h - now)}.")


@ bot.message_handler(commands=['withdraw', 'wid'])
def withdraw(msg):
    args = msg.text.split()
    if len(args) != 2:
        bot.reply_to(msg,
            f"{hbold('❌ Wrong amount of arguments given!')}\nUsage:\n{hcode('/wid <amount>')}\nOr\n{hcode('/withdraw <amount>')}")
        return
    userid = msg.from_user.id
    cash = ecReader(msg.chat.id, userid)['cash']
    bank = ecReader(msg.chat.id, userid)['bank']
    try:
        amount = int(args[1])
    except ValueError:
        if amount := args[1].lower() != 'all':
            bot.reply_to(msg,
                f"{hbold('❌ Amount of bet most be in integer!')}\nExample:\n{hcode('/wid 100')}\nOr\n{hcode('/withdraw 200')}")       
            return
        amount = bank
    if bank < amount:
        bot.reply_to(msg, f"❌ You don't have that much money to withdraw. You currently have {bank}💵 in bank.")
        return
    eco_up({"_id": msg.chat.id}, {"$set": {f'{userid}.cash': cash + amount, f'{userid}.bank': bank - amount}})
    bot.reply_to(msg, f"✅ {amount}💵 Withdrew from your bank!")
    

@ bot.message_handler(commands=['deposit', 'dep'])
def deposit(msg):
    args = msg.text.split()
    if len(args) != 2:
        bot.reply_to(msg,
            f"{hbold('❌ Wrong amount of arguments given!')}\nUsage:\n{hcode('/dep <amount>')}\nOr\n{hcode('/deposit <amount>')}")
        return
    userid = msg.from_user.id
    cash = ecReader(msg.chat.id, userid)['cash']
    try:
        amount = int(args[1])
    except ValueError:
        if amount := args[1].lower() != 'all':
            bot.reply_to(msg,
                f"{hbold('❌ Amount of bet most be in integer!')}\nExample:\n{hcode('/dep 100')}\nOr\n{hcode('/deposit 200')}")       
            return
        amount = cash
    bank = ecReader(msg.chat.id, userid)['bank']
    if cash < amount:
        bot.reply_to(msg, f"❌ You don't have that much money to deposit. You currently have {cash}💵 on hand.")
        return
    eco_up({"_id": msg.chat.id}, {"$set": {f'{userid}.cash': cash - amount, f'{userid}.bank': bank + amount}})
    bot.reply_to(msg, f"✅ Deposited {amount}💵 to your bank!")
    

@ bot.message_handler(commands=['send'], chat_types=["group", "supergroup"])
def send_user(msg: Message):
    args = msg.text.split()
    if len(args) != 2:
        bot.reply_to(msg,
            f"{hbold('❌ Too few arguments given!')}\nUsage:\n{hcode('/send <amount>')}.")
        return
    userid = msg.from_user.id
    Scash = ecReader(msg.chat.id, userid)['cash']
    try:
        amount = int(args[1])
    except ValueError:
        if amount := args[1].lower() != 'all': #* delete amount := from all of them.
            bot.reply_to(msg,
                f"{hbold('❌ Amount to be sent most be in integer!')}\nExample:\n{hcode('/send <amount>')}")
            return
        amount = Scash
    
    if amount > Scash:
        bot.reply_to(msg,
            f"{hbold('❌ You do not have enough money for this!')}")
        return     
    if not msg.reply_to_message:
        bot.reply_to(msg,
            f"{hbold('❌ You should reply to the user you want to send money to!')}")
        return
    if msg.reply_to_message.from_user.id == msg.from_user.id:
        bot.reply_to(msg,
            f"{hbold('❌😀')}")
        return
    rec_id = msg.reply_to_message.from_user.id
    Rname = msg.reply_to_message.from_user.full_name
    Rcash = ecReader(msg.chat.id, rec_id)['cash']
    eco_up({"_id": msg.chat.id}, {"$set": {f'{userid}.cash': Scash - amount, f'{rec_id}.cash': Rcash + amount}})
    bot.reply_to(msg, f"✅ you have successfully sent {amount}💵 to {Rname}!")

    
@ bot.message_handler(commands=['broke'])
def broke(msg):
    bot.reply_to(msg, f"Currently only {hcode('/col')} and {hcode('/collect')} are available.")


@ bot.message_handler(commands=ecoComs, chat_types=["private"])
def ingp(msg):
    bot.reply_to(msg, '❌ This command is only to be used in a groups!')
    