from irispy2 import Bot, ChatContext


bot = Bot(iris_endpoint="http://192.168.35.144:3000")


@bot.on_event("message")
def on_message(chat: ChatContext):
    if chat.message.msg == "!Hi":
        chat.reply(f"Hello {chat.sender.name}")

    if chat.message.msg == "!img":
        chat.reply_media(
            "IMAGE",
            [
                open("./example-assets/martin-woortman-HmS5_Gr_0cI-unsplash.jpg", "rb"),
                open("./example-assets/ririchiyo.webp", "rb"),
            ],
        )


@bot.on_event("new_member")
def on_newmem(chat: ChatContext):
    chat.reply(f"Hello {chat.sender.name}")


@bot.on_event("del_member")
def on_delmem(chat: ChatContext):
    chat.reply(f"Bye {chat.sender.name}")


if __name__ == "__main__":
    bot.run(port=9870)
