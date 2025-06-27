# Del_script
此脚本仅用于网络拨测任务产生的资源清理

环境要求：
1、python3.7+
2、pip3 install requests # 安装requests库
使用方法：
1、登录拨测账号，进入对应项目，F12打开浏览器调试工具，找到并复制任意网络请求头中的u-csrf-token信息，并保存到token.txt文件中。
2、同上将cookie信息复制到header.txt文件中，并保存。
3、切换到Del_script目录，在终端中执行：bash unbind_command.sh，等待UGN和VPC解绑完成。
4、终端执行：bash del_command.sh，等待UGN删除完成。
5、终端执行：python3 main.py，等待UHost等资源删除完成。

如脚本不满足清理需求可自行修改和扩展。
