from src import bot
from src.constants import inline_markup
from math import ceil
from src.mongo import DB, ecReader, new_player
from telebot.formatting import hcode, hbold
from telebot.types import CallbackQuery, Message
import itertools as it
from random import choice, shuffle


eco_up = DB.economy.update_one
CARDS = {'2️⃣': 2, '3️⃣': 3, '4️⃣': 4, '5️⃣': 5,'6️⃣': 6, '7️⃣': 7, '8️⃣': 8,
        '9️⃣': 9, '🔟': 10, 'J': 10, '👸': 10, '🤴': 10, '1️⃣': 11}
SHAPES = ['♠️', '♣️', '♥️', '♦️']


def draw(chatid=None, userid=None, com_id=None, *, rep_id=None):
    try:
        deck = ecReader(chatid, userid)[com_id]['deck']
    except Exception as e:
        deck = ecReader(chatid, userid)[rep_id]['deck']
    card = deck.pop()
    eco_up({'_id': chatid}, {'$set': {f'{str(userid)}.{com_id}.deck': deck}})
    return card


def value(cards):
    hand = cards.copy()
    val, ace = 0, 0
    for card in hand:
        if '1️⃣' not in card:
            val += CARDS[card[0]]
        else:
            ace += 1
    for _ in range(ace):
        if val + 11 < 21:
            val += 11
        elif val + 11 > 21:
            val += 1
            ace -= 1
        else:
            return 'Blackjack' if len(cards) == 2 else 21
    if ace:
        return f'Soft {val}'
    else:
        return val


def result(bj, ids, res=None, *, splt=False):
    chatid, userid, msg_id = ids
    db = ecReader(chatid, userid)
    cash, bet, msgid = db['cash'], db[msg_id]['bet'], db[msg_id]['id']
    if bj:
        amount = ceil(2.5 * bet)
        eco_up({'_id': chatid}, {'$set': {f'{userid}.cash': cash + amount}})
        state = ['Win', int(ceil(1.5 * bet))]
        text = desc(None, None, ids, state)
        bot.edit_message_text(text, chatid, msgid)
        if not splt:
            eco_up({'_id': chatid}, {'$unset': {f'{userid}.{msg_id}': ''}})
        return
    if res in ['Win', 'Dealer bust']:
        amount = 2 * bet
        state = [res, bet]
    elif res in ['Loss', 'Bust']:
        amount = 0
        state = [res, -1 * bet]
    else:
        amount = bet
        state = ['Push, money back', '']
        
    eco_up({'_id': chatid}, {'$set': {f'{userid}.cash': cash + amount}})
    text = desc(None, None, ids, state)
    bot.edit_message_text(text, chatid, msgid)
    if not splt:
        eco_up({'_id': chatid}, {'$unset': {f'{userid}.{msg_id}': ''}})
    
    
def start(msg, dd):
    chatid = msg.chat.id
    userid = msg.from_user.id
    com_id = str(msg.message_id)
    ids = (chatid, userid, com_id)
    plCrds, dlCrds = [], []
    
    plCrds.append(draw(*ids))
    plCrds.append(draw(*ids))
    dlCrds.append(draw(*ids))
    
    data = {f'{userid}.{com_id}.plCrds': plCrds, f'{userid}.{com_id}.dlCrds': dlCrds}
    eco_up({"_id": msg.chat.id}, {"$set": data}, upsert=True)
    
    
    split = CARDS[plCrds[0][0]] == CARDS[plCrds[1][0]]
    text = desc(True, split, ids)
    markup = {'Hit': f'hit {com_id}', 'Stand': f'stand {com_id}'}
    if dd:
        markup.update({'Double Down': f'dd {com_id}'})
        if split:
            markup.update({'Split': f'split {com_id}'})
    first = bot.reply_to(msg, text, reply_markup=inline_markup(markup, 2))
    eco_up({"_id": msg.chat.id}, {"$set": {f'{userid}.{com_id}.id': first.message_id}},upsert=True)
    
    if value(plCrds) == 'Blackjack':
        stand((userid, chatid, com_id, False))
    

@ bot.callback_query_handler(func=None, validator='hit', is_sender=True, is_game=True)
def hit(call: CallbackQuery):
    userid, chatid = call.from_user.id, call.message.chat.id
    com_id, msgid = call.data.split()[1], call.message.message_id
    ids = (chatid, userid, com_id)
    hand_data = ecReader(chatid, userid)[com_id]
    try:
        com_id_org = call.data.split()[3]
    except:
        com_id_org = None
    
    plCrds = hand_data['plCrds']
    plCrds.append(draw(*ids, rep_id=com_id_org))
    eco_up({"_id": int(chatid)}, {"$set": {f'{userid}.{com_id}.plCrds': plCrds}}, upsert=True)
    val = value(plCrds)
    if isinstance(value(plCrds), str):
        val = int(val.split()[1])
    if val > 21:
        if call.data.split()[0] == 'hit':
            return result(False, ids, 'Bust')
        return spland(call)
    if hand_data.get('split', None):
        markup = {'Hit': f'splithit {com_id} {userid}', 'Stand': f'spland {com_id} {userid}'}
    else:
        markup = {'Hit': f'hit {com_id} {userid}', 'Stand': f'stand {com_id} {userid}'}
    text = desc(None, None, ids)
    bot.edit_message_text(text, int(chatid), msgid,
            reply_markup=inline_markup(markup, 2))


@ bot.callback_query_handler(func=None, validator=['stand', 'dd'], is_sender=True, is_game=True)
def stand(call: CallbackQuery):
    if isinstance(call, CallbackQuery):
        userid, chatid = call.from_user.id, call.message.chat.id
        move, com_id = call.data.split()[0] ,call.data.split()[1]
        splt = ecReader(chatid, userid).get('split', None)
    else:
        userid, chatid, com_id, splt, move = *call, 'stand'
    try:
        com_id_org = call.data.split()[3]
    except Exception: #! broad exception
        com_id_org = com_id

    ids = (chatid, userid, com_id)
    hand_data = ecReader(chatid, userid)
    plCrds = hand_data[com_id]['plCrds']
    dlCrds = hand_data[com_id]['dlCrds']
    
    if move == 'dd':
        plCrds.append(draw(*ids))
        cash, bet = hand_data['cash'], hand_data[com_id]['bet']
        eco_up({'_id': chatid}, {'$set': {f'{userid}.cash': cash - bet, f'{userid}.{com_id}.bet': bet * 2}})
        if value(plCrds) > 21:
            eco_up({"_id": chatid}, {"$set": {f'{userid}.{com_id}.dlCrds': dlCrds, f'{userid}.{com_id}.plCrds': plCrds}})
            return result(False, ids, 'Bust')
    
    pl_val = value(plCrds)
    de_val = value(dlCrds)
    if isinstance(pl_val, str) and 'Soft' in pl_val:
        pl_val = int(pl_val.split()[1])
    if isinstance(de_val, str) and 'Soft' in de_val:
        de_val = int(de_val.split()[1])
 
    while de_val != 'Blackjack' and de_val < 17:
        dlCrds.append(draw(*ids, rep_id=com_id_org))
        de_val = value(dlCrds)
        if isinstance(de_val, str):
            if de_val == 'Blackjack':
                break
            else:
                de_val = int(de_val.split()[1])
    eco_up({"_id": chatid}, {"$set": {f'{userid}.{com_id}.dlCrds': dlCrds, f'{userid}.{com_id}.plCrds': plCrds}})
    stand_result(pl_val, de_val, ids, splt)


def stand_result(pl_val, de_val, ids, splt):
    if de_val == 'Blackjack':
        if pl_val == 'Blackjack' or 21:
            return result(False, ids, 'Tie', splt=splt)
        return result(False, ids, 'Loss', splt=splt)
    if pl_val == 'Blackjack':
        return result(True, ids, splt=splt)
    elif pl_val > 21:
        return result(False, ids, 'Bust', splt=splt)
    if de_val > 21:
        return result(False, ids, 'Dealer bust', splt=splt)
    elif de_val > pl_val:
        return result(False, ids, 'Loss', splt=splt)
    elif de_val == pl_val:
        return result(False, ids, 'Tie', splt=splt)
    return result(False, ids, 'Win', splt=splt)


@ bot.callback_query_handler(func=None, validator='split', is_sender=True, is_game=True)
def split(call: CallbackQuery):
    # return bot.answer_callback_query(call.id, '👷‍♀️👷‍♂️', True)
    userid, chatid = call.from_user.id, call.message.chat.id
    com_id, desc_id = call.data.split()[1], call.message.message_id
    ids1, ids2 = (chatid, userid, com_id), (chatid, userid, str(desc_id))
    hand_data = ecReader(chatid, userid)
    round1, round2 = hand_data[com_id]['plCrds']
    round1, round2 = [round1], [round2]
    dlCrds = hand_data[com_id]['dlCrds']
    
    round1.append(draw(*ids1))
    round2.append(draw(*ids1))
    
    bet, cash = hand_data[com_id]['bet'], hand_data['cash']
    data = {f'{userid}.{com_id}.plCrds': round1, f'{userid}.{com_id}.dlCrds': dlCrds,
            f'{userid}.{desc_id}.plCrds': round2, f'{userid}.{desc_id}.dlCrds': dlCrds, f'{userid}.{com_id}.split': True,
            f'{userid}.{desc_id}.bet': bet, f'{userid}.cash': cash - bet, f'{userid}.{desc_id}.split': True}
    eco_up({"_id": chatid}, {"$set": data}, upsert=True)
    text1 = desc(False, False, ids1)
    #? text2 = desc(False, False, ids2)
    mu1 = {'Hit': f'splithit {com_id} {userid}', 'Stand': f'spland {com_id} {userid}'}
    bot.edit_message_text(text1, chatid, desc_id, reply_markup=inline_markup(mu1, 2))
    if value(round1) == 'Blackjack':
        return spland(call)
            
            
@ bot.callback_query_handler(func=None, validator='spland', is_sender=True, is_game=True)
def spland(call: CallbackQuery):
    userid, chatid = call.from_user.id, call.message.chat.id
    repmsgid, msgid = call.data.split()[1], call.message.message_id
    rep_text = call.message.reply_to_message.text
    
    if '/bj' in rep_text or '/blackjack' in rep_text: # first round (dont draw cards for dl - remove inline markup)
        try:
            text1 = desc(False, False, (chatid, userid, repmsgid))
            bot.edit_message_text(text1, chatid, msgid, reply_markup=None)
        except:
            bot.edit_message_reply_markup(chatid, msgid, reply_markup=None)
        
        text2 = desc(False, False, (chatid, userid, str(msgid)))
        mu2 = {'Hit': f'splithit {msgid} {userid} {repmsgid}', 'Stand': f'spland {msgid} {userid} {repmsgid}'}
        sec = bot.send_message(chatid, text2, reply_to_message_id=msgid, reply_markup=inline_markup(mu2, 2))
        eco_up({"_id": chatid}, {"$set": {f'{userid}.{msgid}.id': sec.message_id,
                                          f'{userid}.{msgid}.com_id': repmsgid}},upsert=True)
        if value(ecReader(chatid, userid)[str(msgid)]['plCrds']) == 'Blackjack':
            return spland_result((chatid, userid, str(msgid)))
    else:
        spland_result((chatid, userid, str(repmsgid)))
    

def spland_result(_ids):
    chatid, userid, repmsgid = _ids
    com_id_org = ecReader(chatid, userid)[repmsgid]['com_id']
    stand((userid, chatid, com_id_org, True)) # first round results
    ids = (chatid, userid, repmsgid)
    plCrds = ecReader(chatid, userid)[repmsgid]['plCrds']
    dlCrds = ecReader(chatid, userid)[com_id_org]['dlCrds']
    pl_val, de_val = value(plCrds), value(dlCrds)
    eco_up({'_id': chatid}, {'$unset': {f'{userid}.{com_id_org}': ''}})
    eco_up({'_id': chatid}, {'$set': {f'{userid}.{repmsgid}.dlCrds': dlCrds}})
    if isinstance(pl_val, str) and 'Soft' in pl_val:
        pl_val = int(pl_val.split()[1])
    if isinstance(de_val, str) and 'Soft' in de_val:
        de_val = int(de_val.split()[1])
    if not isinstance(value(plCrds), str) and value(plCrds) > 21:
        return result(False, ids, 'Bust', splt=False)
    return stand_result(pl_val, de_val, ids, False)
    

def desc(double, split, ids, state=None):
    chatid, userid, com_id = ids
    hand_data = ecReader(chatid, userid)
    plCrds = hand_data[com_id]['plCrds']
    dlCrds = hand_data[com_id]['dlCrds']
    
    if not state:
        hints = f"{hbold('hit')} - take another card\n{hbold('stand')} - end the game"
        if double:
            hints += f"\n{hbold('double down')} - double your bet, hit once, then stand"     
            if split:
                hints += f"\n{hbold('split')} - two cards gets separated and treated as separated hands"
    else:
        curr = ''
        if 'Push' not in state[0]:
            # curr = ecReader(chatid, userid)['curr']
            pass
        hints = f'Result: {state[0]}  {state[1]}{"💵"}'
        

    player_value = hbold(value(plCrds)) if value(plCrds) == 'Blackjack' else value(plCrds)
    dealer_value = hbold(value(dlCrds)) if value(dlCrds) == 'Blackjack' else value(dlCrds)
    
    header = "Your Hand                  Dealer's Hand"
    cards = card_print(ids)
    values = f"Value: {player_value}{(19 - len(str(player_value))) * ' '}Value: {dealer_value}"
    return f"{hints}\n\n{header}\n{cards}\n{values}"


def card_print(ids):
    chatid, userid, com_id = ids
    hand_data = ecReader(chatid, userid)
    plCrds = hand_data[com_id]['plCrds']
    dlCrds = hand_data[com_id]['dlCrds']
    
    de_crd_str = ''
    pl_crd_str = ''
    for card in plCrds:
        pl_crd_str += f'({card[0]}{card[1]})&'
    for card in dlCrds:
        de_crd_str+= f'({card[0]}{card[1]})&'
    data1 = pl_crd_str.split('&')
    data2 = de_crd_str.split('&')
    
    i, j = 0, 0 
    res = ''
    for _ in range(ceil(max(len(data1), len(data2)) / 2)):
        plcrds = ''.join(data1[i:i+2])
        spc = 37
        if len(plcrds) > 10:
            spc = 21
        elif len(plcrds) > 3:
            spc = 30
        res += plcrds + (spc - len(plcrds)) * ' ' + ''.join(data2[j:j+2]) + '\n'
        i += 2
        j += 2
        
    return res
        


@ bot.message_handler(commands=['bj', 'blackjack'])
def bj_init(msg: Message):
    userid = str(msg.from_user.id)
    msgid = msg.message_id
    args = msg.text.split()
    if len(args) != 2:
        bot.reply_to(msg,
            f"{hbold('❌ Invalid amount of arguments given!')}\nUsage:\n{hcode('/bj <bet>')}\nOr\n{hcode('/blackjack <bet>')}")
        return
    bet = args[1]
    
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
                f"{hbold('❌ Amount of bet most be in integer!')}\nExample:\n{hcode('/bj 100')}\nOr\n{hcode('/blackjack 200')}")       
            return
        bet = cash
    
    if cash < bet:
        bot.reply_to(msg,
            f"❌ You don't have enough money for this bet.\nYou currently have {hbold(str(cash))}💵 in cash.\n\n\
use {hcode('/broke')} to findout how to make money!\nOr {hcode('/wid')} to withdraw money from your bank.")
        return
    if bet < 20:
        return bot.reply_to(msg, '❌ You must at least bet 20💵.')
        
    deck = list(it.product(CARDS, SHAPES))
    shuffle(deck)
    data = {f'{userid}.{msgid}.bet': int(bet), f'{userid}.{msgid}.deck': deck, f'{userid}.cash': cash - bet,
            'group': msg.chat.title}
    eco_up({'_id': msg.chat.id}, {'$set': data} ,upsert=True)
    
    dd = True
    if bet * 2 > cash:
        dd = False
    
    return start(msg, dd)