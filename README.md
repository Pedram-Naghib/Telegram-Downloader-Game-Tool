# UltraTTBot :rocket:

this is a telegram bot which provides you with 2 things:
1. downloading media from 3 platforms: Youtube - Tiktok - Reddit
2. playing blackjack game with in game money and other cool stuff related to it.
3. channel admin helper.


## 1. media downloader aspect:

for the first part you will be able to download media from those 3 platfrom except reddit without needing anythin extra.
you just provide the link to the bot and will get the video as the result.
API used for TikTok is made by Evil0ctal and can be found [here](https://github.com/Evil0ctal/Douyin_TikTok_Download_API/blob/main/scraper.py). but the rest of the project code was written by me completly.


for using the reddit downloader you would need to get a reddit key by visiting [this page](https://www.reddit.com/prefs/apps) on reddit! fill the `RedditKey` value in `.env` file of the project with key you get after registring for a new app on the mentioned URL.

![alt text](stuff/reddit_key.jpg)

also fill the `RedditUser` and `RedditPass` too which are your reddit username and password respectfully.


feel free to send links from all three platforms and see how bot respond/handles them.

*use /help_media command in bot for more information*

## 2. BlackJack game aspect:

BlackJack is a famous card game which you can try with your friends in groups using this bot.
[Game rules.](https://www.officialgamerules.org/blackjack)

by playing each game with your bot you will either lose or gain money.
you can see your placement among other group members in chat and send and recieve money from your friends.
ran out of money? dont worry you can always get some more every hour by using /collect command.

deposit your money and play with your cash in hand in order to get richer and avoid getting broke.
Word of advice? don't get greedy!

*use /help_game command in bot for more information*

## 3. channel admin helper.

there are some extra functionality with users that are introduced as admins to the bot. those functionality are accessible for anyone who use this project and `bot_admin` filter was commented out for the sake of this project.
But ofcourse you can uncomment them and test them as you wish.

there are lots of functionalities this bot provides for channel admins including: watermarking videos - checking channel membership of bot users - trimming videos - sending media to audiance with a time limit and some more ...

*use /help_admin command in bot for more information*