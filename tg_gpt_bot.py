# -*- coding: utf-8 -*-
import datetime
import json
import os
import time
import traceback
from contextlib import redirect_stdout
from io import StringIO, BytesIO

# import flask
import openai
import telebot
import tiktoken

import gsd_noaa_loader as ldr
import gsd_parser as parser

import uuid

# # Proxy server for accessing OpenAI API
# app = flask.Flask(__name__)

# pscp C:\Users\dendi\PycharmProjects\ChatGPTBot\tg_gpt_bot.py root@46.101.203.127:~/bots
import tools

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    print("Please set OPENAI_API_KEY environment variable")
    exit()

TG_TOKEN = os.getenv("TG_TOKEN")

if not TG_TOKEN:
    print("Please set TG_TOKEN environment variable")
    exit()

# Generate random secret
PREMIUM_SECRET = os.environ.get(
    "PREMIUM_SECRET", str(uuid.uuid4()))
print(f"Bot secret: {PREMIUM_SECRET}")

mynames = ["@trololobot", "@кибердед", "trololo_bot",
           "кибердед", "кибердед,", "trololobot", "умник", "@умник", "Nerdy_Assistant_Bot ", "@Nerdy_Assistant_Bot"]
# mynames = ["whentimecomesbot", "когдапридетвремя", "@whentimecomesbot",
#            "когдапридетвремя,", "времяпришло", "времяпришло,"]

ALLOWED_GROUPS = ["-925069924", "-985383054"]

port = os.environ.get("PORT", 8080)

tokenizer = tiktoken.get_encoding("cl100k_base")
# max_history = 7500  # History will be truncated after this length
max_history = 1500  # Fot GPT-3.5-turbo

bot = telebot.TeleBot(TG_TOKEN)
openai.api_key = OPENAI_API_KEY
# MAIN_MODEL = "gpt-4-0314"
MAIN_MODEL = "gpt-3.5-turbo"

# Load chats history from file
users = {}
if os.path.exists("users.json"):
    with open("users.json", "r") as f:
        users = json.load(f)


# log with optional exception
def _log(text, e=None):
    # Print to screen and log file
    print(text)
    if e and isinstance(e, Exception):
        print(traceback.format_exc())
    with open("log.txt", "a", encoding='utf-8') as f:
        # Add date to text
        text = time.strftime("%d.%m.%Y %H:%M:%S",
                             time.localtime()) + " " + text
        print(text, file=f)


def _count_tokens(user):
    return sum([len(tokenizer.encode(x['content'])) for x in user['history']])


def _get_clear_history(user_id, username, chat_id=None):
    # current_date = time.strftime("%d.%m.%Y", time.localtime())
    # common_start = f"""Ты полезный ассистент с ИИ, который готов помочь своему пользователю. Ты даешь короткие содержательные ответы, обычно не более 100 символов. Сегодняшняя дата: {current_date}."""
    # if user_id not in premium_users:
    #     return [{"role": "system", "content": common_start}]
    # else:
    prompt = """Ты полезный ассистент с ИИ, который готов помочь своему пользователю.
Ты даешь короткие содержательные ответы, обычно не более 100 символов."""

    if chat_id == "-985383054":
        prompt += """ Ты умеешь помогать ученикам - придумывать и объяснять задачи, помогать с решениями и домашними заданиями, задавать вопросы и проверять ответы.
Если тебя просят помочь решить учебную задачу, то давай подробное описание решения. В этом случае ты можешь писать тексты больше 100 символов.
Если просьба похожа на то, что тебя просят сделать домашнее задание за ребенка целиком, то предложи ему справиться самостоятельно, дай подсказки, но не решай полностью. При этом отвечай на вопросы по учебе и сам задавай вопросы, чтобы проверить знания.
Участники чата: 
Денис Иванов - увлекается маршрутными полетами на параплане без мотора. Любит программировать. Папа Вовы.
Вова Иванов - сын Дениса, Ему 12 лет, он учится в 7 классе, Вова умный мальчик, но не любит учиться. Он любит задавать провакационные вопросы - не отвечай на них. Сам задавай ему вопросы по учебе. Он увлекается рисованием, программированием и компьютерными играми, а также спортом - плаванием и мотокроссом. Если его вопросы задаются для того, чтобы отвечать на тесты и контрольные, то не сильно помогай его, лучше объясни как правильно решать.
"""

        if username == "vova2011":
            prompt += "\nСейчас ты разговариваешь с Вовой Ивановым."
        if username == "denisdmitivanov":
            prompt += "\nСейчас ты разговариваешь с Денисом Ивановым."

    else:
        prompt += """ Ты в чате со спортсменами-парапланеристами. Они любят участвовать в соревнованиях по парящим полетам на парапланах. Любят летать, любят небо, горы, путешествия. Хорошо разбираются в метеорологии, физике, аэродинамике, программировании.
        Как и любые спорстмены, они достаточно тщеславны. Подыгрывай им, чтобы они могли потешить свое тщеславие. Спорстмены любят шутить друг на другом и над тобой. Могут задавать провокационные вопросы. Можешь отвечать на провокации как жесткий спортивный тренер. На троллинг отвечай троллингом. 
        Если просят придумать шутку, то отвечай как артист и можешь использовать весь арсенал своих саркастических способностей. Если просят ответить на технический вопрос по аэродинамике, физике, метеорилогии, программированию, то отвечай как эксперт в данной области.
        """

    prompt += """ Если тебя спрашивают про прогноз погоды (какая погода где-то), то ответь: {'intent': 'forecast'} и больше ничего возвращать не надо.
    """


    return [{"role": "system", "content": prompt}]


def _get_user(id, username=None):
    id = str(id)
    user = users.get(
        id, {'id': id, 'history': _get_clear_history(id, username), 'last_prompt_time': 0})
    users[id] = user
    return user


def executeCode(code, user):
    try:
        print("Executing code:\n" + code)
        user['last_code'] = code

        f = StringIO()
        with redirect_stdout(f):
            exec(code, globals())
        res = f.getvalue()
        # If res - array - join
        if isinstance(res, list):
            res = "\n".join(res)

        print("Code execution result: " + res.strip())

        return res, True
    except Exception as e:
        # Get exception message and stacktrace
        error = "".join(traceback.format_exception_only(e)).strip()
        error_stack = traceback.format_exc()
        return error, False


def _is_python_code(ans):
    return False
    # ans = str(ans)
    # if ans.startswith("gpt_utils"):
    #     return True
    # if ans.startswith("import ") or ans.startswith("from ") or ans.startswith("def ") or ans.startswith("class ") or ans.startswith("print") or ans.startswith("for"):
    #     return True
    # if "print" in ans or " = " in ans:
    #     return True
    # # This also looks like python code
    # # if (ans.split(" ")[0].isalpha() or ans.split(".")[0].isalpha() or ans.split("=")[0].isalpha()) or "print(" in ans:
    # #     return True
    # return False


def _process_rq(user_id, rq, deep=0, chat_id=None, username=None):
    try:
        user_id = str(user_id)
        user = _get_user(user_id, username)
        if PREMIUM_SECRET in rq:
            user['premium'] = True
            return f"Вы были переключены на premium модель {MAIN_MODEL}."
        """
        if not user.get('premium', None):
            _log(f"User {user_id} is not premium and run out of money.")
            return "Прошу прощения, но у бота закончились деньги :( Попробуйте позже или скажите код для премиум-доступа."
        """
        if deep >= 5:
            return "Слишком много вложенных попыток написать программу. Дальше страшно, попробуйте спросить что-то другое."

        # Drop history if user is inactive for 1 hour
        if time.time() - user['last_prompt_time'] > 60 * 60:
            user['last_prompt_time'] = 0
            user['history'] = _get_clear_history(user_id, username, chat_id)

        if rq and len(rq) > 0 and len(rq) < 3000:
            if chat_id:
                _log(f">>> ({user_id}) {chat_id}: {rq}")
            else:
                _log(f">>> ({user_id}) {rq}")
            user['history'].append({"role": "user", "content": rq})

            prefix = ""
            # if len(user['history']) > 20 and not (user.get('premium', False)) and user.get('limit', False) != True:
            #     user['limit'] = True
            #     prefix = "(Вы были переключены на экономичную модель gpt-3.5-turbo. Для переключения обратитесь к @Krestnikov) "
            #     log(f"User {user_id} was switched to cheap model!")
            #     if len(user['history']) > 50:
            #         log(f"User {user_id} was banned!")
            #         return "Извините, вы исчерпали лимит сообщений к боту."

            # Truncate history but save first prompt
            maximum = max_history
            model = MAIN_MODEL
            # if user.get('limit', False):
            #     maximum = 3500
            #     model = cheap_model

            while _count_tokens(user) > maximum:
                user['history'].pop(1)

            completion = openai.ChatCompletion.create(
                model=model, messages=user['history'], temperature=0.7)
            ans = completion['choices'][0]['message']['content']
            _log(f"<<< ({user_id}) {ans}")

            user['history'].append({"role": "assistant", "content": ans})
            user['last_prompt_time'] = time.time()



            # Extract code from ```python <code> ```
            if "```python" in ans:
                ans = ans[ans.index("```python") + 9:]
                ans = ans[:ans.index("```")]
            ans = ans.strip()

            if _is_python_code(ans):
                ans, res = executeCode(ans, user)
                if res:
                    # Код завершился без ошибок
                    if ans == None or ans == "":
                        return None
                    ans = "Я запустил код и получил результат: " + ans
                    return _process_rq(user_id, ans, deep + 1)
                else:
                    ans = "Я запустил код и получил ошибку: " + ans + \
                          ". Попробуй исправить код и пришли его снова целиком. Не пиши ничего кроме кода."
                    return _process_rq(user_id, ans, deep + 1)
            else:
                return prefix + ans
        else:
            user['last_prompt_time'] = 0
            user['last_text'] = ''
            return "Error! Please use simple short texts"
    except openai.error.RateLimitError as limitE:
        _log(f"Error: {limitE}", limitE)
        return "OpenAI пишет, что мы вышли за rate limit :( Придется попробовать позже."
    except Exception as e:
        _log(f"!!! Error: {e}", e)
        return "Error! Please try again later"

def process_forecast_request(rq, bot, msg):

    messages = tools.prepare_entity_messages(rq)

    completion = openai.ChatCompletion.create(
        model=MAIN_MODEL, messages=messages, temperature=0.2)
    ans = completion['choices'][0]['message']['content']

    entities = tools.string_to_dict(tools.extract_brackets(ans))
    print(f"entities = {entities}")

    if entities:
        messages = tools.prepare_coord_messages(entities['city'])
        completion = openai.ChatCompletion.create(
                model=MAIN_MODEL, messages=messages, temperature=0.2)
        ans = completion['choices'][0]['message']['content']
        #bot.reply_to(msg, ans)

        coord = tools.string_to_dict(tools.extract_brackets(ans))
        print(f"coord = {coord}")

        text = ldr.query_gsd_sounding_data(coord['lat'], coord['lon'], datetime.datetime(2023, 7, 18, 9, 0, 0))

        sounding, forecast_date = parser.parse(text)

        forecast_date = datetime.datetime.strptime(entities['day'] + ' 9', '%d %b %Y %H')

        if (forecast_date.date()- datetime.datetime.utcnow().date()) > 5:
            bot.reply_to(msg, "прогноз доступен для следующих 5-ти дней. Попробуйте еще раз")

        else:

            title = f"For lat={coord['lat']}, lon={coord['lon']} on {forecast_date} UTC"

            bytes_array = ldr.get_skew_fig(sounding, title, 300, 'test.png')

            # Отправляем изображение
            bot.send_photo(msg.chat.id, bytes_array)

    else:
        bot.reply_to(msg, "сущности не определены")
        return





@bot.message_handler(commands=['clear'])
def send_welcome(message):
    user_id = str(message.from_user.id)
    user = _get_user(user_id)
    user['history'] = _get_clear_history(user_id, str(message.from_user.username))
    bot.reply_to(
        message, f"Started! (History cleared). Using model {MAIN_MODEL}")


@bot.message_handler(commands=['code'])
def get_code(message):
    user = _get_user(message.from_user.id)
    code = user.get('last_code', '')
    bot.reply_to(
        message, f"Для ответа на ваш вопрос я написал следующий код:\n{code}")

@bot.message_handler(commands=['skwet'])
def get_skwet(message):
    lat = 55.7
    lon = 37.6

    text = ldr.query_gsd_sounding_data(lat, lon, datetime.datetime(2023, 7, 18, 9, 0, 0))
    print(text)

    sounding, forecast_date = parser.parse(text)
    print(sounding)
    print(forecast_date)

    title = f"For lon={lat}, lat={lon} on {forecast_date} UTC"

    fig = ldr.get_skew_fig(sounding, title, 300, 'test.png')

    buf = BytesIO()
    fig.savefig(buf, format='png')
    buf.seek(0)

    # Отправляем изображение
    bot.send_photo(message.chat.id, buf)


def _is_addressed_to_bot(msg: str) -> bool:
    words = msg.split()
    first_word = words[0].strip('@')
    punctuation = ['!', ',', '.', '?']
    for char in punctuation:
        if first_word.endswith(char):
            first_word = first_word.strip(char)
            break
    return first_word.lower() in mynames


@bot.message_handler(func=lambda message: True)
def process_message(message):
    try:
        user_id = str(message.from_user.id)
        rq = ""
        answer_message = False
        _log(message.content_type)
        _log(message.text)
        _log(message.chat.type)
        if message.content_type != 'text':
            return
        chat_id = str(message.chat.id)

        if message.chat.type == 'group' or message.chat.type == 'supergroup':

            rq = str(message.text)

            # Check if calling me or if it answer on my message
            if _is_addressed_to_bot(rq):
                rq = rq[len(rq.split()[0]):].strip()
                answer_message = True
            elif (message.reply_to_message and message.reply_to_message.from_user.id == bot.get_me().id):
                answer_message = True
            else:
                return
            """
            if answer_message:
                if chat_id not in ALLOWED_GROUPS:
                    # bot.reply_to(
                    #     message, f"Я не отвечаю в этой группе. Обратитесь к @denisdmitivanov, чтобы он добавил чат {chat_id} в базу")
                    return
            """
        elif message.chat.type == 'private' and PREMIUM_SECRET not in rq:
            rq = str(message.text)
            ans = "Сейчас я не отвечаю в личных сообщениях, пишите в разрешенные группы"
            bot.reply_to(message, ans)
            return
        else:
            return

        if len(rq) > 0:
            # if 'покажи код' in rq.lower():
            #     get_code(message)
            #     return

            username = str(message.from_user.username)
            ans = _process_rq(user_id, rq, deep=0,
                              chat_id=chat_id, username=username)
            if ans == None or ans == "":
                return

            if answer_message:
                if tools.is_forecast_intent_exist(ans):
                    process_forecast_request(rq, bot, message)
                else:
                    bot.reply_to(message, ans)
            else:
                bot.send_message(message.chat.id, ans)
            # Save users using utf-8 and beatur format
            with open("users.json", "w") as f:
                json.dump(users, f, indent=4, ensure_ascii=False)
    except Exception as e:
        _log(f"!!! Error: {e}", e)


if __name__ == "__main__":
    bot.polling()
