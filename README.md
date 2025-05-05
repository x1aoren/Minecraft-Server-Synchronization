# Minecraft服务端和代理同步工具

这是一个用Python编写的Minecraft同步工具，可以自动下载并同步PaperMC旗下的所有项目到指定目录，每个版本存放在独立的文件夹中，并下载每个版本的所有可用文件。

## 支持的项目

- **Paper**: 高性能的Minecraft服务端
- **Velocity**: 现代的Minecraft代理服务器
- **Waterfall**: 针对BungeeCord优化的代理服务器

## 功能特点

- 自动检测并下载所有版本
- 同步每个版本的所有可用文件（不仅仅是JAR文件）
- 按版本号整理（例如：content/paper/1.16.5/）
- 可作为服务持续运行，定期检查更新
- 文件SHA256校验确保下载完整性
- 下载进度实时显示
- 详细的日志记录
- 版本信息保存，避免重复下载

## 安装要求

- Python 3.6+
- 依赖包：requests

## 安装方法

1. 克隆或下载此仓库
2. 安装依赖：

```bash
pip install -r requirements.txt
```

## 使用方法

### 立即同步所有版本

直接运行主脚本：

```bash
python main.py
```

脚本会自动：
1. 获取所有项目的所有版本
2. 为每个版本创建独立目录（例如：content/paper/1.16.5/）
3. 下载每个版本的所有可用文件（主JAR、源代码、文档等）
4. 验证文件完整性

### 作为服务运行

使用调度器脚本定期检查更新：

```bash
python scheduler.py -i 12
```

这将会：
1. 启动一个持续运行的服务
2. 立即进行一次同步
3. 每12小时自动检查一次更新（默认为24小时）
4. 按Ctrl+C可以安全停止服务

### 仅执行一次同步

```bash
python scheduler.py -r
```

## 日志

程序运行日志会保存在以下文件中，同时也会在控制台显示：
- `minecraft_sync.log` - 同步过程的日志
- `scheduler.log` - 调度服务的日志

## 文件结构

```
content/
├── paper/
│   ├── 1.8.8/
│   │   ├── paper-1.8.8-445.jar        # 主JAR文件
│   │   ├── paper-1.8.8-445-sources.jar # 源代码文件
│   │   ├── paper-1.8.8-445-mojang.jar # Mojang映射文件
│   │   └── version_info.json          # 版本信息
│   ├── 1.16.5/
│   │   ├── paper-1.16.5-794.jar
│   │   ├── paper-1.16.5-794-sources.jar
│   │   └── version_info.json
│   └── ...
├── velocity/
│   ├── 3.1.1/
│   │   ├── velocity-3.1.1-103.jar
│   │   ├── velocity-3.1.1-103-api.jar
│   │   └── version_info.json
│   └── ...
└── waterfall/
    ├── 1.18/
    │   ├── waterfall-1.18-498.jar
    │   ├── waterfall-1.18-498-api.jar
    │   └── version_info.json
    └── ...
```

## 自动化部署

### Windows (作为服务运行)

创建一个批处理文件 `start_service.bat`：

```batch
@echo off
echo 启动Minecraft同步服务...
start /b pythonw scheduler.py -i 12 > nul 2>&1
echo 服务已在后台启动，间隔12小时
```

可以将此批处理文件添加到Windows启动项。

### Linux (使用systemd)

创建一个服务文件 `/etc/systemd/system/minecraft-sync.service`：

```
[Unit]
Description=Minecraft Server Sync Service
After=network.target

[Service]
Type=simple
User=你的用户名
WorkingDirectory=/path/to/script
ExecStart=/usr/bin/python3 /path/to/script/scheduler.py -i 12
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

然后启用并启动服务：

```bash
sudo systemctl enable minecraft-sync
sudo systemctl start minecraft-sync
```

## 许可证

MIT 