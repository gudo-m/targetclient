import requests
import json

api_access_token = '' # '' токен можно получить здесь https://qiwi.com/api
my_login = '+' # '+' номер QIWI Кошелька в формате +79991112233

s = requests.Session()
s.headers['authorization'] = 'Bearer ' + api_access_token
parameters = {'rows': '50', 'operation': 'IN'}
h = s.get('https://edge.qiwi.com/payment-history/v1/persons/'+my_login+'/payments', params=parameters)
doings = json.loads(h.text)['data']
for doing in doings:
    print(doing['account'])
    print(doing['comment'])
    print(doing['total']['amount'])
    print('----------\n\n\n')