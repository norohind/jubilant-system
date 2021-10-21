# import json
import requests
import sqlite3
import time
import datetime

"""
request bearer token from capi.demb.design
if there is no token -> exit
loop:
make request for latest known squadron + 1
if +1 squad exists -> write it to db
if new squad have appropriate tags -> report it
goto loop


what to store?
1. History of squadrons changes
2. Current squadrons state
    
"""
db = sqlite3.connect('db.sqlite')

# SquadronTagCollections = json.load(open('available.json', 'r'))['SquadronTagData']['SquadronTagCollections']
ruTag: int = 32

hookURL = 'https://discord.com/api/webhooks/896514472280211477/LIKgbgNIr9Nvuc-1-FfylAIY1YV-a7RMjBlyBsVDellMbnokXLYKyBztY1P9Q0mabI6o'  # noqa: E501

# let's get bearer token
# https://api.orerve.net/2.0/website/squadron/info?platform=PC&squadronId=68879
r = requests.get(url='https://capi.demb.design/users/InIMJmAy9I7XFHDoclQfxAwmPC9xbIwKPOzvGrrRA50=').json()
bearer = r['access_token']

db.execute('create table if not exists squads (ownername text, id int, platform text, created text, created_ts '
           'text, tag text, '
           'inserted text, usertags text, name text, owner_id text);')

try:
    max_known_id: int = db.execute('select id from squads order by id desc limit 1').fetchone()[0]
except TypeError:
    max_known_id: int = 68862

first_retry: bool = True

next_id = max_known_id + 1
# print(f'continuing from {next_id}')
while True:
    r = requests.get(
        url='https://api.orerve.net/2.0/website/squadron/info',
        params={'squadronId': next_id},
        headers={'Authorization': f'Bearer {bearer}'})

    if r.status_code != 200:
        if not first_retry:
            break

        else:
            first_retry = False
            next_id = next_id + 1
            time.sleep(3)
            continue

    squad = r.json()['squadron']

    squad['ownerName'] = bytes.fromhex(squad['ownerName']).decode('utf-8')

    inserted = datetime.datetime.now(tz=datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S')  # in utc
    db.execute('insert into squads '
               '(id, platform, created, created_ts, tag, inserted, usertags, name, ownername, owner_id) values'
               '(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', (squad['id'],
                                                  squad['platform'],
                                                  squad['created'],
                                                  squad['created_ts'],
                                                  squad['tag'],
                                                  inserted,
                                                  str(squad['userTags']),
                                                  squad['name'],
                                                  squad['ownerName'],
                                                  squad['ownerId']))
    db.commit()
    print(squad)

    if ruTag in squad['userTags']:
        message = f"New RU squad: {squad['name']}\ntag: {squad['tag']}\ncreated: {squad['created']}\nplatform: " \
                  f"{squad['platform']}\nowner name: {squad['ownerName']}\nmembers count: {squad['memberCount']}"
        message = requests.utils.quote(message)
        r2 = requests.post(url=hookURL, data=f'content={message}'.encode('utf-8'),
                           headers={'Content-Type': 'application/x-www-form-urlencoded'})

        if r2.status_code != 204:
            print('send failed')

    next_id = next_id + 1
    first_retry = True
    time.sleep(3)
