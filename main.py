#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import requests
import json
import shutil
import hashlib
from pathlib import Path
import logging
import sys
import time
import re
import html

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("minecraft_sync.log", encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("MinecraftSync")

# PaperMC API URL
PAPERMC_API_URL = "https://api.papermc.io/v2/projects"
# PurpurMC API URL
PURPURMC_API_URL = "https://api.purpurmc.org/v2"
# SpigotMC 下载网址
SPIGOTMC_URL = "https://download.getbukkit.org"

# 项目列表
PROJECTS = {
    # PaperMC 旗下项目
    "paper": {"name": "Paper服务端", "type": "papermc"},
    "velocity": {"name": "Velocity代理", "type": "papermc"},
    "waterfall": {"name": "Waterfall代理", "type": "papermc"},
    
    # PurpurMC 旗下项目
    "purpur": {"name": "Purpur服务端", "type": "purpurmc"},
    
    # SpigotMC 旗下项目
    "spigot": {"name": "Spigot服务端", "type": "spigotmc"},
    "bukkit": {"name": "Bukkit服务端", "type": "spigotmc"},
    "craftbukkit": {"name": "CraftBukkit服务端", "type": "spigotmc"},
    "bungeecord": {"name": "BungeeCord代理", "type": "spigotmc"}
}

def create_dirs(project):
    """创建必要的目录"""
    content_dir = Path("content")
    project_dir = content_dir / project
    
    if not content_dir.exists():
        logger.info(f"创建目录: {content_dir}")
        content_dir.mkdir()
    
    if not project_dir.exists():
        logger.info(f"创建目录: {project_dir}")
        project_dir.mkdir()
    
    return project_dir

# ===================== PaperMC 相关函数 =====================

def get_papermc_versions(project):
    """获取PaperMC项目的所有版本信息"""
    try:
        api_url = f"{PAPERMC_API_URL}/{project}"
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()
        versions = response.json()["versions"]
        logger.info(f"获取到 {len(versions)} 个{PROJECTS[project]['name']}版本")
        return versions
    except Exception as e:
        logger.error(f"获取{PROJECTS[project]['name']}版本列表失败: {str(e)}")
        print(f"错误: 获取{PROJECTS[project]['name']}版本列表失败，请检查网络连接")
        return []

def get_papermc_version_info(project, version):
    """获取PaperMC项目指定版本的最新构建信息"""
    try:
        builds_url = f"{PAPERMC_API_URL}/{project}/versions/{version}"
        response = requests.get(builds_url, timeout=10)
        response.raise_for_status()
        builds = response.json()["builds"]
        latest_build = builds[-1]  # 获取最新构建号
        
        build_info_url = f"{PAPERMC_API_URL}/{project}/versions/{version}/builds/{latest_build}"
        response = requests.get(build_info_url, timeout=10)
        response.raise_for_status()
        build_info = response.json()
        
        # 获取所有可下载文件的信息
        files_info = []
        for download_type, download_data in build_info['downloads'].items():
            download_url = f"{PAPERMC_API_URL}/{project}/versions/{version}/builds/{latest_build}/downloads/{download_data['name']}"
            files_info.append({
                "type": download_type,
                "name": download_data['name'],
                "download_url": download_url,
                "sha256": download_data['sha256']
            })
        
        return {
            "version": version,
            "build": latest_build,
            "files": files_info
        }
    except Exception as e:
        logger.error(f"获取{PROJECTS[project]['name']}版本 {version} 信息失败: {str(e)}")
        print(f"错误: 获取{PROJECTS[project]['name']}版本 {version} 信息失败")
        return None

# ===================== PurpurMC 相关函数 =====================

def get_purpurmc_versions(project):
    """获取PurpurMC项目的所有版本信息"""
    try:
        api_url = f"{PURPURMC_API_URL}/{project}"
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()
        versions = response.json()["versions"]
        logger.info(f"获取到 {len(versions)} 个{PROJECTS[project]['name']}版本")
        return versions
    except Exception as e:
        logger.error(f"获取{PROJECTS[project]['name']}版本列表失败: {str(e)}")
        print(f"错误: 获取{PROJECTS[project]['name']}版本列表失败，请检查网络连接")
        return []

def get_purpurmc_version_info(project, version):
    """获取PurpurMC项目指定版本的最新构建信息"""
    try:
        builds_url = f"{PURPURMC_API_URL}/{project}/{version}"
        response = requests.get(builds_url, timeout=10)
        response.raise_for_status()
        build_info = response.json()
        latest_build = build_info["builds"]["latest"]
        
        # 构建下载文件信息
        files_info = []
        # 主JAR文件
        jar_url = f"{PURPURMC_API_URL}/{project}/{version}/{latest_build}/download"
        files_info.append({
            "type": "application",
            "name": f"{project}-{version}-{latest_build}.jar",
            "download_url": jar_url,
            "sha256": None  # Purpur API不提供sha256
        })
        
        return {
            "version": version,
            "build": latest_build,
            "files": files_info
        }
    except Exception as e:
        logger.error(f"获取{PROJECTS[project]['name']}版本 {version} 信息失败: {str(e)}")
        print(f"错误: 获取{PROJECTS[project]['name']}版本 {version} 信息失败")
        return None

# ===================== SpigotMC 相关函数 =====================

def get_spigotmc_versions(project):
    """获取SpigotMC项目的所有版本信息"""
    versions = []
    try:
        # SpigotMC没有官方API，所以我们使用预定义的版本列表
        if project == "bungeecord":
            # BungeeCord常用版本
            versions = ["1.8", "1.9", "1.10", "1.11", "1.12", "1.13", "1.14", "1.15", "1.16", "1.17", "1.18", "1.19", "1.20"]
        else:
            # Spigot/Bukkit/CraftBukkit常用版本
            versions = ["1.4.6", "1.4.7", "1.5.1", "1.5.2", "1.6.2", "1.6.4", "1.7.2", "1.7.5", "1.7.8", "1.7.9", "1.7.10",
                      "1.8", "1.8.3", "1.8.4", "1.8.5", "1.8.6", "1.8.7", "1.8.8", "1.9", "1.9.2", "1.9.4",
                      "1.10", "1.10.2", "1.11", "1.11.1", "1.11.2", "1.12", "1.12.1", "1.12.2",
                      "1.13", "1.13.1", "1.13.2", "1.14", "1.14.1", "1.14.2", "1.14.3", "1.14.4",
                      "1.15", "1.15.1", "1.15.2", "1.16.1", "1.16.2", "1.16.3", "1.16.4", "1.16.5",
                      "1.17", "1.17.1", "1.18", "1.18.1", "1.18.2", "1.19", "1.19.1", "1.19.2", "1.19.3", "1.19.4",
                      "1.20", "1.20.1", "1.20.2", "1.20.3", "1.20.4"]
        
        logger.info(f"获取到 {len(versions)} 个{PROJECTS[project]['name']}版本")
        return versions
    except Exception as e:
        logger.error(f"获取{PROJECTS[project]['name']}版本列表失败: {str(e)}")
        print(f"错误: 获取{PROJECTS[project]['name']}版本列表失败")
        return []

def get_spigotmc_version_info(project, version):
    """获取SpigotMC项目指定版本的信息"""
    try:
        # 根据项目类型和版本确定下载URL
        if project == "bungeecord":
            # BungeeCord的URL格式
            download_url = f"{SPIGOTMC_URL}/download/bungeecord"
            filename = f"BungeeCord-{version}.jar"
        else:
            # Spigot/Bukkit/CraftBukkit的URL格式
            project_path = "spigot" if project == "spigot" else "craftbukkit" if project == "craftbukkit" else "bukkit"
            download_url = f"{SPIGOTMC_URL}/download/{project_path}"
            filename = f"{project.capitalize()}-{version}.jar"
        
        # 构建文件信息
        files_info = [{
            "type": "application",
            "name": filename,
            "download_url": f"{download_url}/{filename}",
            "sha256": None  # SpigotMC不提供sha256
        }]
        
        return {
            "version": version,
            "build": version,  # 对于SpigotMC，使用版本作为构建号
            "files": files_info
        }
    except Exception as e:
        logger.error(f"获取{PROJECTS[project]['name']}版本 {version} 信息失败: {str(e)}")
        print(f"错误: 获取{PROJECTS[project]['name']}版本 {version} 信息失败")
        return None

# ===================== 通用下载与验证函数 =====================

def download_file(url, destination):
    """下载文件并验证SHA256校验和"""
    try:
        logger.info(f"开始下载: {url}")
        response = requests.get(url, stream=True, timeout=60)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        block_size = 1024 * 1024  # 1MB
        downloaded = 0
        
        with open(destination, 'wb') as f:
            for chunk in response.iter_content(chunk_size=block_size):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    percent = int(downloaded / total_size * 100) if total_size > 0 else 0
                    print(f"下载进度: {percent}% ({downloaded}/{total_size} 字节)", end='\r')
        
        print()  # 打印换行
        logger.info(f"下载完成: {destination}")
        return True
    except Exception as e:
        logger.error(f"下载失败: {str(e)}")
        print(f"错误: 下载失败 - {str(e)}")
        return False

def verify_file(file_path, expected_sha256):
    """验证文件的SHA256校验和"""
    # 如果没有提供SHA256，则跳过验证
    if not expected_sha256:
        logger.info(f"未提供SHA256值，跳过验证: {file_path}")
        return True
        
    try:
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        
        calculated_hash = sha256_hash.hexdigest()
        if calculated_hash == expected_sha256:
            logger.info(f"文件验证成功: {file_path}")
            return True
        else:
            logger.error(f"文件验证失败: {file_path}. 预期: {expected_sha256}, 实际: {calculated_hash}")
            print(f"错误: 文件验证失败，可能是下载过程中出现问题")
            return False
    except Exception as e:
        logger.error(f"验证文件时出错: {str(e)}")
        print(f"错误: 验证文件时出错 - {str(e)}")
        return False

def save_version_info(version_dir, version_info):
    """保存版本信息到文件"""
    version_file = version_dir / "version_info.json"
    with open(version_file, 'w', encoding='utf-8') as f:
        json.dump(version_info, f, ensure_ascii=False, indent=2)
    logger.info(f"版本信息已保存到: {version_file}")

def load_version_info(version_dir):
    """加载已保存的版本信息"""
    version_file = version_dir / "version_info.json"
    if version_file.exists():
        try:
            with open(version_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载版本信息失败: {str(e)}")
    return None

# ===================== 同步函数 =====================

def get_versions(project):
    """获取项目的所有版本"""
    project_type = PROJECTS[project]["type"]
    
    if project_type == "papermc":
        return get_papermc_versions(project)
    elif project_type == "purpurmc":
        return get_purpurmc_versions(project)
    elif project_type == "spigotmc":
        return get_spigotmc_versions(project)
    else:
        logger.error(f"未知项目类型: {project_type}")
        return []

def get_version_info(project, version):
    """获取项目指定版本的信息"""
    project_type = PROJECTS[project]["type"]
    
    if project_type == "papermc":
        return get_papermc_version_info(project, version)
    elif project_type == "purpurmc":
        return get_purpurmc_version_info(project, version)
    elif project_type == "spigotmc":
        return get_spigotmc_version_info(project, version)
    else:
        logger.error(f"未知项目类型: {project_type}")
        return None

def sync_version(project, project_dir, version):
    """同步指定版本"""
    logger.info(f"同步{PROJECTS[project]['name']}版本: {version}")
    
    # 为版本创建目录
    version_dir = project_dir / version
    if not version_dir.exists():
        logger.info(f"创建目录: {version_dir}")
        version_dir.mkdir()
    
    # 获取版本信息
    version_info = get_version_info(project, version)
    if not version_info:
        return False
    
    # 加载当前版本信息
    current_info = load_version_info(version_dir)
    
    # 检查是否需要更新
    if current_info and current_info["build"] == version_info["build"]:
        # 检查是否所有文件都已存在
        all_files_exist = True
        for file_info in version_info["files"]:
            file_path = version_dir / file_info["name"]
            if not file_path.exists():
                all_files_exist = False
                break
        
        if all_files_exist:
            logger.info(f"{PROJECTS[project]['name']}版本 {version} 已经是最新构建: {version_info['build']}，所有文件已存在")
            return True
        else:
            logger.info(f"{PROJECTS[project]['name']}版本 {version} 构建 {version_info['build']} 有缺失文件，将重新下载")
    
    # 下载所有文件
    success = True
    for file_info in version_info["files"]:
        file_path = version_dir / file_info["name"]
        
        # 下载文件
        if not download_file(file_info["download_url"], file_path):
            success = False
            continue
        
        # 验证文件
        if not verify_file(file_path, file_info["sha256"]):
            success = False
            continue
            
        logger.info(f"文件 {file_info['name']} 同步成功")
    
    if not success:
        return False
    
    # 保存新版本信息
    save_version_info(version_dir, version_info)
    
    logger.info(f"{PROJECTS[project]['name']}版本 {version} 同步完成: 构建 {version_info['build']}")
    return True

def sync_project(project):
    """同步指定项目的所有版本"""
    logger.info(f"开始同步{PROJECTS[project]['name']}")
    project_dir = create_dirs(project)
    
    # 获取所有版本
    versions = get_versions(project)
    if not versions:
        return False
    
    success_count = 0
    failed_count = 0
    
    # 同步每个版本
    for version in versions:
        if sync_version(project, project_dir, version):
            success_count += 1
        else:
            failed_count += 1
    
    logger.info(f"{PROJECTS[project]['name']}同步完成. 成功: {success_count}, 失败: {failed_count}, 总计: {len(versions)}")
    return failed_count == 0

def sync_all_projects():
    """同步所有项目"""
    results = {}
    
    for project in PROJECTS.keys():
        print(f"开始同步{PROJECTS[project]['name']}...")
        success = sync_project(project)
        results[project] = success
        print(f"{PROJECTS[project]['name']}同步{'成功' if success else '部分失败'}")
    
    return all(results.values())

if __name__ == "__main__":
    try:
        logger.info("开始同步Minecraft服务端和代理...")
        success = sync_all_projects()
        if success:
            logger.info("所有项目同步成功完成!")
        else:
            logger.warning("某些项目同步失败，请查看日志获取详情")
    except KeyboardInterrupt:
        print("\n程序被用户中断")
        logger.warning("程序被用户中断")
    except Exception as e:
        logger.error(f"同步过程中出现错误: {str(e)}", exc_info=True)
        print(f"错误: 同步过程中出现未预期的错误 - {str(e)}") 