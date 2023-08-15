import datetime
from typing import List, Optional
from metpy.units import units
import ast
import requests


_epoc = datetime.datetime(1970, 1, 1)
_update_times = [0, 6, 12, 18]
_forecast_offsets = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 18, 24, 36, 48, 60, 72, 84, 96, 108, 120, 144, 168, 192]


def seconds_from_epoc(day: datetime.date, hours: int = 0) -> int:
    if not day:
        print("From seconds_rom_epoc: day is not recognized")
        return None
    else:
        dt = datetime.datetime(day.year, day.month, day.day, hours)
        diff = dt - _epoc
        return int(diff.total_seconds())

def find_nearest(given:int, arr:List[int])->Optional[int]:
    smallests = [num for num in arr if num<given]
    nearest = max(smallests) if smallests else None
    return nearest

def get_forecast_offset(requested_time:datetime.datetime):
    current_time = datetime.datetime.utcnow()

    offset = (requested_time - current_time).total_seconds()/3600
    if offset < 0:
        print("date in the past")
        return None


    #last update of forecast hours
    hour_of_latest_forecast_update = find_nearest(current_time.hour, _update_times)
    offset += current_time.hour - hour_of_latest_forecast_update

    #find nearest forecast offset
    offset = find_nearest(offset, _forecast_offsets)

    return offset

def is_forecast_intent_exist(s:str)->bool:
    if "{'intent': 'forecast'}" in s:
        return True
    else:
        return False

def prepare_entity_messages(rq:str):

    entity_system_promt = """Ты извлекаешь сущности Город и Дата из заданной строки.  
     Значение Даты можно рассчитать используя текущую дату: """
    entity_system_promt += datetime.datetime.utcnow().date().strftime('%d %b %Y')
    entity_system_promt += """ Если не определена сущность, выдай соответствующее сообщение.
    Если сущности Город и Дата определены, то верни структуру {'city': town, 'day': date}.
    где town - значение сущности Город. date - значение сущности Дата в формате %d %m %Y"""
    entity_sys_role = {"role": "system", "content": entity_system_promt}

    entity_user_content = 'извлеки сущности Город и Дата из сообщения: ' + rq

    entity_user_role = {"role": "user", "content": entity_user_content}

    return [entity_sys_role, entity_user_role]


def prepare_coord_messages(city:str):
    coord_system_promt = """Ты определяешь по названию Города координаты: широту (latitude) и долготу (longitude).
                            Если город называется Кончинка, то latitude = 54.41, longitude = 38.1 Ответ всегда
                            возвращаешь в виде структуры: {'lon': longitude, 'lat': latitude} и больше ничего 
                            возвращать не надо"""

    coord_sys_role = {"role": "system", "content": coord_system_promt}

    coord_user_content = 'какие координаты для: ' + city

    coord_user_role = {"role": "user", "content": coord_user_content}

    return [coord_sys_role, coord_user_role]

def extract_brackets(text):
    start = text.find('{')
    end = text.find('}')
    if start != -1 and end != -1 and end > start:
        return text[start:end+1]
    else:
        return None

def string_to_dict(text):
    try:
        result = ast.literal_eval(text)
        if isinstance(result, dict):
            return result
        else:
            return None
    except (SyntaxError, ValueError):
        return None

def get_coordinates(city_name, api_key):
    base_url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        "address": city_name,
        "key": api_key,
    }
    response = requests.get(base_url, params=params)
    if response.status_code == 200:
        data = response.json()
        if 'results' in data and len(data['results']) > 0:
            geometry = data['results'][0]['geometry']
            location = geometry['location']
            return location['lat'], location['lng']
    return None

# Пример использования функции
# city_name = "Moscow"
# api_key = "ВАШ_КЛЮЧ_API"
# lat, lng = get_coordinates(city_name, api_key)
# print(f"Coordinates of {city_name}: {lat}, {lng}")


def gradient_to_color(temp_grad: List[float]) -> List[str]:

    pass

if __name__ == '__main__':
    print(is_forecast_intent_exist('  dfdfadfljjdf forecast'))
    print(is_forecast_intent_exist("{'intent': 'forecast'}"))
    print(is_forecast_intent_exist("dafdafs {'intent': 'forecast'} dfdsf"))
    print(prepare_entity_messages("какой прогноз в кончинке завтра"))



