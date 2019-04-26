from room import vk_requests


api = vk_requests.create_api(app_id=6493489, login='', password='', proxies={'http': 'http://5NetqS:M5cXTh@185.204.109.32:8000','https': 'http://5NetqS:M5cXTh@185.204.109.32:8000'})
print(api.users.get(user_ids=1))