import json
import logging
import os

from flask import Flask, request, jsonify

from geo import get_distance, get_geo_info

app = Flask(__name__)

# Добавляем логирование в файл.
logging.basicConfig(level=logging.INFO, filename='app.log',
                    format='%(asctime)s %(levelname)s %(name)s %(message)s')

sessionStorage = {}

@app.route('/post', methods=['POST'])
def main():
    logging.info('Request: %r', request.json)
    response = {
        'session': request.json['session'],
        'version': request.json['version'],
        'response': {
            'end_session': False
        }
    }
    handle_dialog(response, request.json)
    logging.info('Request: %r', response)
    return json.dumps(response)


@app.route('/')
def main2():
    return jsonify("Alice geo map is work!")


def handle_dialog(res, req):
    user_id = req['session']['user_id']

    if req['session']['new']:
        res['response']['text'] = 'Привет! Назови своё имя!'
        res["response"]["buttons"] = [{"title": "Помощь", "hide": True}]
        sessionStorage[user_id] = {
            'first_name': None,  # здесь будет храниться имя пользователя
            'game_started': False  # здесь информация о том, что пользователь начал игру. По умолчанию False
        }
        return

    if sessionStorage[user_id]['first_name'] is None:
        first_name = get_first_name(req)
        if first_name is None:
            res['response']['text'] = 'Не расслышала имя. Повтори, пожалуйста!'
        else:
            sessionStorage[user_id]['first_name'] = first_name

    first_name = sessionStorage[user_id]['first_name']

    if not sessionStorage[user_id]['game_started']:
        res['response']['text'] = f'Привет, {first_name}! Я могу показать город или сказать расстояние между городами!'
        sessionStorage[user_id]['game_started'] = True
        return

    # Получаем города из нашего
    cities = get_cities(req)
    if not cities:
        res['response']['text'] = f'{first_name}, ты не написал название не одного города!'
    elif len(cities) == 1:
        res['response']['text'] = f'{first_name}, этот город в стране - ' + \
                                  get_geo_info(cities[0], 'country')
    elif len(cities) == 2:
        distance = get_distance(get_geo_info(
            cities[0], 'coordinates'), get_geo_info(cities[1], 'coordinates'))
        res['response']['text'] = f'{first_name}, расстояние между этими городами: ' + \
                                  str(round(distance)) + ' км.'
    else:
        res['response']['text'] = f'{first_name}, слишком много городов!'

def get_first_name(req):
    # перебираем сущности
    for entity in req['request']['nlu']['entities']:
        # находим сущность с типом 'YANDEX.FIO'
        if entity['type'] == 'YANDEX.FIO':
            # Если есть сущность с ключом 'first_name', то возвращаем её значение.
            # Во всех остальных случаях возвращаем None.
            return entity['value'].get('first_name', None)

def get_cities(req):
    cities = []
    for entity in req['request']['nlu']['entities']:
        if entity['type'] == 'YANDEX.GEO':
            if 'city' in entity['value']:
                cities.append(entity['value']['city'])
    return cities


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5001))
    app.run(host='0.0.0.0', port=port)
    #app.run()

