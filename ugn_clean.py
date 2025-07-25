import sys
import time
import requests
from common import get_common_headers
from urllib.parse import urlencode

def usage():
    print("Usage: python ugn_clean.py <ProjectId> <Region> <Zone>")
    print("Example: python ugn_clean.py org-xxxxx cn-bj2 cn-bj2-01")
    sys.exit(1)

if len(sys.argv) != 4:
    usage()

PROJECT_ID, REGION, ZONE = sys.argv[1:4]

def list_ugns():
    url = 'https://api.ucloud.cn/?Action=ListUGN'
    all_ugns = []
    offset = 0
    limit = 100  
    while True:
        payload = {
            "ProjectId": PROJECT_ID,
            "Zone": ZONE,
            "Region": REGION,
            "Limit": limit,
            "Offset": offset,
            "Action": "ListUGN",
            "_timestamp": int(time.time() * 1000)
        }
        resp = requests.post(url, headers=get_common_headers(), json=payload)
        try:
            data = resp.json()
        except Exception:
            print("查询 UGN 列表失败:", resp.text)
            sys.exit(1)
        if 'UGNs' not in data or not data['UGNs']:
            break
        all_ugns.extend([ugn['UGNID'] for ugn in data['UGNs']])
        if len(data['UGNs']) < limit:
            break
        offset += limit
    if not all_ugns:
        print("未找到任何 UGN")
        sys.exit(0)
    return list(set(all_ugns))

def get_networks(ugnid):
    url = 'https://api.ucloud.cn/?Action=GetUGNNetworks'
    payload = {
        "ProjectId": PROJECT_ID,
        "Zone": ZONE,
        "Region": REGION,
        "UGNID": ugnid,
        "Action": "GetUGNNetworks",
        "_timestamp": int(time.time() * 1000)
    }
    resp = requests.post(url, headers=get_common_headers(), json=payload)
    try:
        data = resp.json()
    except Exception:
        print("查询 UGN 绑定网络实例失败:", resp.text)
        return []
    return [net['NetworkID'] for net in data.get('Networks', [])]

def detach_networks(ugnid, networks):
    url = 'https://api.ucloud.cn/?Action=DetachUGNNetworks'
    params = {
        "ProjectId": PROJECT_ID,
        "Region": REGION,
        "UGNID": ugnid,
        "Action": "DetachUGNNetworks",
        "_timestamp": int(time.time() * 1000)
    }
    for i, net in enumerate(networks):
        params[f'Networks[{i}]'] = net

    # 获取通用头部，并设置正确的 Content-Type
    headers = get_common_headers().copy()
    headers['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8'

    resp = requests.post(url, headers=headers, data=urlencode(params))
    try:
        data = resp.json()
        if data.get('RetCode', 0) != 0:
            print(f"解绑失败: {data}")
        else:
            print("解绑成功")
    except Exception:
        print(f"解绑请求异常: {resp.text}")

def del_ugn(ugnid, retry=3):
    url = 'https://api.ucloud.cn/?Action=DelUGN'
    payload = {
        "ProjectId": PROJECT_ID,
        "Zone": ZONE,
        "Region": REGION,
        "UGNID": ugnid,
        "Action": "DelUGN",
        "_timestamp": int(time.time() * 1000)
    }
    for attempt in range(1, retry + 1):
        resp = requests.post(url, headers=get_common_headers(), json=payload)
        try:
            data = resp.json()
            if data.get('RetCode', 0) == 0:
                print(f"UGN {ugnid} 删除成功")
                return True
            else:
                print(f"删除失败: {ugnid}, 返回: {data}，第{attempt}次重试")
                time.sleep(2)
        except Exception:
            print(f"删除请求异常: {ugnid}, {resp.text}，第{attempt}次重试")
            time.sleep(2)
    print(f"UGN {ugnid} 删除最终失败，请手动检查！")
    return False       

def main():
    ugns = list_ugns()
    print("找到以下 UGN：")
    print('\n'.join(ugns))
    # 遍历每个 UGN 进行解绑和删除操作
    for ugnid in ugns:
        time.sleep(1)
        print(f"正在解绑 UGN: {ugnid}")
        networks = get_networks(ugnid)
        if not networks:
            print("未找到任何 UGN 绑定网络实例")
            continue
        detach_networks(ugnid, networks)
        print("解绑完成...")
    print("所有 UGN 解绑 VPC 操作已完成！")
    # 删除所有 UGN
    for ugnid in ugns:
        time.sleep(1)
        print(f"正在删除 UGN: {ugnid}")
        del_ugn(ugnid)
        print("删除完成...")
    print("所有 UGN 删除操作已完成！")

if __name__ == '__main__':
    main()