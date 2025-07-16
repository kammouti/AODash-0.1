import requests

url = "http://127.0.0.1:5000/pointerinsert"
data = {"station_id": 19, "counter": 767}

response = requests.post(url, json=data)
print(response.json())