from pathlib import Path
import traceback
from irispy2 import Bot, ChatEvent
from irispy2.core.emitter import ErrorContext


bot = Bot(iris_url="http://192.168.35.219:3000")

ASSETS_PATH = Path(__file__).parent / "assets"


@bot.on_event("message")
def on_message(chat: ChatEvent):
    if chat.message.content == "!src":
        src = chat.message.source
        if src:
            chat.channel.send(f"content={src.content}, type={src.type}")

    if chat.message.content == "!room":
        chat.channel.send(f"{chat.channel.name}")

    msg = chat.message.content
    if msg.startswith(".ev "):
        if chat.sender.id != 7886930902727150833:
            return

        try:
            res = eval(msg[4:])
            chat.channel.send(str(res))
        except Exception as e:
            chat.channel.send("Error: " + str(e))

    if chat.message.content == "!Hi":
        chat.channel.send(f"Hello {chat.sender.name}")

    if chat.message.content == "!img":
        with open(ASSETS_PATH / "ririchiyo.webp", "rb") as f:
            chat.channel.send_media("IMAGE", f.read())

    if chat.message.content == "!img2":
        with open(ASSETS_PATH / "ririchiyo.webp", "rb") as f:
            data = f.read()
            chat.channel.send_media("IMAGE", [data] * 4)

    if chat.message.content == "!err":
        0 / 0


@bot.on_event("new_member")
def on_newmem(chat: ChatEvent):
    chat.channel.send(f"Hello {chat.sender.name}")


@bot.on_event("del_member")
def on_delmem(chat: ChatEvent):
    chat.channel.send(f"Bye {chat.sender.name}")


@bot.on_event("error")
def on_error(err: ErrorContext):
    print(err.event, "이벤트에서 오류가 발생했습니다")
    traceback.print_exception(err.exception)


if __name__ == "__main__":
    bot.run()
