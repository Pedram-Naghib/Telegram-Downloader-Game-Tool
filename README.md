# UltraTTBot :rocket:

Introducing a versatile Telegram bot that brings together entertainment and utility in a single, convenient package. This feature-packed bot allows you to *download media from popular platforms like TikTok, Reddit, and YouTube.* But that's not all - you can also *enjoy a thrilling game of blackjack* with your friends, complete with a built-in money transfer system that lets you easily send and receive funds.

To add more fun and competition to your group chats, the bot also features a leaderboard that displays who among your friends has the most money. You can easily compare your bank account with your friends and see who's the richest in the group.

But the bot isn't just about fun and games. *It also provides channel admins with a suite of powerful tools* to help them manage their content. With the ability to trim and watermark videos, admins can ensure that their content is protected and stands out from the crowd. Additionally, certain features of the bot can be restricted to channel members only, adding an extra layer of security and exclusivity.

Furthermore, the bot includes a unique feature that lets admins send media to their audience with a time limit. This means that after a set amount of time, the media will be automatically deleted, ensuring that sensitive content is kept secure.

With all these amazing features and more, this Telegram bot is the ultimate all-in-one solution for your media, gaming, and content management needs. Give it a try today and see how it can elevate your Telegram experience!


## 1. Media Downloader:

For the first part, you will be able to download media from those 3 platforms except Reddit without needing anything extra. You just provide the link to the bot and will get the video as the result. The API used for TikTok is made by Evil0ctal and can be found [here](https://github.com/Evil0ctal/Douyin_TikTok_Download_API/blob/main/scraper.py). But the rest of the project code was written by me completely.

For using the Reddit downloader, you would need to get a Reddit key by visiting [this page on Reddit](https://www.reddit.com/prefs/apps). Fill the RedditKey value in the .env file of the project with the key you get after registering for a new app on the mentioned URL.

![App Registring](stuff/reddit_key.jpg)

Also fill the RedditUser and RedditPass too, which are your Reddit username and password respectively.

Feel free to send links from all three platforms and see how the bot responds/handles them.

*Use the /help_media command in the bot for more information.*

## 2.BlackJack and Economy:

BlackJack is a famous card game which you can try with your friends in groups using this bot. [game rules](https://www.officialgamerules.org/blackjack).

By playing each game with your bot, you will either lose or gain money. You can see your placement among other group members in chat and send and receive money from your friends. Ran out of money? Don't worry, you can always get some more every hour by using the /collect command.

Deposit your money and play with your cash in hand in order to get richer and avoid getting broke. Word of advice? Don't get greedy!

*Use the /help_game command in the bot for more information.*

## 3.A Handy Tool for Admins:

There are some extra functionalities with users that are introduced as admins to the bot. Those functionalities are accessible for anyone who uses this project, and bot_admin filter was commented out for the sake of this project. But of course, you can uncomment them and test them as you wish.

There are lots of functionalities this bot provides for channel admins including watermarking videos, checking channel membership of bot users, trimming videos, sending media to the audience with a time limit, and some more.

*Use the /help_admin command in the bot for more information.*