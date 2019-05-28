import requests
import time
import telegram
import os
from requests.exceptions import ReadTimeout, ConnectionError, HTTPError


DVMN_API_URL = "https://dvmn.org/api/long_polling/"


def main():
    dvmn_token = os.environ["DVMN_TOKEN"]
    bot_token = os.environ["BOT_TOKEN"]
    chat_id = int(os.environ["CHAT_ID"])

    timestamp = time.time()

    bot = telegram.Bot(token=bot_token)

    while True:
        try:
            r = requests.get(DVMN_API_URL,
                             params={"timestamp": timestamp},
                             headers={"Authorization": dvmn_token},
                             timeout=100)
            r.raise_for_status()
            response_json = r.json()
            if 'error' in response_json:
                raise HTTPError(response_json['error'])
        except (ReadTimeout, ConnectionError):
            continue

        if response_json["status"] == "found":
            timestamp = response_json["last_attempt_timestamp"]
            for attempt in response_json["new_attempts"]:
                bot.send_message(chat_id=chat_id,
                                 text="У вас проверили работу '{}'".format(attempt["lesson_title"]))
                if attempt["is_negative"]:
                    bot.send_message(chat_id=chat_id,
                                     text="К сожалению, в работе нашлись ошибки.")
                else:
                    bot.send_message(chat_id=chat_id,
                                     text="Преподавателю всё понравилось, можно приступать к следующему уроку!")
                bot.send_message(chat_id=chat_id,
                                 text="Ссылка на урок: https://dvmn.org{}".format(attempt["lesson_url"]))
        elif response_json["status"] == "timeout":
            timestamp = response_json["timestamp_to_request"]


if __name__ == '__main__':
    main()
