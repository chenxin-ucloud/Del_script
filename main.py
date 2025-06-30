import json
import time
from common import get_common_headers, post_request

def main(project_id):
    try:
        # 读取JSON文件，指定编码为utf-8
        with open('region.json', 'r', encoding='utf-8') as f:
            regions_data = json.load(f)
    except FileNotFoundError:
        print("错误: region.json文件未找到")
        return
    except json.JSONDecodeError:
        print("错误: region.json文件格式错误")
        return
    except Exception as e:
        print(f"发生未知错误: {e}")
        return

    regions = regions_data.keys()
    common_headers = get_common_headers()

    # 遍历每个区域
    for region in regions:
        region_info = regions_data[region]
        REGION = region_info['Region']
        ZONE = region_info['Zone']

        print(f"\n\n------------------------------------------------")
        print(f"操作地域: {region} (Region: {REGION}, Zone: {ZONE})")
        print(f"------------------------------------------------\n\n")

        # 执行删除UHost、UDisk、EIP、ALB、NATGW等资源
        try:
            delete_host(project_id, REGION, ZONE, common_headers)
            delete_disk(project_id, REGION, ZONE, common_headers)
            delete_eip(project_id, REGION, ZONE, common_headers)
            delete_alb(project_id, REGION, ZONE, common_headers)
            delete_natgw(project_id, REGION, ZONE, common_headers)
            delete_networkinterface(project_id, REGION, ZONE, common_headers)
        except Exception as e:
            print(f"在操作地域 {region} 时发生错误: {e}")
            continue

    # 再次遍历每个区域，删除子网和VPC
    for region in regions:
        region_info = regions_data[region]
        REGION = region_info['Region']
        ZONE = region_info['Zone']

        print(f"\n\n-----------------------------------------------")
        print(f"操作地域: {region} (Region: {REGION}, Zone: {ZONE})")
        print(f"-----------------------------------------------\n\n")

        try:
            delete_subnet(project_id, REGION, ZONE, common_headers)
            delete_vpc(project_id, REGION, ZONE, common_headers)
        except Exception as e:
            print(f"在操作地域 {region} 时发生错误: {e}")
            continue

    print("所有操作已完成")

# 删除UHost
def delete_host(project_id, region, zone, headers):
    try:
        print("正在查询UHost列表...")
        timestamp = int(time.time() * 1000)
        url = 'https://api.ucloud.cn/?Action=DescribeUHostInstance'
        data = {
            'ProjectId': project_id,
            'Region': region,
            'Limit': 2000,
            'Offset': 0,
            'Action': 'DescribeUHostInstance',
            '_timestamp': timestamp
        }
        response = post_request(url, data, headers)
        if response is None or 'UHostSet' not in response:
            print("未找到任何UHost")
            return
        uhosts = [uhost['UHostId'] for uhost in response['UHostSet']]
        if not uhosts:
            print("未找到任何UHost")
            return
        print("找到以下UHost：")
        for uhost in uhosts:
            print(uhost)

        # 遍历并执行删除操作
        for uhostid in uhosts:
            print(f"正在删除UHost: {uhostid}")
            delete_timestamp = int(time.time() * 1000)
            # 关机
            poweroff_url = 'https://api.ucloud.cn/?Action=PoweroffUHostInstance'
            poweroff_data = {
                'ProjectId': project_id,
                'Region': region,
                'UHostId': uhostid,
                'Action': 'PoweroffUHostInstance',
                '_timestamp': delete_timestamp
            }
            post_request(poweroff_url, poweroff_data, headers)
            print("\n等待UHost关机...")
            time.sleep(3)

            # 删除
            terminate_url = 'https://api.ucloud.cn/?Action=TerminateUHostInstance'
            terminate_data = {
                'ProjectId': project_id,
                'Region': region,
                'UHostId': uhostid,
                'Action': 'TerminateUHostInstance',
                '_timestamp': delete_timestamp
            }
            post_request(terminate_url, terminate_data, headers)
            print("\n删除完成，等待1秒...")
            time.sleep(1)
    except Exception as e:
        print(f"在删除UHost时发生错误: {e}")

    print("所有UHost删除操作已完成！")

# 删除UDisk
def delete_disk(project_id, region, zone, headers):
    print("正在查询UDisk列表...")
    timestamp = int(time.time() * 1000)
    url = 'https://api.ucloud.cn/?Action=DescribeUDisk'
    data = {
        'ProjectId': project_id,
        'Region': region,
        'HostProduct': 'uhost',
        'Limit': 2000,
        'Offset': 0,
        'Action': 'DescribeUDisk',
        '_timestamp': timestamp
    }
    response = post_request(url, data, headers)
    if response is None or 'DataSet' not in response:
        print("未找到任何UDisk")
        return
    udisks = [udisk['UDiskId'] for udisk in response['DataSet']]
    if not udisks:
        print("未找到任何UDisk")
        return
    print("找到以下UDisk：")
    for udisk in udisks:
        print(udisk)

    # 遍历并执行删除操作
    for udisk in udisks:
        print(f"正在删除UDisk: {udisk}")
        delete_timestamp = int(time.time() * 1000)
        delete_url = 'https://api.ucloud.cn/?Action=DeleteUDisk'
        delete_data = {
            'ProjectId': project_id,
            'Region': region,
            'Zone': zone,
            'UDiskId': udisk,
            'DeleteSnapshotService': 'No',
            'Action': 'DeleteUDisk',
            '_timestamp': delete_timestamp
        }
        post_request(delete_url, delete_data, headers)
        print("\n删除完成，等待1秒...")
        time.sleep(1)

    print("所有UDisk删除操作已完成！")

# 删除EIP
def delete_eip(project_id, region, zone, headers):
    try:
        print("正在查询EIP列表...")
        timestamp = int(time.time() * 1000)
        url = 'https://api.ucloud.cn/?Action=DescribeEIPWithAllNum'
        data = {
            'ProjectId': project_id,
            'Region': region,
            'HostProduct': 'uhost',
            'Limit': 2000,
            'Offset': 0,
            'Action': 'DescribeEIPWithAllNum',
            '_timestamp': timestamp
        }
        response = post_request(url, data, headers)
        if response is None or 'EIPSet' not in response:
            print("未找到任何EIP")
            return
        eips = [eip['EIPId'] for eip in response['EIPSet']]
        if not eips:
            print("未找到任何EIP")
            return
        print("找到以下EIP：")
        for eip in eips:
            print(eip)

        # 遍历并执行删除操作
        for eip in eips:
            print(f"正在删除EIP: {eip}")
            delete_timestamp = int(time.time() * 1000)
            delete_url = 'https://api.ucloud.cn/?Action=ReleaseEIP'
            delete_data = {
                'ProjectId': project_id,
                'Region': region,
                'Zone': zone,
                'EIPId': eip,
                'ApiVersion': 3,
                'Action': 'ReleaseEIP',
                '_timestamp': delete_timestamp
            }
            post_request(delete_url, delete_data, headers)
            print("\n删除完成，等待1秒...")
            time.sleep(1)
    except Exception as e:
        print(f"在删除EIP时发生错误: {e}")

    print("所有EIP删除操作已完成！")

#删除ALB
def delete_alb(project_id, region, zone, headers):
    try:
        print("正在查询ALB列表...")
        timestamp = int(time.time() * 1000)
        url = 'https://api.ucloud.cn/?Action=DescribeLoadBalancers'
        data = {
            'ProjectId': project_id,
            'Region': region,
            'Limit': 100,
            'Offset': 0,
            'Action': 'DescribeLoadBalancers',
            '_timestamp': timestamp
        }
        response = post_request(url, data, headers)                              
        if response is None or 'LoadBalancers' not in response:
            print("未找到任何ALB")
        albs = [alb['LoadBalancerId'] for alb in response['LoadBalancers']]        
        if not albs:
            print("未找到任何ALB")
            return
        print("找到以下ALB：")           
        for alb in albs:
            print(alb)

        # 遍历并执行删除操作
        for albid in albs:
            print(f"正在删除ALB: {albid}")  
            delete_url = 'https://api.ucloud.cn/?Action=DeleteLoadBalancer'
            delete_data = {
                'ProjectId': project_id,
                'Zone': zone,
                'Region': region,
                'LoadBalancerId': albid,
                'Action': 'DeleteLoadBalancer',
                '_timestamp': timestamp
            }
            try:
                post_request(delete_url, delete_data, headers)
                print("\n删除完成，等待1秒...")
                time.sleep(1)
            except Exception as e:
                print(f"在删除ALB {albid} 时发生错误: {e}")
                continue
    except Exception as e:
        print(f"在查询ALB时发生错误: {e}")
        return

    print("所有ALB删除操作已完成！")

# 删除NAT网关
def delete_natgw(project_id, region, zone, headers):
    try:
        print("正在查询NAT网关列表...")
        timestamp = int(time.time() * 1000)
        url = 'https://api.ucloud.cn/?Action=DescribeNATGW'
        data = {
            'ProjectId': project_id,
            'Region': region,          
            'Limit': 100,
            'Offset': 0,
            'Action': 'DescribeNATGW',
            '_timestamp': timestamp
        }
        response = post_request(url, data, headers)
        if response is None or 'DataSet' not in response:
            print("未找到任何NAT网关")
            return
        natgws = [natgw['NATGWId'] for natgw in response['DataSet']]        
        print("找到以下NAT网关：")        
        for natgw in natgws:
            print(natgw)

        # 遍历并执行删除操作
        for natgwid in natgws:
            print(f"正在删除natgw: {natgwid}")
            delete_url = 'https://api.ucloud.cn/?Action=DeleteNATGW'
            delete_data = {
                'ProjectId': project_id,
                'Zone': zone,
                'Region': region,
                'ReleaseEip': 'true',
                'NATGWId': natgwid,
                'Action': 'DeleteNATGW',
                '_timestamp': timestamp
            }
            post_request(delete_url, delete_data, headers)
            print("\n删除完成，等待1秒...")
            time.sleep(1)
    except Exception as e:
        print(f"在删除natgw时发生错误: {e}")

    print("所有NAT网关删除操作已完成！")

# 删除虚拟网卡
def delete_networkinterface(project_id, region, zone, headers):
    try:
        print("正在查询虚拟网卡列表...")
        timestamp = int(time.time() * 1000)
        url = 'https://api.ucloud.cn/?Action=DescribeNetworkInterface'
        data = {
            'ProjectId': project_id,
            'Region': region,          
            'Limit': 100,
            'Offset': 0,
            'Action': 'DescribeNetworkInterface',
            '_timestamp': timestamp
        }
        response = post_request(url, data, headers)
        if response is None or 'NetworkInterfaceSet' not in response:
            print("未找到任何虚拟网卡")
            return
        networkinterfaces = [networkinterface['InterfaceId'] for networkinterface in response['NetworkInterfaceSet']]   
        print("找到以下虚拟网卡：")
        for networkinterface in networkinterfaces:
            print(networkinterface)

        # 遍历并执行删除操作
        for networkinterface in networkinterfaces:
            print(f"正在删除虚拟网卡: {networkinterface}")
            delete_url = 'https://api.ucloud.cn/?Action=DeleteNetworkInterface'
            delete_data = {
                'ProjectId': project_id,
                'Zone': zone,
                'Region': region,                
                'InterfaceId': networkinterface,
                'Action': 'DeleteNetworkInterface',                
                '_timestamp': timestamp
            }
            post_request(delete_url, delete_data, headers)
            print("\n删除完成，等待1秒...")
            time.sleep(1)
    except Exception as e:
        print(f"在删除虚拟网卡时发生错误: {e}")
        
    print("所有虚拟网卡删除操作已完成！")

# 删除子网
def delete_subnet(project_id, region, zone, headers):
    try:
        print("正在查询子网列表...")
        timestamp = int(time.time() * 1000)
        url = 'https://api.ucloud.cn/?Action=DescribeSubnet'
        data = {
            'ProjectId': project_id,
            'Region': region,
            'ShowAvailableIPs': True,
            'IgnoreResource': True,
            'Limit': 2000,
            'Offset': 0,
            'Action': 'DescribeSubnet',
            '_timestamp': timestamp
        }
        response = post_request(url, data, headers)
        if response is None or 'DataSet' not in response:
            print("未找到任何子网")
            return
        subnets = [subnet['SubnetId'] for subnet in response['DataSet']]        
        print("找到以下子网：")
        for subnet in subnets:
            print(subnet)

        # 遍历并执行删除操作
        for subnetid in subnets:
            print(f"正在删除子网: {subnetid}")
            delete_url = 'https://api.ucloud.cn/?Action=DeleteSubnet'
            delete_data = {
                'ProjectId': project_id,
                'Zone': zone,
                'Region': region,
                'SubnetId': subnetid,
                'Action': 'DeleteSubnet',
                '_timestamp': timestamp
            }
            post_request(delete_url, delete_data, headers)
            print("\n删除完成，等待1秒...")
            time.sleep(1)
    except Exception as e:
        print(f"在删除子网时发生错误: {e}")

    print("所有子网删除操作已完成！")

# 删除VPC
def delete_vpc(project_id, region, zone, headers):
    try:
        print("正在查询VPC列表...")
        timestamp = int(time.time() * 1000)
        url = 'https://api.ucloud.cn/?Action=DescribeVPC'
        data = {
            'ProjectId': project_id,
            'Region': region,
            'Limit': 2000,
            'Offset': 0,
            'Action': 'DescribeVPC',
            '_timestamp': timestamp
        }
        response = post_request(url, data, headers)
        if response is None or 'DataSet' not in response:
            print("未找到任何VPC")
            return
        # 检查 DataSet 是否为 None 或非可迭代对象（如空值）
        data_set = response['DataSet']
        if data_set is None or not isinstance(data_set, (list, tuple)):
            print("VPC列表格式异常（DataSet为空或非列表）")
            return    
        vpcs = [vpc['VPCId'] for vpc in data_set]
        print("找到以下VPC：")
        for vpc in vpcs:
            print(vpc)

        # 遍历并执行删除操作
        for vpcid in vpcs:
            print(f"正在删除VPC: {vpcid}")
            delete_timestamp = int(time.time() * 1000)
            delete_url = 'https://api.ucloud.cn/?Action=DeleteVPC'
            delete_data = {
                'ProjectId': project_id,
                'Region': region,
                'VPCId': vpcid,
                'Action': 'DeleteVPC',
                '_timestamp': delete_timestamp
            }
            post_request(delete_url, delete_data, headers)
            print("\n删除完成，等待1秒...")
            time.sleep(1)
    except Exception as e:
        print(f"在删除VPC时发生错误: {e}")

    print("所有VPC删除操作已完成！")

# 设置项目ID
ProjectId = 'org-n4wmt0'
# 调用主函数
if __name__ == '__main__':
    main(ProjectId)