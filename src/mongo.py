from dotenv import load_dotenv, find_dotenv
import os
import pymongo
from telebot.types import Message

load_dotenv(find_dotenv())
client = pymongo.MongoClient(os.environ['MONGODB_URI']) # MongoDB's connection sequence

DB = client.TTBotDB


def update_ids(id, file_id, key='sfw'):
    # DB.file_IDs.update_one({'id': id}, {'$pop': {key: -1}})
    DB.file_IDs.update_one({'id': id}, {'$push': {key: file_id}}, upsert=True)


def update_links(link, id):
    # DB.links.update_one({'id': id}, )
    DB.links.update_one(
        {'id': id}, {'$push': {'files': link}}, upsert=True)


def send_link(link):

    things = DB.links.find({'id': 123})
    for i in list(things)[0]['links']:
        if link in i:
            return i
    return False


def finder(id, file_id, key='sfw'):
    things = DB.file_IDs.find({'id': id})
    try:
        if file_id in list(things)[0][key]:
            return True
        return False
    except (IndexError, KeyError):
        update_ids(id, file_id, key)


def reader(id, item):
    things = DB.users.find({'id': id})
    return list(things)[0][item]


def ecReader(chatid, userid=None, *, key=None):
    things = DB.economy.find({'_id': int(chatid)})
    return list(things)[0][str(userid)] if not key else list(things)[0].get(key, None)


def new_player(msg: Message):
    eco_up = DB.economy.update_one
    userid = msg.from_user.id
    eco_up({"_id": msg.chat.id}, {"$set": {f'{userid}.cash': 1000, f'{userid}.bank': 0,
        f'{userid}.name': msg.from_user.first_name}} ,upsert=True)


def user_ids():
    ids = DB.users.find()
    names = set()
    id_s = set()
    for document in ids:
        # return [document.keys()]
        id_s.add(document.get('id', 'NA'))
        conf = document.get('username', 'NA')
        names.add(f'@{conf}' if conf != 'NA' else 'None')
    return [names, id_s]


def user_finder(id):
    user = DB.users.find({'id': id})
    user = list(user)[0]
    return user.get('username', f'{id} --> {user.get("first_name", None)}')

