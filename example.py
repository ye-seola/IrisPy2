from irispy2 import Bot, ChatContext


bot = Bot(iris_endpoint="http://192.168.35.144:3000")


@bot.on_event("message")
def on_message(chat: ChatContext):
    if chat.message.msg == "!Hi":
        chat.reply(f"Hello {chat.sender.name}")


@bot.on_event("new_member")
def on_newmem(chat: ChatContext):
    chat.reply(f"Hello {chat.sender.name}")


@bot.on_event("del_member")
def on_delmem(chat: ChatContext):
    chat.reply(f"Bye {chat.sender.name}")


if __name__ == "__main__":
    bot.run(port=9870)
