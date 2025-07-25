# Del_script

此脚本仅用于网络拨测任务产生的资源清理。

## 环境要求
- Python 3.7 或更高版本。
- 安装 `requests` 库，可使用以下命令进行安装：
```bash
pip3 install requests
```

## 使用方法
1. **创建token.txt和header.txt文件**：
    在common.py同级目录新建token.txt和header.txt文件。
2. **获取并保存 Token 信息**：
    登录拨测账号，进入对应项目，使用 F12 打开浏览器调试工具，找到并复制任意网络请求头中的 `u-csrf-token` 信息，保存到 `token.txt` 。
3. **获取并保存 Cookie 信息**：
    同理复制 Cookie 信息保存到 `header.txt` 。
4. **解绑 UGN 和 VPC并删除 UGN**：
    切换到 `Del_script` 目录，在终端中执行以下命令，等待 UGN 删除完成：
```bash
python3 ugn_clean.py org-n4wmt0 hk hk-02
```
5. **删除 UHost 等资源**：
    在终端执行以下命令，等待 UHost 等资源删除完成：
```bash
python3 main.py
```

## 注意事项
如脚本不满足清理需求，可自行修改和扩展。 