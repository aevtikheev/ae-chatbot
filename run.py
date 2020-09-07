import time
import logging
import os

import requests
from requests.exceptions import ReadTimeout, ConnectionError, HTTPError
import telegram


BOT_RERUN_TIMEOUT = 60*10

DVMN_API_URL = "https://dvmn.org/api/long_polling/"


class TelegramLogsHandler(logging.Handler):
    def __init__(self, bot_token, chat_id):
        self._bot = telegram.Bot(token=bot_token)
        self._chat_id = chat_id
        super().__init__()

    def emit(self, record):
        log_entry = self.format(record)
        self._bot.send_message(chat_id=self._chat_id, text=log_entry)


def run_dvmn_bot(bot_token, chat_id, dvmn_token):
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
                                 text="У вас проверили работу '{}'"
                                 .format(attempt["lesson_title"]))
                if attempt["is_negative"]:
                    bot.send_message(chat_id=chat_id,
                                     text="К сожалению, в работе нашлись ошибки.")
                else:
                    bot.send_message(chat_id=chat_id,
                                     text="Преподавателю всё понравилось,"
                                          " можно приступать к следующему уроку!")
        elif response_json["status"] == "timeout":
            timestamp = response_json["timestamp_to_request"]


def main():
    dvmn_token = os.environ["DVMN_TOKEN"]
    bot_token = os.environ["BOT_TOKEN"]
    chat_id = int(os.environ["CHAT_ID"])

    logger = logging.getLogger("TelegramLogger")
    logger.setLevel(logging.INFO)
    logger.addHandler(TelegramLogsHandler(bot_token, chat_id))

    while True:
        try:
            run_dvmn_bot(bot_token, chat_id, dvmn_token)
        except Exception as exc:
            logger.exception("Бот умер с ошибкой {}".format(exc))
            time.sleep(BOT_RERUN_TIMEOUT)


if __name__ == '__main__':
    main()
