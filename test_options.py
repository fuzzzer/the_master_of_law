import requests
url = "http://127.0.0.1:8000/api/v1/conversations"
headers = {
    "Origin": "http://localhost:55230",
    "Access-Control-Request-Method": "POST",
    "Access-Control-Request-Headers": "content-type"
}
try:
    r = requests.options(url, headers=headers)
    print(r.status_code)
    print(r.headers)
    print(r.text)
except Exception as e:
    print(e)
