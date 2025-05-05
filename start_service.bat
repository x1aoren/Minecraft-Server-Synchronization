@echo off
echo 启动Minecraft同步服务...
start /b pythonw scheduler.py -i 12 > nul 2>&1
echo 服务已在后台启动，间隔12小时
echo 日志文件: scheduler.log 和 minecraft_sync.log 