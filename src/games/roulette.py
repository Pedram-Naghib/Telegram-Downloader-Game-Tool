from src import bot
from random import randint
from telebot.types import Message
from telebot.formatting import hcode, hbold
from src.mongo import DB, ecReader, new_player
import threading
#! this module is work in progress and is not ready yet !

eco_up = DB.economy.update_one


class Roullete:
    def __init__(self, num) -> None:
        self.num = num
        
    def color(self, space):
        if self.num == 0:
            return 'green'
        red = (1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36)
        return 'red' if self.num in red else 'black'

    def parity(self, space):
        if self.num == 0:
            return False
        result = 'even' if self.num % 2 == 0 else 'odd'
        return result == space

    def one_third(self, space):
        if self.num in range(0, 13):
            num_loc = '1-12'
        elif self.num in range(13, 25):
            num_loc = '13-24'
        else:
            num_loc = '25-36'
        return num_loc == space

    def one_half(self, space):
        result = '1-18' if self.num in range(0, 19) else '19-36'
        return result == space


@ bot.message_handler(commands=['roulette'])
def roullete_init(msg: Message):
    userid = str(msg.from_user.id)
    msgid = msg.message_id
    args = msg.text.split()
    VALID_SPACES = ('1-12', '13-24', '25-36', '1-18', '19-36', '1-18',
                    '19-36', 'even', 'odd', 'red', 'black')
    if len(args) != 3:
        bot.reply_to(msg,
            f"{hbold('❌ Too few arguments given!')}\nUsage:\n{hcode('/roulette <bet> <space>')}")
        return
    bet = args[1]
    space = args[2]
    
    try:
        cash = ecReader(msg.chat.id, userid)['cash']
    except (IndexError, KeyError):
        new_player(msg)
        cash = 1000
        
    try:
        bet = int(bet)
    except ValueError:
        if bet.lower() != 'all':
            bot.reply_to(msg,
                f"{hbold('❌ Amount of bet most be in integer!')}\nExample:\n{hcode('/roulette 200 red')}")       
            return
        bet = cash
        
    if space not in VALID_SPACES or isinstance(space, float):
        spc = hcode("<space>")
        bot.reply_to(msg, f"❌ {hbold('Invalid <space> argument given.')}'\nExample:\n\
{hcode('/roulette 200 red')}\n{hcode('/roulette_help')} for all avaiable spaces.")
        return
    
    if cash < bet:
        bot.reply_to(msg,
            f"❌ You don't have enough money for this bet.\nYou currently have {hbold(str(cash))}💵 in cash.\n\n\
use {hcode('/broke')} to findout how to make money!")
        return
    if bet < 20:
        return bot.reply_to(msg, '❌ You must at least bet 20💵.')
    
    data = {f'{userid}.cash': cash - bet, 'group': msg.chat.title}

    user = f'roulette.{userid}'
    if ecReader(msg.chat.id, key='roulette'):
        data.update({f'{user}.bet': bet, f'{user}.name': msg.from_user.full_name,
                     f'{user}.space': space})
        pass # join game
    else:
        data = {f'{user}.bet': bet, f'{user}.name': msg.from_user.full_name,
                            f'{user}.space': space}
        game = bot.send_message(msg.chat.id, 'text')
        t = threading.Timer(30.0, roulette, (msg.chat.id, game.message_id))
        t.start()
        pass # new game
    
    eco_up({'_id': msg.chat.id}, {'$set': data} ,upsert=True)
    
    
def roulette(chatid, msgid):
    num = randint(0, 36)
    players = ecReader(chatid, key='roulette')
    print(players)
    winners = list()
    eco_up({'_id': chatid}, {'$unset': {'roulette': ''}}) # delete game
    
    for player, data in players.items():
        if is_win(player, num)[0]:
            print(f'\n\n{Roullete(num).color(num)} {num}\n{player}: {data["space"]}')
        else:
            print(f'\n\n{Roullete(num).color(num)} {num}\n\n{player}: {data["space"]}')
            


def is_win(space, num):
    game = Roullete(num)
    color = game.color
    
    if space.isdigit():
        return (True, 37) if num == int(space) else (False, None)
    elif space.lower() in ('red', 'black'):
        return (True, 2) if color(num) == space.lower() else (False, None)
    elif space.lower() in ('even', 'odd'):
        return (True, 2) if game.parity(space.lower()) else (False, None)
    elif space in ('1-12', '13-24', '25-36'):
        return (True, 3) if game.one_third(space) else (False, None)
    elif space in ('1-18', '19-36'):
        return (True, 2) if game.one_half(space) else (False, None)
