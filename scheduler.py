#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import subprocess
import logging
import sys
import os
from datetime import datetime, timedelta
import argparse
import signal

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("scheduler.log", encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("SchedulerService")

# 全局变量，用于控制服务运行
running = True

def signal_handler(sig, frame):
    """处理终止信号"""
    global running
    logger.info("收到终止信号，正在停止服务...")
    running = False

def run_sync():
    """运行同步脚本"""
    logger.info("执行同步任务")
    try:
        # 使用当前脚本的目录作为工作目录
        script_dir = os.path.dirname(os.path.abspath(__file__))
        os.chdir(script_dir)
        
        # 执行同步脚本
        process = subprocess.Popen(
            [sys.executable, "main.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = process.communicate()
        
        if process.returncode == 0:
            logger.info("同步任务执行成功")
            return True
        else:
            logger.error(f"同步任务执行失败: {stderr}")
            return False
    except Exception as e:
        logger.error(f"执行同步任务时出错: {str(e)}")
        return False

def run_as_service(interval_hours=24):
    """
    作为服务运行，定期执行同步任务
    
    Args:
        interval_hours: 间隔小时数，默认为24小时
    """
    global running
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info(f"服务已启动，同步间隔: {interval_hours}小时")
    print(f"服务已启动，同步间隔: {interval_hours}小时")
    print("按Ctrl+C停止服务")
    
    # 首次运行立即执行一次
    run_sync()
    
    # 计算下次执行时间
    next_run = datetime.now() + timedelta(hours=interval_hours)
    logger.info(f"下次执行时间: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
    
    while running:
        # 检查是否到达下次执行时间
        now = datetime.now()
        if now >= next_run:
            # 执行同步任务
            run_sync()
            
            # 更新下次执行时间
            next_run = now + timedelta(hours=interval_hours)
            logger.info(f"下次执行时间: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 每分钟检查一次
        time.sleep(60)
    
    logger.info("服务已停止")
    print("服务已停止")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Minecraft服务端和代理自动同步服务")
    parser.add_argument(
        "-i", "--interval", 
        type=int, 
        default=24, 
        help="同步间隔(小时)，默认24小时"
    )
    parser.add_argument(
        "-r", "--run-now",
        action="store_true",
        help="立即运行一次同步，不启动服务"
    )
    
    args = parser.parse_args()
    
    if args.run_now:
        run_sync()
    else:
        try:
            run_as_service(args.interval)
        except KeyboardInterrupt:
            logger.info("服务已停止")
            sys.exit(0) 