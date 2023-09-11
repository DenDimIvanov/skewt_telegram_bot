import os
from typing import Dict, List

from langchain.agents import AgentType, initialize_agent

from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.prompts import MessagesPlaceholder
from langchain.tools import tool

llm = ChatOpenAI(model="gpt-3.5-turbo")

#база данных телефонов
stuff_database = [
    {"name": "iPhone 8 mini", "price": 300, "memory": 128, "ram": 8, "camera": 12, "description": "Самая дешевая модель iPhone"},
    {"name": "iPhone 14", "price": 1000, "memory": 128, "ram": 8, "camera": 12, "description": "Телефон будущего, уже сегодня!"},
    {"name": "Samsung Galaxy S23", "price": 900, "memory": 256, "ram": 12, "camera": 108, "description": "Камера такая острая, что сможет увидеть даже ваши ошибки"},
    {"name": "Google Pixel 7", "price": 850, "memory": 128, "ram": 8, "camera": 16, "description": "Для тех, кто хочет получить стоковый Android и хорошие фотки"},
    {"name": "OnePlus 9T", "price": 700, "memory": 128, "ram": 8, "camera": 48, "description": "Зарядка быстрее, чем ваш кофе"},
    {"name": "Xiaomi Mi 12", "price": 600, "memory": 128, "ram": 6, "camera": 64, "description": "Бюджетный флагман для ценителей вкуса"},
    {"name": "Sony Xperia 3", "price": 1100, "memory": 256, "ram": 12, "camera": 20, "description": "Телефон для тех, кто скучал по кнопке для камеры"},
    {"name": "Huawei P60", "price": 800, "memory": 128, "ram": 8, "camera": 50, "description": "Для любителей ночной съемки и без Google Play"},
    {"name": "Nokia 10 PureView", "price": 750, "memory": 128, "ram": 6, "camera": 48, "description": "Nokia вернулась, и у неё есть змейка!"},
    {"name": "LG Velvet 2", "price": 650, "memory": 128, "ram": 8, "camera": 32, "description": "Потому что жизнь хороша"},
    {"name": "Asus ROG Phone 6", "price": 1000, "memory": 512, "ram": 16, "camera": 64, "description": "Играй как профи, заряжай как новичок"},
    {"name": "Motorola Edge Plus", "price": 700, "memory": 128, "ram": 8, "camera": 108, "description": "Край к краю, пиксель к пикселю"},
    {"name": "Realme X4 Pro", "price": 450, "memory": 128, "ram": 8, "camera": 48, "description": "Экономия без потерь в качестве"},
    {"name": "Oppo Find X4", "price": 900, "memory": 256, "ram": 12, "camera": 50, "description": "Найди X, но без математики"},
    {"name": "BlackBerry Secure", "price": 1200, "memory": 128, "ram": 8, "camera": 12, "description": "Для тех, кто ещё помнит, что такое физическая клавиатура"},
    {"name": "Fairphone 4", "price": 500, "memory": 64, "ram": 4, "camera": 12, "description": "Этичный выбор для заботливого потребителя"}
]


@tool
def get_all_phone_names(txt: str) -> List[str]:
    """Возвращает названия моделей всех телефонов через запятую"""
    # Print with green color
    print("\033[92m" + "Bot requested get_all_phone_names" + "\033[0m")
    return [stuff["name"] for stuff in stuff_database]

@tool
def get_phone_data_by_name(name: str) -> Dict:
    """Возвращает цену, характеристики и описание телефона по строгому названию модели"""
    print("\033[92m" + f"Bot requested get_phone_data_by_name({name})" + "\033[0m")
    for stuff in stuff_database:
        if stuff["name"] == name:
            return stuff
    return None

@tool
def create_order(name: str, phone: str, enshurance: str) -> str:
    """Создает новый заказ на телефон. Для заказа нужно передать название телефона,
    телефонный номер пользователя и информацию о том, нужна ли ему страховка"""
    print("\033[92m" + f"Bot requested create_order({name}, {phone}, {enshurance})" + "\033[0m")
    print(f"!!! NEW ORDER !!! {name} {phone} {enshurance}")
    return "OK"


agent_kwargs = {
    "extra_prompt_messages": [MessagesPlaceholder(variable_name="memory")],
}
memory = ConversationBufferMemory(memory_key="memory", return_messages=True)

system = "Ты бот-продавец телефонов. Твоя задача продать телефон пользователю, получив от него заказ"

agent_chain = initialize_agent(
    [get_all_phone_names, get_phone_data_by_name, create_order],
    llm,
    agent=AgentType.OPENAI_FUNCTIONS,
    verbose=False,
    agent_kwargs=agent_kwargs,
    memory=memory,
    agentArgs={
        "systemMessage": system
    },
)

print("\033[94m" + "System: " + system + "\033[0m")
while True:
    q = input("User: ")
    resp = agent_chain.run(input=q)
    print(f"\033[94mBot: {resp}\033[0m")
