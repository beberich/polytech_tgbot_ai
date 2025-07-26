import json
import time
import csv
import requests
from datetime import datetime
import pandas as pd
from secret_info import domain, version, token


def pars_posts():
    count = 100
    offset = 0
    all_posts = []

    while offset <= 21000:
        response = requests.get('https://api.vk.com/method/wall.get',
                                params={
                                    'access_token': token,
                                    'v': version,
                                    'domain': domain,
                                    'count': count,
                                    'offset': offset
                                })
        data = response.json()['response']['items']
        offset += 100
        all_posts.extend(data)
        time.sleep(0.7)
    s = len(all_posts)
    return all_posts


def to_dataframe(all_posts):
    forbidden_symbols = [',', '.', ';', ':', '!', '\n', 'Анонимно', 'анонимно', 'анон', 'Анон']
    data_text, data = [], []
    for post in all_posts:
        txt = post['text']
        if '?' in txt and 'https://' not in txt:
            for symbol in forbidden_symbols:
                txt = txt.replace(symbol, '')
            if len(txt) > 7:
                data_text.append(txt)
                data.append(datetime.utcfromtimestamp(post['date']).strftime('%Y-%m-%d %H:%M:%S'))
            else:
                pass
        else:
            pass

    data = {'time': data,
            'text': data_text}
    row_labels = [i for i in range(len(data_text))]
    df = pd.DataFrame(data=data)
    df.to_csv('vk_questions_without_index.csv', encoding='utf-8')
    print(df.head())


all_posts = pars_posts()
to_dataframe(all_posts)
