from loguru import logger
from src import server, bot
import os

#ToDo: explain about running the code
if __name__ == "__main__":
    # if you want to run this bot on a server rather than on a hosting service
    # uncomment out next 2 lines and comment the last two ones.
    
    # server.run(host="0.0.0.0", port=8080)
    # logger.info("Bot Started")

    import src.responses
    bot.infinity_polling()