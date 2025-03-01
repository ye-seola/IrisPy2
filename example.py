import irispy2


class Bot(irispy2.IrisPy):
    def on_message(self, room, sender, message):
        if message.msg == "Hi":
            self.reply(f"Hello {sender.name}")


bot = Bot()
bot.run(port=9870, iris_endpoint="http://192.168.35.144:3000")
