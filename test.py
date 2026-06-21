import requests

r = requests.get("http://192.168.137.244/stop")
print(r.status_code)
print(r.text)