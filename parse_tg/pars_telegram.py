from xmlrpc.client import DateTime
from telethon.sync import TelegramClient
from telethon.tl.functions.messages import GetDialogsRequest
from telethon.tl.types import InputPeerEmpty
from telethon.tl.functions.messages import GetHistoryRequest
from telethon.tl.types import PeerChannel
import pandas as pd
import time
from secret_info import api_id, api_hash, phone, password
import csv

client = TelegramClient(phone, api_id, api_hash, system_version='4.16.30-vxCUSTOM', device_model='PC',
                        app_version='5.5.1')

client.start(password=password)
chats = []
last_date = None
chunk_size = 200
groups = []
result = client(GetDialogsRequest(
    offset_date=last_date,
    offset_id=0,
    offset_peer=InputPeerEmpty(),
    limit=chunk_size,
    hash=0
))
chats.extend(result.chats)
for chat in chats:
    try:
        if chat.megagroup:
            groups.append(chat)
    except:
        continue
print("Выберите группу для парсинга сообщений и членов группы:")
i = 0
for g in groups:
    print(str(i) + "- " + g.title)
    i += 1
g_index = input("Введите нужную цифру: ")
target_group = groups[int(g_index)]
print("Парсинг участников группы успешно выполнен.")

offset_id = 0
limit = 100
all_messages = []
total_messages = 0
total_count_limit = 0

while True:
    history = client(GetHistoryRequest(
        peer=target_group,
        offset_id=offset_id,
        offset_date=None,
        add_offset=0,
        limit=limit,
        max_id=0,
        min_id=0,
        hash=0
    ))
    if not history.messages:
        break
    messages = history.messages
    for message in messages:
        all_messages.append(message.to_dict())
    offset_id = messages[len(messages) - 1].id
    if total_count_limit != 0 and total_messages >= total_count_limit:
        break

text_all_message = []
for i in range(len(all_messages)):
    try:
        text_all_message.append(all_messages[i]['message'])
    except:
        pass

forbidden_symbols = [',', '.', '!', ';', ':']
new_all_message = []
for i in text_all_message:
    if '?' in i and len(i) > 30:
        for symbol in forbidden_symbols:
            i = i.replace(symbol, '')
        i = i.replace('\n', ' ')
        new_all_message.append(i)
    else:
        pass

data = {'text': new_all_message}
df = pd.DataFrame(data=data)
df.to_csv('tg_boltalka_polytech.csv', encoding='utf-8')
print("Сохраняем данные в файл...")
print('Парсинг сообщений группы успешно выполнен.')
