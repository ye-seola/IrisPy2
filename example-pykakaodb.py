from irispy2.compat.pykakaodb import LegacyBot, KakaoDB, Replier
import threading

from irispy2.compat.pykakaodb.context import copy_context

bot = LegacyBot(iris_endpoint="http://192.168.35.144:3000")


# @bot.response를 추가해주세요
@bot.response
def response(
    room: str, msg: str, sender: str, replier: Replier, msg_json, db: KakaoDB, g: dict
):
    if msg == "!cnt":
        cnt = g.get("cnt", 0)
        g["cnt"] = cnt + 1

        replier.reply(f"count ({cnt} -> {cnt + 1})")

    if msg == "!hi":
        replier.reply(f"hello {sender} (room={room})")

    if msg == "!test":
        print(1, db.check_new_db())
        print(2, db.get_column_info("chat_logs"))
        print(3, db.get_table_info())
        print(4, db.get_name_of_user_id(msg_json["user_id"]))
        print(5, db.get_user_info(msg_json["chat_id"], msg_json["user_id"]))
        print(6, db.get_row_from_log_id(msg_json["id"]))
        print(7, db.log_to_dict(msg_json["id"]))

    if msg == "!test2":
        # 이 코드는 오류가 뜹니다!! thread 사용시 @copy_context를 사용해주세요
        def task():
            db2 = KakaoDB()
            print(1, db2.check_new_db())
            replier.reply("Good")

        threading.Thread(target=task).start()

    if msg == "!test3":

        @copy_context
        def task():
            db2 = KakaoDB()
            print(1, db2.check_new_db())
            replier.reply("Good")

        threading.Thread(target=task).start()


if __name__ == "__main__":
    bot.run(port=9870)
