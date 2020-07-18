import requests

URL = "http://0.0.0.0:5000/events/new"

"""
r = requests.get(url=URL)

data = r.json()

print(data)
"""

data = {
    'source': "asadasdad",
    'eventType': "fire",
    'location': "istanbul"
}

r = requests.post(url = URL, data = data)

response_Text = r.text

print(response_Text)