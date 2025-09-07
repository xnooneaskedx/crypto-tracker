import requests

# 替换为你的实际API密钥
API_KEY = "9b39a270-2b3e-436d-8e16-206d5d99b453"

url = "https://pro-api.coinmarketcap.com/v1/global-metrics/quotes/latest"

headers = {
    "Accepts": "application/json",
    "X-CMC_PRO_API_KEY": API_KEY,
}

try:
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    data = response.json()
    print("API密钥验证成功!")
    print(f"状态码: {response.status_code}")
    print("返回数据结构:")
    print(list(data.keys()))
except requests.exceptions.RequestException as e:
    print(f"请求失败: {e}")
except ValueError as e:
    print(f"JSON解析失败: {e}")
