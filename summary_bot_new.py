import io
import json
import os
import re
import threading
import time
import traceback
import urllib.parse
import uuid
from io import BytesIO
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Sequence, Union
from urllib.parse import unquote, urlparse
from uuid import UUID

import telebot
# from PyPDF2 import PdfReader
import trafilatura
from langchain.callbacks.base import BaseCallbackHandler
from langchain.callbacks.manager import CallbackManagerForLLMRun
from langchain.chains import RetrievalQA
from langchain.chains.summarize import load_summarize_chain
from langchain.chat_models.gigachat import GigaChat
from langchain.chat_models import ChatOpenAI
from langchain.document_loaders import WebBaseLoader, WikipediaLoader
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.prompts import PromptTemplate
from langchain.schema.messages import BaseMessage
from langchain.schema.output import LLMResult
from langchain.text_splitter import CharacterTextSplitter
from langchain.text_splitter import RecursiveCharacterTextSplitter
# from langchain.vectorstores import Chroma
from langchain.vectorstores import FAISS
from trafilatura.settings import use_config

#import tg_tools

bot = telebot.TeleBot(os.getenv("TG_TOKEN"))  # Prod
# os.environ["OPENAI_API_KEY"]

### Prompts

from langchain.prompts import load_prompt

map_prompt = load_prompt('lc://prompts/summarize/map_reduce/map.yaml')
combine_prompt = load_prompt('lc://prompts/summarize/map_reduce/combine.yaml')

### Code

# Локальное хранилище пользовательских данных
memory = {}


class LoggingGigaChat(GigaChat):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _log_requests(
        self, request, response, model_name, user_id, session_id="", url=""
    ):
        with open("log.jsonl", "a", encoding="utf-8") as f:
            data = {
                "model": model_name,
                "user_id": user_id,
                "request": request,
                "response": response,
                "session_id": session_id,
                "url": url,
            }
            # Append to file
            f.write(json.dumps(data, ensure_ascii=False) + "\n")

    def _call(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        message_dicts = [self.convert_message_to_dict(m) for m in messages]
        # Call parent method
        resp = super()._call(messages, stop, run_manager, **kwargs)
        self._log_requests(
            message_dicts,
            resp,
            "giga",
            run_manager.inheritable_metadata["user_id"],
            run_manager.inheritable_metadata["session_id"],
            run_manager.inheritable_metadata.get("url", None),
        )

        return resp


giga = LoggingGigaChat(
    profanity=False,
    verbose=True,
    user="ddmitivanov",
    password="bKlpW9DaKyRy",
)


#giga = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.4)
#giga = ChatOpenAI(model="gpt-4", temperature=0.4)


embeddings = OpenAIEmbeddings()


def _extract_links(text):
    url_pattern = re.compile(
        r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F])|[^\x00-\x7F])+"
    )

    urls = re.findall(url_pattern, text)
    return urls


def extract_wikipedia_article_title(url):
    parts = urllib.parse.urlsplit(url)
    title_encoded = parts.path.split("/")[-1]
    title = urllib.parse.unquote(title_encoded)
    title = title.replace("_", " ")

    return title


def summarize(url, user_id, message=None):
    docs = []
    chain = None
    splitted_docs = []
    splitter = RecursiveCharacterTextSplitter(chunk_size=8000, chunk_overlap=200)
    splitter_mini = CharacterTextSplitter(chunk_size=500, chunk_overlap=0)
    if ".wikipedia.org/" in url:
        title = extract_wikipedia_article_title(url)
        docs = WikipediaLoader(
            query=title, lang="ru", load_max_docs=1, doc_content_chars_max=200000
        ).load()
        chunks = splitter.split_documents(docs)
        chunks_mini = splitter_mini.split_documents(docs)
    else:
        downloaded = trafilatura.fetch_url(url)
        newconfig = use_config()
        newconfig.set("DEFAULT", "EXTRACTION_TIMEOUT", "0")
        extracted = trafilatura.extract(
            downloaded,
            output_format="txt",
            favor_precision=True,
            include_comments=False,
            include_formatting=True,
            include_tables=True,
            include_images=False,
            include_links=False,
            deduplicate=True,
            config=newconfig,
        )
        texts = splitter.split_text(extracted)
        texts_mini = splitter_mini.split_text(extracted)
        chunks = splitter.create_documents(texts=texts)
        chunks_mini = splitter_mini.create_documents(texts=texts_mini)

    if user_id not in memory:
        memory[user_id] = {}
    if "chunks" in memory[user_id]:
        memory[user_id]["chunks"].extend(chunks)
    else:
        memory[user_id]["chunks"] = chunks
    if "chunks_mini" in memory[user_id]:
        memory[user_id]["chunks_mini"].extend(chunks_mini)
    else:
        memory[user_id]["chunks_mini"] = chunks_mini

    memory[user_id]["url"] = url
    memory[user_id]["session_id"] = str(uuid.uuid4())
    memory[user_id].pop("docsearch", None)

    if len(chunks) > 20:
        memory[user_id]["chunks"] = []
        memory[user_id]["url"] = ""
        return "Извините, статья слишком длинная!"
    if len(chunks) == 1:
        chain = load_summarize_chain(giga, chain_type="stuff", prompt=combine_prompt)
    else:
        chain = load_summarize_chain(
            giga,
            chain_type="map_reduce",
            map_prompt=map_prompt,
            combine_prompt=combine_prompt,
        )

    metadata = {
        "user_id": user_id,
        "session_id": memory[user_id]["session_id"],
        "url": url,
    }
    res = chain.run(chunks, metadata=metadata)
    return res


@bot.message_handler(func=lambda message: True)
def process_message(message):
    try:
        if message.content_type == "text":
            text = message.text
            links = _extract_links(text)
            user_id = str(message.from_user.id)
            if len(links) > 0:
                bot_mess = bot.send_message(
                    message.chat.id,
                    "Суммаризация...",
                )
                res = summarize(links[0], user_id, message=message) + "\n\nВы можете задать мне дополнительные вопросы по статье."
                bot.send_message(message.chat.id, res)
                # bot.edit_message_text(
                #     f"Summary:\n\n{res}", message.chat.id, bot_mess.message_id
                # )
            else:
                if user_id in memory and "chunks" in memory[user_id]:
                    chunks_mini = memory[user_id]["chunks_mini"]
                    if "docsearch" not in memory[user_id]:
                        docsearch = FAISS.from_documents(chunks_mini, embeddings)
                        memory[user_id]["docsearch"] = docsearch
                    bot_mess = bot.send_message(message.chat.id, "Готовлю ответ...")
                    qa = RetrievalQA.from_chain_type(
                        giga,
                        chain_type="stuff",
                        retriever=memory[user_id]["docsearch"].as_retriever(),
                    )
                    metadata = {
                        "user_id": user_id,
                        "session_id": memory[user_id]["session_id"],
                        "url": "",
                    }
                    ans = qa.run(message.text, metadata=metadata)
                    bot.send_message(message.chat.id, ans)
                else:
                    bot.send_message(
                        message.chat.id,
                        "Пришлите мне ссылку на статью, которую нуно суммаризировать.",
                    )

    except Exception as ex:
        print(f"!!! Error: {ex}")
        traceback.print_exc()
        bot.send_message(message.chat.id, f"Пошу прощения, произошла ошибка: {ex}")


def _run_polling_in_loop():
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as ex:
            print(f"!!! Error: {ex}")
            traceback.print_exc()
            time.sleep(5)


if __name__ == "__main__":
    threading.Thread(target=_run_polling_in_loop).start()
#     webserver.app.run(host='0.0.0.0', port=8080)
