import requests
import json

# 读取cookie和token信息
def read_headers_and_token():
    with open('header.txt', 'r') as f:
        headers = f.read().strip()
    with open('token.txt', 'r') as f:
        token = f.read().strip()
    return headers, token

# 定义通用的HTTP头信息
def get_common_headers():
    headers, token = read_headers_and_token()
    common_headers = {
        'Cookie': headers,
        'U-CSRF-Token': token
    }
    return common_headers

# URL编码函数
def urlencode(s):
    import urllib.parse
    return urllib.parse.quote(s)

# 执行POST请求
def post_request(url, data, headers):
    try:
        response = requests.post(url, data=data, headers=headers, timeout=60)
        response.raise_for_status()
    except requests.exceptions.Timeout:
        print("请求超时，请检查网络连接或服务器状态。")
        return None
    except requests.RequestException as e:
        print(f"请求失败: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"JSON解析失败: {e}")
        return None
    else:
        return response.json()