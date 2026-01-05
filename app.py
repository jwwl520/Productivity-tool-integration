#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import eel
import os
import platform
import hashlib
import secrets
import subprocess
import json
import requests
import time
import threading
import shutil
import uuid
import base64
import sys
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime

class EelToolLauncher:
    def __init__(self):
        # GitHub仓库配置
        self._internal_config = {
            'repositories': {
                "subtitle_merger": {
                    "owner": "jwwl520",
                    "repo": "Subtitle-merging",
                    "file_path": "专业字幕合并工具.py",
                    "local_name": "专业字幕合并工具.py",
                    "dependencies": ["pysrt", "opencv-python"]
                },
                "video_converter": {
                    "owner": "jwwl520",
                    "repo": "Automatic-Video-Blurring-Tool",
                    "file_path": "打码工具.py",
                    "local_name": "打码工具.py",
                    "dependencies": ["opencv-python", "numpy", "moviepy"]
                },
                "file_organizer": {
                    "owner": "jwwl520",
                    "repo": "File-Organization-Tool",
                    "file_path": "文件整理工具.py",
                    "local_name": "文件整理工具.py",
                    "dependencies": []
                }
            },
            # 前端界面仓库配置
            'web_interface': {
                "owner": "jwwl520",  # 改成你的GitHub用户名
                "repo": "Tool-Launcher-Web",  # 改成你的前端仓库名
                "files": [
                    {"path": "index.html", "local": "index.html"},
                    {"path": "style.css", "local": "style.css"},
                    {"path": "script.js", "local": "script.js"}
                ]
            }
        }
        
        # 工具配置
        self.tools = {
            "subtitle_merger": {
                "name": "字幕合并工具",
                "description": "专业的字幕文件合并工具",
                "icon": "🎬"
            },
            "video_converter": {
                "name": "视频模糊工具",
                "description": "高效的视频打码模糊工具",
                "icon": "🎥"
            },
            "file_organizer": {
                "name": "文件整理工具",
                "description": "智能文件分类整理工具",
                "icon": "📁"
            }
        }
        
        # 缓存配置
        self.cache_duration = 7 * 24 * 60 * 60  # 7天
        self.web_cache_duration = 24 * 60 * 60  # 前端文件缓存1天
        self.machine_id = self.get_machine_id()
        self.cache_dir = self.get_or_create_hidden_cache_dir()
        self.web_cache_dir = os.path.join(self.cache_dir, 'web')
        self.ensure_cache_directory()
        self.cleanup_old_cache_directories()
        
        self.tool_processes = {}
        self._python_interpreter = None

    def get_machine_id(self):
        """生成机器唯一标识"""
        system = platform.system()
        try:
            if system == "Windows":
                import subprocess
                result = subprocess.check_output(['wmic', 'csproduct', 'get', 'UUID'], 
                                                stderr=subprocess.DEVNULL)
                uuid_str = result.decode().split('\n')[1].strip()
            elif system == "Darwin":
                result = subprocess.check_output(['ioreg', '-rd1', '-c', 'IOPlatformExpertDevice'], 
                                                stderr=subprocess.DEVNULL)
                uuid_str = result.decode()
            elif system == "Linux":
                with open('/etc/machine-id', 'r') as f:
                    uuid_str = f.read().strip()
            else:
                uuid_str = str(uuid.uuid4())
            
            machine_hash = hashlib.sha256(uuid_str.encode()).hexdigest()
            return machine_hash[:16]
        except:
            return hashlib.sha256(str(uuid.uuid4()).encode()).hexdigest()[:16]

    def get_week_identifier(self):
        """获取当前周标识符（格式：YYYY-WW）"""
        now = datetime.now()
        week_num = now.isocalendar()[1]
        return f"{now.year}-W{week_num:02d}"

    def get_or_create_hidden_cache_dir(self):
        """创建隐藏的缓存目录"""
        week_id = self.get_week_identifier()
        cache_name = f".{self.machine_id}_{week_id}_{secrets.token_hex(4)}"
        
        if platform.system() == 'Windows':
            base_dir = os.path.join(os.getenv('LOCALAPPDATA', os.path.expanduser('~')), 'Temp')
        else:
            base_dir = '/tmp'
        
        cache_dir = os.path.join(base_dir, cache_name)
        
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir, exist_ok=True)
            if platform.system() == 'Windows':
                try:
                    subprocess.run(['attrib', '+H', cache_dir], check=False, 
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                except:
                    pass
        
        return cache_dir

    def ensure_cache_directory(self):
        """确保缓存目录存在"""
        os.makedirs(self.cache_dir, exist_ok=True)
        os.makedirs(self.web_cache_dir, exist_ok=True)

    def cleanup_old_cache_directories(self):
        """清理旧的缓存目录"""
        current_week = self.get_week_identifier()
        
        if platform.system() == 'Windows':
            base_dir = os.path.join(os.getenv('LOCALAPPDATA', os.path.expanduser('~')), 'Temp')
        else:
            base_dir = '/tmp'
        
        try:
            for item in os.listdir(base_dir):
                if item.startswith(f".{self.machine_id}_") and current_week not in item:
                    old_cache_path = os.path.join(base_dir, item)
                    try:
                        shutil.rmtree(old_cache_path)
                    except:
                        pass
        except:
            pass

    def get_python_interpreter(self):
        """获取Python解释器路径"""
        if self._python_interpreter:
            return self._python_interpreter
        
        if getattr(sys, 'frozen', False):
            self._python_interpreter = sys.executable
        else:
            self._python_interpreter = sys.executable
        
        return self._python_interpreter

    def download_file_from_github(self, owner, repo, file_path, local_path, progress_callback=None):
        """从GitHub下载文件（公共仓库无需token）"""
        try:
            # 使用GitHub API下载文件
            api_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{file_path}"
            
            headers = {
                'Accept': 'application/vnd.github.v3+json',
                'User-Agent': 'Python-Tool-Launcher'
            }
            
            response = requests.get(api_url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                content = response.json()
                
                if 'content' in content:
                    file_content = base64.b64decode(content['content'])
                    
                    with open(local_path, 'wb') as f:
                        f.write(file_content)
                    
                    if progress_callback:
                        progress_callback(100, f"文件下载完成")
                    
                    return True
                else:
                    if progress_callback:
                        progress_callback(0, f"文件内容为空")
                    return False
            else:
                if progress_callback:
                    progress_callback(0, f"下载失败: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            if progress_callback:
                progress_callback(0, f"下载异常: {str(e)}")
            return False

    def download_web_interface(self):
        """从GitHub下载前端界面文件"""
        try:
            web_config = self._internal_config.get('web_interface')
            if not web_config:
                return True  # 如果没有配置，使用本地文件
            
            print("正在检查前端文件更新...")
            
            for file_info in web_config['files']:
                local_path = os.path.join(self.web_cache_dir, file_info['local'])
                
                # 检查缓存是否有效
                cache_valid = False
                if os.path.exists(local_path):
                    file_age = time.time() - os.path.getmtime(local_path)
                    cache_valid = file_age < self.web_cache_duration
                
                # 如果缓存无效，下载新版本
                if not cache_valid:
                    print(f"下载: {file_info['path']}")
                    success = self.download_file_from_github(
                        web_config['owner'],
                        web_config['repo'],
                        file_info['path'],
                        local_path
                    )
                    
                    if not success:
                        print(f"警告: 无法下载 {file_info['path']}, 将使用本地文件")
                        # 如果下载失败且本地也没有，从web目录复制
                        if not os.path.exists(local_path):
                            local_web_file = os.path.join('web', file_info['local'])
                            if os.path.exists(local_web_file):
                                shutil.copy2(local_web_file, local_path)
                else:
                    print(f"使用缓存: {file_info['path']}")
            
            print("前端文件准备完成")
            return True
            
        except Exception as e:
            print(f"下载前端文件失败: {str(e)}")
            # 如果下载失败，尝试从本地web目录复制
            try:
                for file_info in web_config['files']:
                    local_path = os.path.join(self.web_cache_dir, file_info['local'])
                    if not os.path.exists(local_path):
                        local_web_file = os.path.join('web', file_info['local'])
                        if os.path.exists(local_web_file):
                            shutil.copy2(local_web_file, local_path)
            except:
                pass
            return True

    def check_and_install_dependencies(self, tool_id, progress_callback=None):
        """检查并安装依赖"""
        repo_config = self._internal_config['repositories'].get(tool_id)
        if not repo_config or not repo_config.get('dependencies'):
            return True
        
        python_cmd = self.get_python_interpreter()
        
        for i, package in enumerate(repo_config['dependencies']):
            if progress_callback:
                percent = (i / len(repo_config['dependencies'])) * 30
                progress_callback(percent, f"检查依赖: {package}")
            
            try:
                result = subprocess.run(
                    [python_cmd, '-m', 'pip', 'show', package],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=30
                )
                
                if result.returncode != 0:
                    if progress_callback:
                        progress_callback(percent, f"安装依赖: {package}")
                    
                    install_result = subprocess.run(
                        [python_cmd, '-m', 'pip', 'install', package],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        timeout=300
                    )
                    
                    if install_result.returncode != 0:
                        if progress_callback:
                            progress_callback(0, f"依赖安装失败: {package}")
                        return False
            except:
                return False
        
        if progress_callback:
            progress_callback(30, "依赖检查完成")
        
        return True

    def get_tools_list(self):
        """获取工具列表"""
        return self.tools

    def launch_tool(self, tool_id):
        """启动工具"""
        try:
            # 检查并安装依赖
            if not self.check_and_install_dependencies(tool_id, eel.updateProgress):
                return {"success": False, "message": "依赖安装失败"}
            
            eel.updateProgress(40, "准备工具文件...")
            
            # 获取仓库配置
            repo_config = self._internal_config['repositories'].get(tool_id)
            if not repo_config:
                return {"success": False, "message": "工具配置未找到"}
            
            # 本地缓存文件路径
            local_file = os.path.join(self.cache_dir, repo_config['local_name'])
            
            # 检查缓存是否存在且有效
            cache_valid = False
            if os.path.exists(local_file):
                file_age = time.time() - os.path.getmtime(local_file)
                cache_valid = file_age < self.cache_duration
            
            # 如果缓存无效，下载新版本
            if not cache_valid:
                eel.updateProgress(50, "正在下载工具...")
                success = self.download_file_from_github(
                    repo_config['owner'],
                    repo_config['repo'],
                    repo_config['file_path'],
                    local_file,
                    eel.updateProgress
                )
                
                if not success:
                    return {"success": False, "message": "工具下载失败"}
            
            eel.updateProgress(90, "启动工具...")
            
            # 启动工具
            python_cmd = self.get_python_interpreter()
            process = subprocess.Popen(
                [python_cmd, local_file],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NEW_CONSOLE if platform.system() == 'Windows' else 0
            )
            
            self.tool_processes[tool_id] = process
            
            eel.updateProgress(100, "启动成功")
            
            return {"success": True, "message": f"{self.tools[tool_id]['name']} 已启动"}
            
        except Exception as e:
            return {"success": False, "message": f"启动失败: {str(e)}"}

    def check_and_update_all(self):
        """检查并更新所有工具"""
        try:
            total_tools = len(self._internal_config['repositories'])
            
            for i, (tool_id, repo_config) in enumerate(self._internal_config['repositories'].items()):
                percent = (i / total_tools) * 100
                eel.updateProgress(percent, f"更新 {self.tools[tool_id]['name']}...")
                
                local_file = os.path.join(self.cache_dir, repo_config['local_name'])
                
                success = self.download_file_from_github(
                    repo_config['owner'],
                    repo_config['repo'],
                    repo_config['file_path'],
                    local_file,
                    eel.updateProgress
                )
                
                if not success:
                    return {"success": False, "message": f"更新 {self.tools[tool_id]['name']} 失败"}
            
            eel.updateProgress(100, "更新完成")
            
            return {"success": True, "message": "所有工具已更新到最新版本"}
            
        except Exception as e:
            return {"success": False, "message": f"更新失败: {str(e)}"}


# 全局 launcher 实例
launcher = None


@eel.expose
def get_tools_list():
    """获取工具列表"""
    return launcher.get_tools_list()


@eel.expose
def launch_tool(tool_id):
    """启动工具"""
    return launcher.launch_tool(tool_id)


@eel.expose
def check_and_update_all():
    """检查并更新所有工具"""
    return launcher.check_and_update_all()


def main():
    """主函数"""
    global launcher
    
    # 创建启动器实例
    launcher = EelToolLauncher()
    
    # 下载最新的前端界面文件
    launcher.download_web_interface()
    
    # 初始化Eel，使用缓存的web目录
    if os.path.exists(launcher.web_cache_dir) and os.listdir(launcher.web_cache_dir):
        eel.init(launcher.web_cache_dir)
        print(f"使用缓存的前端文件: {launcher.web_cache_dir}")
    else:
        # 如果缓存不存在，使用本地web目录
        eel.init('web')
        print("使用本地前端文件")
    
    # 启动应用
    try:
        eel.start('index.html', size=(1000, 700), port=0)
    except (SystemExit, MemoryError, KeyboardInterrupt):
        pass


if __name__ == '__main__':
    main()
