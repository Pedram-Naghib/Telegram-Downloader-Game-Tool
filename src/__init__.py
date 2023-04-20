from telebot import types, TeleBot
from telebot.storage import StateMemoryStorage
from flask import Flask, request
import os
import requests as req
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())


CLIENT_ID = '' #ToDo

def reddit_config():
    auth = req.auth.HTTPBasicAuth(CLIENT_ID, os.environ['RedditKey'])
    data = {
        'grant_type': 'password',
        'username': os.environ['RedditUser'], # Reddit account username
        'password': os.environ['RedditPass'] # Reddit account password
    }

    headers = {'User-Agent': 'MyAPI/0.0.1'}
    res = req.post('https://www.reddit.com/api/v1/access_token',
                auth=auth, data=data, headers=headers, timeout=100)
    REDDIT_TOKEN = res.json()['access_token']
    headers['Authorization'] = f'bearer {REDDIT_TOKEN}'
    return headers

TOKEN = '' # Token obtained from https://t.me/BotFather
state_storage = StateMemoryStorage()
bot = TeleBot(TOKEN, parse_mode='HTML', state_storage=state_storage)

server = Flask(__name__)


@server.route('/' + TOKEN, methods=['POST'])
def getMessage():
    json_string = request.get_data().decode('utf-8')
    update = types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200


@server.route("/")
def webhook():
    bot.remove_webhook()
    # Set the webhook to your project on a VPS (heroku in my case).
    #! (ignore this and check run.py in order to run this project on your own system)
    bot.set_webhook(url='https://myproject.herokuapp.com/' + TOKEN)
    return "!", 200


from src.media_dl import reddit, tiktok, youtube
from src import constants, mongo, media_tools, responses
from src.games import economy, black_jack, roulette