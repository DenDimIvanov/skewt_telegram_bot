import os
from langchain.agents import initialize_agent, Tool
from langchain.agents import AgentType
from langchain.chat_models import ChatOpenAI
from langchain.schema.messages import SystemMessage

openai_api_key = os.getenv("OPENAI_API_KEY")
llm = ChatOpenAI(temperature=0, model="gpt-4", openai_api_key=openai_api_key)
system = "Ты бот-продавец телефонов. Твоя задача продать телефон пользователю, получив от него заказ. Необходимые для заказа данные уточняй у пользователя. Пиши короткие понятные сообщения."

stuff_database = [
    {"name": "iPhone 8 mini", "price": 300, "memory": 64, "ram": 4, "camera": 8,
     "description": "Самая дешевая модель iPhone"},
    {"name": "iPhone 14", "price": 1000, "memory": 512, "ram": 12, "camera": 12,
     "description": "Телефон будущего, уже сегодня!"},
    {"name": "Samsung Galaxy S23", "price": 900, "memory": 256, "ram": 12, "camera": 108,
     "description": "Камера такая острая, что сможет увидеть даже ваши ошибки"},
    {"name": "Google Pixel 7", "price": 850, "memory": 128, "ram": 8, "camera": 16,
     "description": "Для тех, кто хочет получить стоковый Android и хорошие фотки"},
    {"name": "OnePlus 9T", "price": 700, "memory": 128, "ram": 8, "camera": 48,
     "description": "Зарядка быстрее, чем ваш кофе"},
    {"name": "Xiaomi Mi 12", "price": 600, "memory": 128, "ram": 6, "camera": 64,
     "description": "Бюджетный флагман для ценителей вкуса"},
    {"name": "Sony Xperia 3", "price": 1100, "memory": 256, "ram": 12, "camera": 20,
     "description": "Телефон для тех, кто скучал по кнопке для камеры"},
    {"name": "Huawei P60", "price": 800, "memory": 128, "ram": 8, "camera": 50,
     "description": "Для любителей ночной съемки и без Google Play"},
    {"name": "Nokia 10 PureView", "price": 750, "memory": 128, "ram": 6, "camera": 48,
     "description": "Nokia вернулась, и у неё есть змейка!"},
    {"name": "LG Velvet 2", "price": 650, "memory": 128, "ram": 8, "camera": 32,
     "description": "Потому что жизнь хороша"},
    {"name": "Asus ROG Phone 6", "price": 1000, "memory": 512, "ram": 16, "camera": 64,
     "description": "Играй как профи, заряжай как новичок"},
    {"name": "Motorola Edge Plus", "price": 700, "memory": 128, "ram": 8, "camera": 108,
     "description": "Край к краю, пиксель к пикселю"},
    {"name": "Realme X4 Pro", "price": 450, "memory": 128, "ram": 8, "camera": 48,
     "description": "Экономия без потерь в качестве"},
    {"name": "Oppo Find X4", "price": 900, "memory": 256, "ram": 12, "camera": 50,
     "description": "Найди X, но без математики"},
    {"name": "BlackBerry Secure", "price": 1200, "memory": 128, "ram": 8, "camera": 12,
     "description": "Для тех, кто ещё помнит, что такое физическая клавиатура"},
    {"name": "Fairphone 4", "price": 500, "memory": 64, "ram": 4, "camera": 12,
     "description": "Этичный выбор для заботливого потребителя"}
]
from langchain.prompts import MessagesPlaceholder
from langchain.memory import ConversationBufferMemory

agent_kwargs = {
    "system_message": SystemMessage(content=system),
    "extra_prompt_messages": [MessagesPlaceholder(variable_name="memory")],
}
from langchain.tools import tool
from typing import Dict, List


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
    return {}


@tool
def create_order(model_name: str, enshurance: bool, phone_number: str, additional: dict = {}) -> str:
    """Создает новый заказ на телефон model_name. Для заказа нужно узнать у пользователя номер телефона phone_number и спросить, хочет ли он оформить страховку ($50).

    parameters:
        model_name: название модели телефона
        phone_number: номер телефона пользователя для связи
        enshurance: нужна ли пользователю страховка телефона
        additional: дополнительные данные, которые пользователь может указать при заказе. Может быть пустым, не нужно отдельно спрашивать, если пользователь сам не сказал.

    returns:
        OK в случае успешного заказа
    """
    if not model_name:
        return "Incorrect name parameter"
    if not phone_number:
        return "Incorrect phone parameter"
    print(
        "\033[92m" + f"Bot requested create_order({model_name}, {phone_number}, enshurance={enshurance}, additional={additional})" + "\033[0m")
    return "OK"


memory = ConversationBufferMemory(memory_key="memory", return_messages=True)
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
    if q == "":
        break
    print(f"User: {q}")
    resp = agent_chain.run(input=q)
    print(f"\033[94mBot: {resp}\033[0m")