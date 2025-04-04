import json
import logging
import os
import sys
import time

import requests
from config import keys
import video_converter

# Bot token from Telegram BotFather
bot_token = keys['bot_token']
api = f'https://api.telegram.org/bot{bot_token}/'

# Bot statement
bot_statement = keys['bot_statement']
# Bot nickname
bot_nickname = r'[TestBot]{1}'
# Bot username
bot_username = '@username'
group_user_nickname = ""
# Allowed group and the enable status of the group
group = {
    keys['default_group']: True
}
block_user = []
# log
log_file = 'data/bot.log'
logging.basicConfig(filename=log_file,
                    level=logging.INFO)
bot_enable = True


# Logging
def log_message(update):
    user_name = update['message']['from_user']['user_name']
    chat_name = update['chat']['chat_name']
    is_bot = update['message']['from_user']['is_bot']
    message_type = update['message']['message_type']
    message_content = update['message']['text']

    logging.info(
        '%(asctime)s - %(user_name)s - %(chat_name)s - %(is_bot)s - %(message_type)s - %(message_content)s',
        {'asctime': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()), 'user_name': user_name,
         'chat_name': chat_name, 'is_bot': is_bot,
         'message_type': message_type,
         'message_content': message_content})


# Fetch the information of bot
def getMe():
    return json.loads(requests.get(api + 'getMe').content)


# Reply to message via bot
def telegram_bot_sendText(bot_msg, chat_id, msg_id):
    data = {
        'chat_id': chat_id,
        'text': bot_msg,
        'reply_to_message_id': msg_id
    }
    url = api + 'sendMessage'

    response = requests.post(url, data=data)
    return response.json()


# Send text via bot
def telegram_bot_send(bot_msg, chat_id):
    data = {
        'chat_id': chat_id,
        'text': bot_msg,
    }
    url = api + 'sendMessage'

    response = requests.post(url, data=data)
    return response.json()


# Send photo via bot
def telegram_bot_sendImage(image_url, chat_id, msg_id):
    url = api + 'sendPhoto'
    data = {
        'chat_id': chat_id,
        'reply_to_message_id': msg_id
    }
    with open(image_url, "rb") as photo:
        files = {
            "photo": photo
        }
        response = requests.post(url, data=data, files=files)
    if os.path.exists(image_url):
        os.remove(image_url)
    return response.json()


# Send video via bot
def telegram_bot_sendVideo(video_path, chat_id, msg_id=None):
    url = api + 'sendVideo'
    data = {
        'chat_id': chat_id,
        'reply_to_message_id': msg_id
    }

    with open(video_path, "rb") as video:
        files = {
            "video": video
        }
        response = requests.post(url, data=data, files=files)

    if os.path.exists(video_path):
        os.remove(video_path)

    return response.json()


# Fetch photo via bot
def telegram_bot_get_file(file_id, update_id, file_type):
    # Fetch the location of the photo in Telegram server
    location = api + 'getFile?file_id=' + file_id
    response = requests.get(location)
    response_dict = response.json()
    file_path = response_dict['result']['file_path']
    # Download the image
    file_url = 'https://api.telegram.org/file/bot' + bot_token + '/' + file_path
    response = requests.get(file_url)
    if response.status_code == 200:
        with open(f'cache/{update_id}.{file_type}', 'wb') as f:
            f.write(response.content)
    return file_url


def task():
    # Fetch the current document location
    cwd = os.getcwd()
    # Get the timestamp in timer_log.txt or create a new one if it isn't existed
    timer_log = cwd + '/data/timer_log.txt'
    if not os.path.exists(timer_log):
        with open(timer_log, "w") as f:
            f.write('1')
    # else:
    # print("Timer Log Exists")

    with open(timer_log) as f:
        last_update = f.read()

    # Set offset based on timestamp to fetch the latest messages
    url = f'{api}getUpdates?offset={last_update}'
    response = requests.get(url)
    data = json.loads(response.content)
    global bot_enable

    # Read the data
    for res in data['result']:
        try:
            if 'message' in res:
                comment = ''
                update_id = res['update_id']
                chat_id = res['message']['chat']['id']
                msg_id = res['message']['message_id']
                # If data type is photo
                if 'text' in res['message']:
                    comment = res['message']['text']
                elif 'caption' in res['message']:
                    comment = res['message']['caption']

                # Renew the timestamp
                with open(timer_log, "w") as f:
                    f.write(f'{update_id}')

                if float(update_id) > float(last_update) and comment != "":
                    if not res['message']['from']['is_bot']:
                        group_name = res['message']['chat']['title'] if 'title' in res['message']['chat'] else \
                            res['message']['chat']['type']
                        group_id = res['message']['chat']['id']
                        user_name = res['message']['from']['first_name']
                        message_type = res['message']['chat']['type']

                        # Check is the bot is allowed to use in the group, and the bot is enabled
                        if group_id in group or group_name == 'private':
                            # Set the log contents
                            update = {'message': {'from_user': {'user_name': user_name, 'is_bot': 'False'},
                                                  'message_type': message_type,
                                                  'text': comment.replace("\n", "").replace("\t", "")},
                                      'chat': {'chat_name': group_name}}
                            if bot_enable:

                                # Disable the bot in a group
                                if '/disable_bot' in comment:
                                    bot_enable = False
                                    update['message']['message_type'] = 'command disable the bot'
                                    log_message(update)
                                    print(telegram_bot_send('Bot disabled', chat_id))

                                # Return the introduction of the bot
                                elif '/info' in comment:
                                    bot_info = getMe()
                                    bot_response = "I'm a Telegram auto reply BOT - " + f"{bot_info['result']['first_name']}"
                                    update['message']['message_type'] = 'command get the bot info'
                                    log_message(update)
                                    print(telegram_bot_send(bot_response + "\n" + bot_statement, chat_id))

                                elif '/convert' in comment:
                                    update['message']['message_type'] = 'command convert video'

                                    if 'video' in res['message']:
                                        file_type = res['message']['video']['mime_type'].split("/")[-1]
                                        file_id = res['message']['video']['file_id']
                                        telegram_bot_get_file(file_id, update_id, file_type)
                                        input_file = f'cache/{update_id}.{file_type}'
                                        output_file = f'cache/output_{update_id}.avi'
                                        video_converter.convert_mp4_to_avi(input_file, output_file)
                                        print(telegram_bot_sendVideo(f'cache/output_{update_id}.avi', chat_id, msg_id))
                                    else:
                                        print(telegram_bot_send("Please send with the video", chat_id))

                                    log_message(update)

                            # Enable the bot in a group
                            if '/enable_bot' in comment:
                                bot_enable = True
                                update['message']['message_type'] = 'command enable the bot'
                                log_message(update)
                                print(telegram_bot_send('Bot enabled', chat_id))

        except Exception as e:
            logging.error(e)


if __name__ == "__main__":
    # Loading cookies

    print(getMe())

    try:
        while True:
            task()
            # time.sleep(5)
    except BaseException as e:
        logging.error(e)
    finally:
        sys.exit()
