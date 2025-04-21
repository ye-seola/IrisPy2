from irispy2 import Bot, ChatContext
from irispy2.bot.models import ErrorContext


bot = Bot(iris_url="http://192.168.35.71:3000")


@bot.on_event("message")
def on_message(chat: ChatContext):
    if chat.message.msg == "!room":
        chat.reply(f"{chat.room}")

    if chat.message.msg == "!Hi":
        chat.reply(f"Hello {chat.sender.name}")

    if chat.message.msg == "!img":
        chat.reply_media(
            "IMAGE",
            [
                # IO로 보내기
                open("./assets/martin-woortman-HmS5_Gr_0cI-unsplash.jpg", "rb"),
                
                # bytes로 보내기
                open("./assets/ririchiyo.webp", "rb").read(),
            ],
        )

    if chat.message.msg == "!err":
        0 / 0


@bot.on_event("new_member")
def on_newmem(chat: ChatContext):
    chat.reply(f"Hello {chat.sender.name}")


@bot.on_event("del_member")
def on_delmem(chat: ChatContext):
    chat.reply(f"Bye {chat.sender.name}")


@bot.on_event("error")
def on_error(err: ErrorContext):
    print(err.event, "이벤트에서 오류가 발생했습니다", err.exception)


if __name__ == "__main__":
    bot.run()
