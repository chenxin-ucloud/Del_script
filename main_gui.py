import sys
import time
import threading
import json
import requests
from tkinter import Tk, Text, Entry, Button, Label, Frame, Scrollbar, END, messagebox
from tkinter.ttk import Progressbar
from urllib.parse import urlencode

class ResourceCleanerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("UCloud资源清理工具")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        # 确保中文显示正常
        self.setup_ui()
        
        # 加载地区数据
        self.load_region_data()
        
        # 状态控制
        self.is_cleaning = False

    def setup_ui(self):
        # 创建主框架
        main_frame = Frame(self.root)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 左侧输入区域
        input_frame = Frame(main_frame, width=350)
        input_frame.pack(side="left", fill="y", padx=(0, 10))
        
        # Token输入
        Label(input_frame, text="U-CSRF-Token:").pack(anchor="w", pady=(10, 2))
        self.token_entry = Entry(input_frame, width=40, show="*")
        self.token_entry.pack(fill="x", pady=(0, 10))
        
        # Cookie输入
        Label(input_frame, text="Cookie:").pack(anchor="w", pady=(10, 2))
        self.cookie_entry = Entry(input_frame, width=40)
        self.cookie_entry.pack(fill="x", pady=(0, 10))
        
        # Project ID输入
        Label(input_frame, text="Project ID:").pack(anchor="w", pady=(10, 2))
        self.project_id_entry = Entry(input_frame, width=40)
        self.project_id_entry.pack(fill="x", pady=(0, 10))
        
        # Region输入
        Label(input_frame, text="Region:").pack(anchor="w", pady=(10, 2))
        self.region_entry = Entry(input_frame, width=40)
        self.region_entry.pack(fill="x", pady=(0, 10))
        
        # Zone输入
        Label(input_frame, text="Zone:").pack(anchor="w", pady=(10, 2))
        self.zone_entry = Entry(input_frame, width=40)
        self.zone_entry.pack(fill="x", pady=(0, 10))
        
        # 按钮区域
        button_frame = Frame(input_frame)
        button_frame.pack(side="bottom", pady=20)
        
        self.clean_ugn_btn = Button(
            button_frame, text="解绑并删除UGN", 
            command=self.start_clean_ugn, width=15
        )
        self.clean_ugn_btn.pack(side="left", padx=5)
        
        self.clean_resources_btn = Button(
            button_frame, text="删除其他资源", 
            command=self.start_clean_resources, width=15
        )
        self.clean_resources_btn.pack(side="left", padx=5)
        
        self.stop_btn = Button(
            button_frame, text="停止操作", 
            command=self.stop_cleaning, width=10, state="disabled"
        )
        self.stop_btn.pack(side="left", padx=5)
        
        # 右侧日志区域
        log_frame = Frame(main_frame)
        log_frame.pack(side="right", fill="both", expand=True)
        
        Label(log_frame, text="执行日志:").pack(anchor="w")
        
        # 日志文本框和滚动条
        log_scroll = Scrollbar(log_frame)
        log_scroll.pack(side="right", fill="y")
        
        self.log_text = Text(log_frame, wrap="word", yscrollcommand=log_scroll.set)
        self.log_text.pack(fill="both", expand=True)
        log_scroll.config(command=self.log_text.yview)
        
        # 进度条
        self.progress = Progressbar(log_frame, orient="horizontal", length=100, mode="indeterminate")
        self.progress.pack(fill="x", pady=5)

    def load_region_data(self):
        try:
            with open('region.json', 'r', encoding='utf-8') as f:
                self.regions_data = json.load(f)
            self.log("成功加载地区数据")
        except Exception as e:
            self.log(f"加载地区数据失败: {str(e)}")
            self.regions_data = {}

    def log(self, message):
        """在日志区域显示消息"""
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.insert(END, f"[{timestamp}] {message}\n")
        self.log_text.see(END)  # 滚动到最新内容

    def get_common_headers(self):
        """获取通用请求头"""
        token = self.token_entry.get().strip()
        cookie = self.cookie_entry.get().strip()
        
        if not token or not cookie:
            return None
            
        return {
            'Cookie': cookie,
            'U-CSRF-Token': token,
            'Content-Type': 'application/json'
        }

    def start_clean_ugn(self):
        """开始清理UGN"""
        if self.is_cleaning:
            messagebox.showwarning("警告", "已有操作正在执行，请等待完成或停止当前操作")
            return
            
        project_id = self.project_id_entry.get().strip()
        region = self.region_entry.get().strip()
        zone = self.zone_entry.get().strip()
        
        if not all([project_id, region, zone]):
            messagebox.showerror("错误", "请填写Project ID、Region和Zone")
            return
            
        headers = self.get_common_headers()
        if not headers:
            messagebox.showerror("错误", "请填写Token和Cookie")
            return
            
        self.is_cleaning = True
        self.clean_ugn_btn.config(state="disabled")
        self.clean_resources_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.progress.start()
        
        # 在新线程中执行清理操作，避免界面卡死
        threading.Thread(
            target=self.clean_ugn_thread,
            args=(project_id, region, zone, headers),
            daemon=True
        ).start()

    def clean_ugn_thread(self, project_id, region, zone, headers):
        """UGN清理线程"""
        try:
            self.log("开始清理UGN...")
            
            # 列出所有UGN
            ugns = self.list_ugns(project_id, region, zone, headers)
            if not ugns:
                self.log("未找到任何UGN")
                return
                
            self.log(f"找到以下UGN: {', '.join(ugns)}")
            
            # 解绑网络
            for ugnid in ugns:
                if not self.is_cleaning:
                    self.log("操作已停止")
                    return
                    
                self.log(f"正在解绑UGN: {ugnid}")
                networks = self.get_networks(ugnid, project_id, region, zone, headers)
                if networks:
                    self.detach_networks(ugnid, networks, project_id, region, headers)
                    self.log(f"UGN {ugnid} 解绑完成")
                else:
                    self.log(f"UGN {ugnid} 没有绑定的网络")
            
            # 删除UGN
            for ugnid in ugns:
                if not self.is_cleaning:
                    self.log("操作已停止")
                    return
                    
                self.log(f"正在删除UGN: {ugnid}")
                success = self.del_ugn(ugnid, project_id, region, zone, headers)
                if success:
                    self.log(f"UGN {ugnid} 删除成功")
                else:
                    self.log(f"UGN {ugnid} 删除失败")
            
            self.log("所有UGN清理操作已完成")
            
        except Exception as e:
            self.log(f"清理UGN时发生错误: {str(e)}")
        finally:
            self.finish_cleaning()

    def start_clean_resources(self):
        """开始清理其他资源"""
        if self.is_cleaning:
            messagebox.showwarning("警告", "已有操作正在执行，请等待完成或停止当前操作")
            return
            
        project_id = self.project_id_entry.get().strip()
        if not project_id:
            messagebox.showerror("错误", "请填写Project ID")
            return
            
        headers = self.get_common_headers()
        if not headers:
            messagebox.showerror("错误", "请填写Token和Cookie")
            return
            
        self.is_cleaning = True
        self.clean_ugn_btn.config(state="disabled")
        self.clean_resources_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.progress.start()
        
        # 在新线程中执行清理操作
        threading.Thread(
            target=self.clean_resources_thread,
            args=(project_id, headers),
            daemon=True
        ).start()

    def clean_resources_thread(self, project_id, headers):
        """清理其他资源线程"""
        try:
            self.log("开始清理其他资源...")
            
            if not self.regions_data:
                self.log("没有可用的地区数据，无法清理资源")
                return
                
            # 遍历每个区域删除资源
            for region_name in self.regions_data:
                if not self.is_cleaning:
                    self.log("操作已停止")
                    return
                    
                region_info = self.regions_data[region_name]
                region = region_info['Region']
                zone = region_info['Zone']
                
                self.log(f"\n开始处理地区: {region_name} (Region: {region}, Zone: {zone})")
                
                # 删除UHost、UDisk、EIP等资源
                self.delete_host(project_id, region, zone, headers)
                self.delete_disk(project_id, region, zone, headers)
                self.delete_eip(project_id, region, zone, headers)
                self.delete_alb(project_id, region, zone, headers)
                self.delete_natgw(project_id, region, zone, headers)
                self.delete_networkinterface(project_id, region, zone, headers)
            
            # 再次遍历删除子网和VPC
            for region_name in self.regions_data:
                if not self.is_cleaning:
                    self.log("操作已停止")
                    return
                    
                region_info = self.regions_data[region_name]
                region = region_info['Region']
                zone = region_info['Zone']
                
                self.log(f"\n开始处理地区: {region_name} (子网和VPC)")
                self.delete_subnet(project_id, region, zone, headers)
                self.delete_vpc(project_id, region, zone, headers)
            
            self.log("所有资源清理操作已完成")
            
        except Exception as e:
            self.log(f"清理资源时发生错误: {str(e)}")
        finally:
            self.finish_cleaning()

    def stop_cleaning(self):
        """停止当前清理操作"""
        self.is_cleaning = False
        self.log("正在停止操作...")

    def finish_cleaning(self):
        """完成清理操作后的处理"""
        self.root.after(0, lambda: self.progress.stop())
        self.root.after(0, lambda: self.clean_ugn_btn.config(state="normal"))
        self.root.after(0, lambda: self.clean_resources_btn.config(state="normal"))
        self.root.after(0, lambda: self.stop_btn.config(state="disabled"))
        self.is_cleaning = False

    # 以下是原有清理逻辑的封装方法
    def list_ugns(self, project_id, region, zone, headers):
        url = 'https://api.ucloud.cn/?Action=ListUGN'
        all_ugns = []
        offset = 0
        limit = 100  
        
        while True:
            if not self.is_cleaning:
                return []
                
            payload = {
                "ProjectId": project_id,
                "Zone": zone,
                "Region": region,
                "Limit": limit,
                "Offset": offset,
                "Action": "ListUGN",
                "_timestamp": int(time.time() * 1000)
            }
            
            try:
                resp = requests.post(url, headers=headers, json=payload, timeout=30)
                data = resp.json()
                
                if 'UGNs' not in data or not data['UGNs']:
                    break
                    
                all_ugns.extend([ugn['UGNID'] for ugn in data['UGNs']])
                
                if len(data['UGNs']) < limit:
                    break
                    
                offset += limit
                
            except Exception as e:
                self.log(f"查询UGN列表失败: {str(e)}")
                return []
                
        return list(set(all_ugns))

    def get_networks(self, ugnid, project_id, region, zone, headers):
        url = 'https://api.ucloud.cn/?Action=GetUGNNetworks'
        payload = {
            "ProjectId": project_id,
            "Zone": zone,
            "Region": region,
            "UGNID": ugnid,
            "Action": "GetUGNNetworks",
            "_timestamp": int(time.time() * 1000)
        }
        
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=30)
            data = resp.json()
            return [net['NetworkID'] for net in data.get('Networks', [])]
        except Exception as e:
            self.log(f"查询UGN绑定网络失败: {str(e)}")
            return []

    def detach_networks(self, ugnid, networks, project_id, region, headers):
        url = 'https://api.ucloud.cn/?Action=DetachUGNNetworks'
        params = {
            "ProjectId": project_id,
            "Region": region,
            "UGNID": ugnid,
            "Action": "DetachUGNNetworks",
            "_timestamp": int(time.time() * 1000)
        }
        
        for i, net in enumerate(networks):
            params[f'Networks[{i}]'] = net
            
        # 复制 headers 并修改 Content-Type
        headers_copy = headers.copy()
        headers_copy['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8'
        
        try:
            resp = requests.post(
                url, 
                headers=headers_copy, 
                data=urlencode(params),
                timeout=30
            )
            data = resp.json()
            
            if data.get('RetCode', 0) != 0:
                self.log(f"解绑失败: {str(data)}")
            else:
                self.log("解绑成功")
                
        except Exception as e:
            self.log(f"解绑请求异常: {str(e)}")

    def del_ugn(self, ugnid, project_id, region, zone, headers, retry=3):
        url = 'https://api.ucloud.cn/?Action=DelUGN'
        
        for attempt in range(1, retry + 1):
            if not self.is_cleaning:
                return False
                
            payload = {
                "ProjectId": project_id,
                "Zone": zone,
                "Region": region,
                "UGNID": ugnid,
                "Action": "DelUGN",
                "_timestamp": int(time.time() * 1000)
            }
            
            try:
                resp = requests.post(url, headers=headers, json=payload, timeout=30)
                data = resp.json()
                
                if data.get('RetCode', 0) == 0:
                    return True
                else:
                    self.log(f"删除失败 (尝试 {attempt}/{retry}): {str(data)}")
                    time.sleep(2)
                    
            except Exception as e:
                self.log(f"删除请求异常 (尝试 {attempt}/{retry}): {str(e)}")
                time.sleep(2)
                
        return False

    def post_request(self, url, data, headers):
        try:
            response = requests.post(url, json=data, headers=headers, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            self.log("请求超时")
            return None
        except Exception as e:
            self.log(f"请求失败: {str(e)}")
            return None

    def delete_host(self, project_id, region, zone, headers):
        self.log("正在查询UHost列表...")
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
        
        response = self.post_request(url, data, headers)
        if not response or 'UHostSet' not in response:
            self.log("未找到任何UHost")
            return
            
        uhosts = [uhost['UHostId'] for uhost in response['UHostSet']]
        if not uhosts:
            self.log("未找到任何UHost")
            return
            
        self.log(f"找到 {len(uhosts)} 个UHost")
        
        for uhostid in uhosts:
            if not self.is_cleaning:
                return
                
            self.log(f"正在删除UHost: {uhostid}")
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
            self.post_request(poweroff_url, poweroff_data, headers)
            self.log("等待UHost关机...")
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
            self.post_request(terminate_url, terminate_data, headers)
            self.log("UHost删除完成")
            time.sleep(1)
            
        self.log("所有UHost删除操作已完成")

    def delete_disk(self, project_id, region, zone, headers):
        self.log("正在查询UDisk列表...")
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
        
        response = self.post_request(url, data, headers)
        if not response or 'DataSet' not in response:
            self.log("未找到任何UDisk")
            return
            
        udisks = [udisk['UDiskId'] for udisk in response['DataSet']]
        if not udisks:
            self.log("未找到任何UDisk")
            return
            
        self.log(f"找到 {len(udisks)} 个UDisk")
        
        for udisk in udisks:
            if not self.is_cleaning:
                return
                
            self.log(f"正在删除UDisk: {udisk}")
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
            self.post_request(delete_url, delete_data, headers)
            self.log("UDisk删除完成")
            time.sleep(1)
            
        self.log("所有UDisk删除操作已完成")

    def delete_eip(self, project_id, region, zone, headers):
        self.log("正在查询EIP列表...")
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
        
        response = self.post_request(url, data, headers)
        if not response or 'EIPSet' not in response:
            self.log("未找到任何EIP")
            return
            
        eips = [eip['EIPId'] for eip in response['EIPSet']]
        if not eips:
            self.log("未找到任何EIP")
            return
            
        self.log(f"找到 {len(eips)} 个EIP")
        
        for eip in eips:
            if not self.is_cleaning:
                return
                
            self.log(f"正在删除EIP: {eip}")
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
            self.post_request(delete_url, delete_data, headers)
            self.log("EIP删除完成")
            time.sleep(1)
            
        self.log("所有EIP删除操作已完成")

    def delete_alb(self, project_id, region, zone, headers):
        self.log("正在查询ALB列表...")
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
        
        response = self.post_request(url, data, headers)
        if not response or 'LoadBalancers' not in response:
            self.log("未找到任何ALB")
            return
            
        albs = [alb['LoadBalancerId'] for alb in response['LoadBalancers']]
        if not albs:
            self.log("未找到任何ALB")
            return
            
        self.log(f"找到 {len(albs)} 个ALB")
        
        for albid in albs:
            if not self.is_cleaning:
                return
                
            self.log(f"正在删除ALB: {albid}")
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
                self.post_request(delete_url, delete_data, headers)
                self.log("ALB删除完成")
                time.sleep(1)
            except Exception as e:
                self.log(f"删除ALB {albid} 时出错: {str(e)}")
                
        self.log("所有ALB删除操作已完成")

    def delete_natgw(self, project_id, region, zone, headers):
        self.log("正在查询NAT网关列表...")
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
        
        response = self.post_request(url, data, headers)
        if not response or 'NATGWSet' not in response:
            self.log("未找到任何NAT网关")
            return
            
        natgws = [natgw['NATGWId'] for natgw in response['NATGWSet']]
        if not natgws:
            self.log("未找到任何NAT网关")
            return
            
        self.log(f"找到 {len(natgws)} 个NAT网关")
        
        for natgwid in natgws:
            if not self.is_cleaning:
                return
                
            self.log(f"正在删除NAT网关: {natgwid}")
            delete_url = 'https://api.ucloud.cn/?Action=DeleteNATGW'
            delete_data = {
                'ProjectId': project_id,
                'Region': region,
                'NATGWId': natgwid,
                'Action': 'DeleteNATGW',
                '_timestamp': timestamp
            }
            self.post_request(delete_url, delete_data, headers)
            self.log("NAT网关删除完成")
            time.sleep(1)
            
        self.log("所有NAT网关删除操作已完成")

    def delete_networkinterface(self, project_id, region, zone, headers):
        self.log("正在查询虚拟网卡列表...")
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
        
        response = self.post_request(url, data, headers)
        if not response or 'NetworkInterfaceSet' not in response:
            self.log("未找到任何虚拟网卡")
            return
            
        interfaces = [ni['InterfaceId'] for ni in response['NetworkInterfaceSet']]
        if not interfaces:
            self.log("未找到任何虚拟网卡")
            return
            
        self.log(f"找到 {len(interfaces)} 个虚拟网卡")
        
        for interface_id in interfaces:
            if not self.is_cleaning:
                return
                
            self.log(f"正在删除虚拟网卡: {interface_id}")
            delete_url = 'https://api.ucloud.cn/?Action=DeleteNetworkInterface'
            delete_data = {
                'ProjectId': project_id,
                'Region': region,
                'NetworkInterfaceId': interface_id,
                'Action': 'DeleteNetworkInterface',
                '_timestamp': timestamp
            }
            self.post_request(delete_url, delete_data, headers)
            self.log("虚拟网卡删除完成")
            time.sleep(1)
            
        self.log("所有虚拟网卡删除操作已完成")

    def delete_subnet(self, project_id, region, zone, headers):
        self.log("正在查询子网列表...")
        timestamp = int(time.time() * 1000)
        url = 'https://api.ucloud.cn/?Action=DescribeSubnet'
        data = {
            'ProjectId': project_id,
            'Region': region,
            'Limit': 100,
            'Offset': 0,
            'Action': 'DescribeSubnet',
            '_timestamp': timestamp
        }
        
        response = self.post_request(url, data, headers)
        if not response or 'SubnetSet' not in response:
            self.log("未找到任何子网")
            return
            
        subnets = [subnet['SubnetId'] for subnet in response['SubnetSet']]
        if not subnets:
            self.log("未找到任何子网")
            return
            
        self.log(f"找到 {len(subnets)} 个子网")
        
        for subnet_id in subnets:
            if not self.is_cleaning:
                return
                
            self.log(f"正在删除子网: {subnet_id}")
            delete_url = 'https://api.ucloud.cn/?Action=DeleteSubnet'
            delete_data = {
                'ProjectId': project_id,
                'Region': region,
                'SubnetId': subnet_id,
                'Action': 'DeleteSubnet',
                '_timestamp': timestamp
            }
            self.post_request(delete_url, delete_data, headers)
            self.log("子网删除完成")
            time.sleep(1)
            
        self.log("所有子网删除操作已完成")

    def delete_vpc(self, project_id, region, zone, headers):
        self.log("正在查询VPC列表...")
        timestamp = int(time.time() * 1000)
        url = 'https://api.ucloud.cn/?Action=DescribeVPC'
        data = {
            'ProjectId': project_id,
            'Region': region,
            'Limit': 100,
            'Offset': 0,
            'Action': 'DescribeVPC',
            '_timestamp': timestamp
        }
        
        response = self.post_request(url, data, headers)
        if not response or 'VPCSet' not in response:
            self.log("未找到任何VPC")
            return
            
        vpcs = [vpc['VPCId'] for vpc in response['VPCSet']]
        if not vpcs:
            self.log("未找到任何VPC")
            return
            
        self.log(f"找到 {len(vpcs)} 个VPC")
        
        for vpc_id in vpcs:
            if not self.is_cleaning:
                return
                
            self.log(f"正在删除VPC: {vpc_id}")
            delete_url = 'https://api.ucloud.cn/?Action=DeleteVPC'
            delete_data = {
                'ProjectId': project_id,
                'Region': region,
                'VPCId': vpc_id,
                'Action': 'DeleteVPC',
                '_timestamp': timestamp
            }
            self.post_request(delete_url, delete_data, headers)
            self.log("VPC删除完成")
            time.sleep(1)
            
        self.log("所有VPC删除操作已完成")

if __name__ == "__main__":
    root = Tk()
    app = ResourceCleanerGUI(root)
    root.mainloop()