#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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
from datetime import datetime
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import webbrowser

class SimpleToolLauncher:
    def __init__(self):
        # 内部配置（用户不可见）- 手动配置下载链接
        self._internal_config = {
            'downloads': {
                "subtitle_merger": {
                    "download_url": "https://release-assets.githubusercontent.com/github-production-release-asset/1037134520/a3842f69-aa3b-4c5c-af6e-c9a356a5e7d5?sp=r&sv=2018-11-09&sr=b&spr=https&se=2025-08-22T07%3A56%3A40Z&rscd=attachment%3B+filename%3DSubtitle-merging.exe&rsct=application%2Foctet-stream&skoid=96c2d410-5711-43a1-aedd-ab1947aa7ab0&sktid=398a6654-997b-47e9-b12b-9515b896b4de&skt=2025-08-22T06%3A56%3A40Z&ske=2025-08-22T07%3A56%3A40Z&sks=b&skv=2018-11-09&sig=ou0E5z0pE2y9KfvkT5uSjzq77PKRK22Wlsy8shGZA7c%3D&jwt=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmVsZWFzZS1hc3NldHMuZ2l0aHVidXNlcmNvbnRlbnQuY29tIiwia2V5Ijoia2V5MSIsImV4cCI6MTc1NTg0NzU4NCwibmJmIjoxNzU1ODQ3Mjg0LCJwYXRoIjoicmVsZWFzZWFzc2V0cHJvZHVjdGlvbi5ibG9iLmNvcmUud2luZG93cy5uZXQifQ.4ohQF47tlnrE-sKB6vzjHcDxS1H25O0KyzqB1wb2888&response-content-disposition=attachment%3B%20filename%3DSubtitle-merging.exe&response-content-type=application%2Foctet-stream",
                    "exe_name": "Subtitle-merging.exe"
                },
                "video_converter": {
                    "download_url": "https://release-assets.githubusercontent.com/github-production-release-asset/1037137661/612ae7d5-5d5c-42ac-81b2-bae4a267767b?sp=r&sv=2018-11-09&sr=b&spr=https&se=2025-08-22T07%3A59%3A22Z&rscd=attachment%3B+filename%3DAutomatic-Video-Blurring-Tool.exe&rsct=application%2Foctet-stream&skoid=96c2d410-5711-43a1-aedd-ab1947aa7ab0&sktid=398a6654-997b-47e9-b12b-9515b896b4de&skt=2025-08-22T06%3A58%3A53Z&ske=2025-08-22T07%3A59%3A22Z&sks=b&skv=2018-11-09&sig=08y%2FtNbYsWfrZkHUQZ9rbHoZUMO0%2FyOUJwQwiYiQteU%3D&jwt=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmVsZWFzZS1hc3NldHMuZ2l0aHVidXNlcmNvbnRlbnQuY29tIiwia2V5Ijoia2V5MSIsImV4cCI6MTc1NTg0NzY4OCwibmJmIjoxNzU1ODQ3Mzg4LCJwYXRoIjoicmVsZWFzZWFzc2V0cHJvZHVjdGlvbi5ibG9iLmNvcmUud2luZG93cy5uZXQifQ.Hwso9oY7Uw8Ys1MA_tHKhi_ZcJhXvDicbRcGbKH5v04&response-content-disposition=attachment%3B%20filename%3DAutomatic-Video-Blurring-Tool.exe&response-content-type=application%2Foctet-stream",
                    "exe_name": "Automatic-Video-Blurring-Tool.exe"
                },
                "file_organizer": {
                    "download_url": "https://github.com/jwwl520/File-Organization-Tool/releases/download/%E6%96%87%E4%BB%B6%E6%95%B4%E7%90%86%E5%B7%A5%E5%85%B7/File-Organization-Tool.exe",
                    "exe_name": "File-Organization-Tool.exe"
                }
            }
        }
        
        # 工具配置（用户可见）
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
        
        # 保护机制：与客户端.py相同的方式，但缓存持久化
        self.cache_duration = 7 * 24 * 60 * 60  # 7天（一周）
        self.machine_id = self.get_machine_id()
        self.cache_dir = self.get_or_create_hidden_cache_dir()
        self.ensure_cache_directory()
        
        # 清理旧的缓存目录（非当前周的）
        self.cleanup_old_cache_directories()
        
        self.tool_processes = {}
        self.root = None

    def cleanup_old_cache_directories(self):
        """清理旧的缓存目录 - 只保留当前周的，彻底删除历史目录"""
        try:
            current_week_id = self.get_current_week_id()
            current_week_hash = hashlib.md5(f"{current_week_id}_{self.machine_id}".encode()).hexdigest()[:16]
            
            # Windows系统深层伪装路径
            if platform.system() == 'Windows':
                base_paths = [
                    os.path.join('C:', 'Windows', 'System32', 'drivers', 'etc', 'ssl', 'certs'),
                    os.path.join('C:', 'Windows', 'SysWOW64', 'config', 'systemprofile', 'AppData', 'LocalLow'),
                    os.path.join('C:', 'ProgramData', 'Microsoft', 'Windows Defender', 'Platform', 'Backup'),
                    os.path.join('C:', 'Windows', 'Temp', '.NET Framework Setup Cache', 'Client'),
                    os.path.join('C:', 'Windows', 'Microsoft.NET', 'assembly', 'GAC_64', 'temp'),
                    # 添加用户目录的清理
                    os.path.expanduser('~/.cache')
                ]
            else:
                base_paths = [
                    os.path.expanduser('~/.local/share/applications/.cache'),
                    os.path.expanduser('~/.config/fontconfig/.tmp'),
                    '/var/cache/fontconfig/.hidden',
                    '/tmp/.system-cache',
                    os.path.expanduser('~/.cache')
                ]
            
            # 清理旧的缓存目录
            cleaned_count = 0
            total_size_cleaned = 0
            
            for base_path in base_paths:
                if os.path.exists(base_path):
                    try:
                        for item in os.listdir(base_path):
                            # 匹配我们的隐藏目录格式: .开头 + 16位十六进制
                            if (item.startswith('.') and len(item) == 17 and 
                                all(c in '0123456789abcdef' for c in item[1:])):
                                
                                old_cache_path = os.path.join(base_path, item)
                                
                                # 确保是目录且不是当前周的目录
                                if (os.path.isdir(old_cache_path) and 
                                    item[1:] != current_week_hash):
                                    
                                    # 计算目录大小
                                    try:
                                        dir_size = self.get_directory_size(old_cache_path)
                                        total_size_cleaned += dir_size
                                    except:
                                        dir_size = 0
                                    
                                    # 强制删除目录（包括只读文件）
                                    try:
                                        self.force_remove_directory(old_cache_path)
                                        cleaned_count += 1
                                        # 静默删除，不输出日志
                                    except Exception as e:
                                        # 静默失败，不输出错误信息
                                        pass
                                        
                    except Exception as e:
                        # 静默处理扫描失败
                        pass
            
            if cleaned_count > 0:
                pass  # 静默清理，不输出信息
            else:
                pass  # 静默，不输出信息
                
        except Exception as e:
            # 静默处理清理失败
            pass

    def get_directory_size(self, path):
        """计算目录大小"""
        total_size = 0
        try:
            for dirpath, dirnames, filenames in os.walk(path):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    try:
                        total_size += os.path.getsize(filepath)
                    except:
                        pass
        except:
            pass
        return total_size

    def force_remove_directory(self, path):
        """强制删除目录，包括只读文件"""
        def handle_remove_readonly(func, path, exc):
            """处理只读文件删除"""
            if os.path.exists(path):
                os.chmod(path, 0o777)
                func(path)
        
        try:
            # Windows系统先移除只读属性
            if platform.system() == 'Windows':
                try:
                    subprocess.run(['attrib', '-R', '-H', '-S', path, '/S', '/D'], 
                                 capture_output=True, timeout=30)
                except:
                    pass
            
            # 递归删除目录
            shutil.rmtree(path, onerror=handle_remove_readonly)
            
        except Exception as e:
            # 如果常规删除失败，尝试逐文件删除
            try:
                for root, dirs, files in os.walk(path, topdown=False):
                    for file in files:
                        file_path = os.path.join(root, file)
                        try:
                            os.chmod(file_path, 0o777)
                            os.remove(file_path)
                        except:
                            pass
                    for dir in dirs:
                        dir_path = os.path.join(root, dir)
                        try:
                            os.chmod(dir_path, 0o777)
                            os.rmdir(dir_path)
                        except:
                            pass
                os.rmdir(path)
            except Exception as final_e:
                raise Exception(f"无法删除目录: {final_e}")

    def get_current_week_id(self):
        """获取当前周标识 - 用于一周更换一次缓存目录"""
        from datetime import datetime, timedelta
        now = datetime.now()
        # 获取本周一的日期作为周标识
        monday = now - timedelta(days=now.weekday())
        week_str = monday.strftime("%Y%m%d")  # 格式：20250818
        return hashlib.md5(week_str.encode()).hexdigest()[:8]

    def get_machine_id(self):
        """生成机器唯一标识 - 与客户端.py相同"""
        machine_info = {
            'hostname': platform.node(),
            'system': platform.system(),
            'processor': platform.processor(),
            'mac_address': hex(uuid.getnode())
        }
        machine_string = json.dumps(machine_info, sort_keys=True)
        return hashlib.md5(machine_string.encode()).hexdigest()[:16]

    def get_system_config_path(self):
        """获取系统深层目录中的配置文件路径 - 与客户端.py相同"""
        system = platform.system()
        
        if system == 'Windows':
            base_path = os.environ.get('PROGRAMDATA', 'C:\\ProgramData')
            deep_path = os.path.join(
                base_path,
                'Microsoft',
                'Windows',
                'WER',
                'Temp',
                f'.{secrets.token_hex(6)}',
                'Cache',
                f'{self.machine_id[:8]}.cfg'
            )
        elif system == 'Darwin':
            base_path = os.path.expanduser('~/Library')
            deep_path = os.path.join(
                base_path,
                'Caches',
                'com.apple.Safari',
                'WebKitCache',
                f'.{secrets.token_hex(6)}',
                f'{self.machine_id[:8]}.plist'
            )
        else:
            base_path = os.path.expanduser('~/.cache')
            deep_path = os.path.join(
                base_path,
                'fontconfig',
                f'.{secrets.token_hex(6)}',
                f'{self.machine_id[:8]}.conf'
            )
        
        return deep_path

    def get_or_create_hidden_cache_dir(self):
        """获取或创建隐藏的缓存目录 - C盘深层伪装，一周更换一次"""
        config_key = 'hidden_cache_dir'
        system_config_file = self.get_system_config_path()
        current_week_id = self.get_current_week_id()
        
        # 尝试从系统配置文件读取已存在的目录
        if os.path.exists(system_config_file):
            try:
                with open(system_config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    if (config_key in config and 
                        'week_id' in config and 
                        config['week_id'] == current_week_id and 
                        os.path.exists(config[config_key])):
                        # 静默使用已存在的缓存目录
                        return config[config_key]
            except:
                pass
        
        # 生成C盘深层伪装目录结构
        week_hash = hashlib.md5(f"{current_week_id}_{self.machine_id}".encode()).hexdigest()
        
        # Windows系统深层伪装路径
        if platform.system() == 'Windows':
            base_paths = [
                os.path.join('C:', 'Windows', 'System32', 'drivers', 'etc', 'ssl', 'certs'),
                os.path.join('C:', 'Windows', 'SysWOW64', 'config', 'systemprofile', 'AppData', 'LocalLow'),
                os.path.join('C:', 'ProgramData', 'Microsoft', 'Windows Defender', 'Platform', 'Backup'),
                os.path.join('C:', 'Windows', 'Temp', '.NET Framework Setup Cache', 'Client'),
                os.path.join('C:', 'Windows', 'Microsoft.NET', 'assembly', 'GAC_64', 'temp')
            ]
        else:
            # 非Windows系统的深层路径
            base_paths = [
                os.path.expanduser('~/.local/share/applications/.cache'),
                os.path.expanduser('~/.config/fontconfig/.tmp'),
                '/var/cache/fontconfig/.hidden',
                '/tmp/.system-cache'
            ]
        
        # 选择一个可写的基础路径
        cache_dir = None
        for base_path in base_paths:
            try:
                # 使用周哈希生成子目录名
                dir_name = f".{week_hash[:16]}"
                test_cache_dir = os.path.join(base_path, dir_name)
                
                # 尝试创建目录
                if not os.path.exists(test_cache_dir):
                    os.makedirs(test_cache_dir, exist_ok=True)
                
                # 测试写入权限
                test_file = os.path.join(test_cache_dir, 'test.tmp')
                with open(test_file, 'w') as f:
                    f.write('test')
                os.remove(test_file)
                
                cache_dir = test_cache_dir
                # 静默创建缓存目录
                break
                
            except (OSError, PermissionError):
                continue
        
        # 如果所有深层路径都失败，回退到用户目录的隐藏文件夹
        if not cache_dir:
            fallback_dir = os.path.expanduser(f"~/.cache/.{week_hash[:16]}")
            os.makedirs(fallback_dir, exist_ok=True)
            cache_dir = fallback_dir
            # 静默使用回退目录
        
        # 在Windows上设置隐藏和系统属性
        if platform.system() == 'Windows':
            try:
                subprocess.run(['attrib', '+H', '+S', cache_dir], check=True, capture_output=True)
                # 设置父目录也为隐藏
                parent_dir = os.path.dirname(cache_dir)
                subprocess.run(['attrib', '+H', parent_dir], capture_output=True)
            except:
                pass
        
        # 保存配置，包含周标识
        config_data = {
            config_key: cache_dir,
            'week_id': current_week_id,
            'created_at': datetime.now().isoformat()
        }
        self.save_system_config(config_data)
        return cache_dir

    def save_system_config(self, config_data):
        """保存配置到系统深层目录 - 与客户端.py相同"""
        try:
            system_config_file = self.get_system_config_path()
            config_dir = os.path.dirname(system_config_file)
            
            if not os.path.exists(config_dir):
                os.makedirs(config_dir)
                if platform.system() == 'Windows':
                    try:
                        subprocess.run(['attrib', '+H', config_dir], capture_output=True)
                    except:
                        pass
            
            with open(system_config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
                
            if platform.system() == 'Windows':
                try:
                    subprocess.run(['attrib', '+H', system_config_file], capture_output=True)
                except:
                    pass
        except Exception as e:
            print(f"警告：无法保存到系统目录，使用当前目录: {e}")
            fallback_file = f".{secrets.token_hex(4)}.cfg"
            try:
                with open(fallback_file, 'w', encoding='utf-8') as f:
                    json.dump(config_data, f, indent=2, ensure_ascii=False)
                if platform.system() == 'Windows':
                    subprocess.run(['attrib', '+H', fallback_file], capture_output=True)
            except:
                pass

    def ensure_cache_directory(self):
        """确保缓存目录存在"""
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)

    def get_cache_file_path(self, tool_id):
        """获取工具缓存文件路径 - 使用哈希文件名保护"""
        if tool_id in self._internal_config['downloads']:
            exe_name = self._internal_config['downloads'][tool_id]['exe_name']
            return os.path.join(self.cache_dir, exe_name)
        hashed_name = hashlib.md5(tool_id.encode()).hexdigest()
        return os.path.join(self.cache_dir, f"{hashed_name}.dat")

    def get_cache_info_path(self, tool_id):
        """获取缓存信息文件路径 - 使用哈希文件名保护"""
        hashed_name = hashlib.md5(f"{tool_id}_info".encode()).hexdigest()
        return os.path.join(self.cache_dir, f"{hashed_name}.cfg")

    def is_cache_valid(self, tool_id):
        """检查缓存是否有效"""
        cache_info_path = self.get_cache_info_path(tool_id)
        cache_file_path = self.get_cache_file_path(tool_id)
        
        if not os.path.exists(cache_info_path) or not os.path.exists(cache_file_path):
            return False
        
        try:
            with open(cache_info_path, 'r', encoding='utf-8') as f:
                cache_info = json.load(f)
            
            cache_time = datetime.fromisoformat(cache_info['cached_at'])
            current_time = datetime.now()
            
            time_diff = (current_time - cache_time).total_seconds()
            return time_diff < self.cache_duration
            
        except Exception as e:
            # 静默处理缓存检查失败
            return False

    def get_download_info(self, tool_id):
        """获取工具下载信息"""
        if tool_id not in self._internal_config['downloads']:
            return None
            
        config = self._internal_config['downloads'][tool_id]
        return {
            'download_url': config['download_url'],
            'exe_name': config['exe_name']
        }

    def download_exe_from_release(self, tool_id, progress_callback=None):
        """下载exe文件 - 支持进度回调"""
        if self.is_cache_valid(tool_id):
            return self.get_cache_file_path(tool_id)
        
        download_info = self.get_download_info(tool_id)
        if not download_info or not download_info['download_url']:
            # 静默处理获取下载链接失败
            return None
        
        try:
            download_url = download_info['download_url']
            # 静默下载，不输出调试信息
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/octet-stream, */*',
            }
            
            response = requests.get(download_url, headers=headers, timeout=60, stream=True)
            
            if response.status_code == 200:
                # 获取文件总大小
                total_size = int(response.headers.get('content-length', 0))
                downloaded_size = 0
                exe_data = b''
                
                # 分块下载并更新进度
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        exe_data += chunk
                        downloaded_size += len(chunk)
                        
                        # 更新进度条
                        if progress_callback and total_size > 0:
                            progress = (downloaded_size / total_size) * 100
                            progress_callback(progress, downloaded_size, total_size)
                
                if self.save_exe_to_cache(tool_id, exe_data, "latest"):
                    return self.get_cache_file_path(tool_id)
            else:
                # 静默处理下载失败
                pass
                
        except Exception as e:
            # 静默处理下载异常
            pass
            
        return None

    def save_exe_to_cache(self, tool_id, exe_data, version):
        """保存exe文件到缓存 - 与客户端.py相同的加密方式"""
        try:
            cache_file_path = self.get_cache_file_path(tool_id)
            cache_info_path = self.get_cache_info_path(tool_id)
            
            # 保存二进制exe文件
            with open(cache_file_path, 'wb') as f:
                f.write(exe_data)
            
            # 保存缓存信息
            cache_info = {
                'tool_id': tool_id,
                'cached_at': datetime.now().isoformat(),
                'file_size': len(exe_data),
                'version': version,
                'file_type': 'exe'
            }
            
            with open(cache_info_path, 'w', encoding='utf-8') as f:
                json.dump(cache_info, f, ensure_ascii=False, indent=2)
            
            # 静默保存成功，不输出调试信息
            return True
            
        except Exception as e:
            # 静默处理保存失败
            return False

    def create_main_window(self):
        """创建简化的主窗口"""
        self.root = tk.Tk()
        self.root.title("生产力工具整合")
        self.root.geometry("500x400")
        self.root.configure(bg='#f0f0f0')
        
        # 居中显示
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() - self.root.winfo_width()) // 2
        y = (self.root.winfo_screenheight() - self.root.winfo_height()) // 2
        self.root.geometry(f"+{x}+{y}")
        
        # 标题
        title_label = tk.Label(self.root, text="生产力工具整合", 
                              font=("Microsoft YaHei UI", 16, "bold"),
                              bg='#f0f0f0', fg='#2c3e50')
        title_label.pack(pady=20)
        
        # 工具列表
        self.tools_frame = tk.Frame(self.root, bg='#f0f0f0')
        self.tools_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=20)
        
        # 创建工具按钮
        for tool_id, tool_info in self.tools.items():
            self.create_tool_button(tool_id, tool_info)
        
        # 状态栏
        self.status_label = tk.Label(self.root, text="就绪", 
                                    font=("Microsoft YaHei UI", 9),
                                    bg='#95a5a6', fg='white')
        self.status_label.pack(fill=tk.X, pady=(0, 0))

    def create_tool_button(self, tool_id, tool_info):
        """创建简化的工具按钮"""
        button_frame = tk.Frame(self.tools_frame, bg='white', relief=tk.RAISED, bd=1)
        button_frame.pack(fill=tk.X, pady=5)
        
        content_frame = tk.Frame(button_frame, bg='white')
        content_frame.pack(fill=tk.X, padx=15, pady=10)
        
        # 工具信息
        info_frame = tk.Frame(content_frame, bg='white')
        info_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        name_label = tk.Label(info_frame, text=f"{tool_info['icon']} {tool_info['name']}", 
                             font=("Microsoft YaHei UI", 11, "bold"),
                             bg='white', fg='#333333')
        name_label.pack(anchor=tk.W)
        
        desc_label = tk.Label(info_frame, text=tool_info['description'],
                             font=("Microsoft YaHei UI", 9),
                             bg='white', fg='#666666')
        desc_label.pack(anchor=tk.W, pady=(2, 0))
        
        # 启动按钮
        launch_btn = tk.Button(content_frame, text="启动",
                              command=lambda: self.launch_tool(tool_id),
                              font=("Microsoft YaHei UI", 10),
                              bg='#007acc', fg='white', 
                              padx=20, pady=5, relief=tk.FLAT)
        launch_btn.pack(side=tk.RIGHT, padx=(10, 0))

    def show_download_progress(self, tool_id, tool_name):
        """显示下载进度窗口"""
        # 创建进度窗口
        progress_window = tk.Toplevel(self.root)
        progress_window.title(f"下载 {tool_name}")
        progress_window.geometry("400x180")
        progress_window.configure(bg='#f0f0f0')
        progress_window.resizable(False, False)
        
        # 居中显示
        progress_window.transient(self.root)
        progress_window.grab_set()
        
        # 标题
        title_label = tk.Label(progress_window, text=f"正在下载 {tool_name}", 
                              font=("Microsoft YaHei UI", 12, "bold"),
                              bg='#f0f0f0', fg='#2c3e50')
        title_label.pack(pady=15)
        
        # 进度条
        progress_var = tk.DoubleVar()
        progress_bar = ttk.Progressbar(progress_window, 
                                      variable=progress_var, 
                                      maximum=100,
                                      length=350,
                                      mode='determinate')
        progress_bar.pack(pady=10)
        
        # 进度信息
        info_label = tk.Label(progress_window, text="准备下载...", 
                             font=("Microsoft YaHei UI", 9),
                             bg='#f0f0f0', fg='#666666')
        info_label.pack(pady=5)
        
        # VPN提示
        vpn_label = tk.Label(progress_window, 
                            text="下载缓慢或下载失败请尝试开启VPN下载", 
                            font=("Microsoft YaHei UI", 9),
                            bg='#f0f0f0', fg='#e74c3c')
        vpn_label.pack(pady=10)
        
        # 取消按钮
        cancel_btn = tk.Button(progress_window, text="取消",
                              command=lambda: progress_window.destroy(),
                              font=("Microsoft YaHei UI", 9),
                              bg='#95a5a6', fg='white', 
                              padx=20, pady=5, relief=tk.FLAT)
        cancel_btn.pack(pady=5)
        
        return progress_window, progress_var, info_label

    def format_file_size(self, size_bytes):
        """格式化文件大小"""
        if size_bytes == 0:
            return "0 B"
        size_names = ["B", "KB", "MB", "GB"]
        import math
        i = int(math.floor(math.log(size_bytes, 1024)))
        p = math.pow(1024, i)
        s = round(size_bytes / p, 2)
        return f"{s} {size_names[i]}"

    def launch_tool(self, tool_id):
        """启动工具"""
        if tool_id in self.tool_processes:
            try:
                if self.tool_processes[tool_id].poll() is None:
                    messagebox.showinfo("提示", f"{self.tools[tool_id]['name']} 已在运行")
                    return
                else:
                    del self.tool_processes[tool_id]
            except:
                if tool_id in self.tool_processes:
                    del self.tool_processes[tool_id]
        
        # 检查缓存是否有效，如果有效直接启动
        if self.is_cache_valid(tool_id):
            self.start_cached_tool(tool_id)
            return
            
        # 需要下载，显示进度窗口
        tool_name = self.tools[tool_id]['name']
        progress_window, progress_var, info_label = self.show_download_progress(tool_id, tool_name)
        
        self.status_label.config(text=f"正在下载 {tool_name}...")
        
        def progress_callback(progress, downloaded, total):
            """进度更新回调"""
            progress_var.set(progress)
            if total > 0:
                info_text = f"已下载: {self.format_file_size(downloaded)} / {self.format_file_size(total)} ({progress:.1f}%)"
            else:
                info_text = f"已下载: {self.format_file_size(downloaded)}"
            info_label.config(text=info_text)
            progress_window.update_idletasks()
        
        def download_and_run():
            try:
                exe_path = self.download_exe_from_release(tool_id, progress_callback)
                
                # 关闭进度窗口
                self.root.after(0, lambda: progress_window.destroy())
                
                if exe_path and os.path.exists(exe_path):
                    # 启动exe进程
                    process = subprocess.Popen([exe_path], 
                                             cwd=os.path.dirname(exe_path))
                    self.tool_processes[tool_id] = process
                    self.root.after(0, lambda: self.status_label.config(text=f"{tool_name} 已启动"))
                    # 静默启动成功，不输出调试信息
                else:
                    self.root.after(0, lambda: messagebox.showerror("下载失败", 
                        f"无法下载 {tool_name}\n\n建议：\n1. 检查网络连接\n2. 尝试开启VPN\n3. 稍后重试"))
                    self.root.after(0, lambda: self.status_label.config(text="就绪"))
            except Exception as e:
                # 关闭进度窗口
                self.root.after(0, lambda: progress_window.destroy())
                self.root.after(0, lambda: messagebox.showerror("启动失败", 
                    f"下载或启动失败: {str(e)}\n\n建议：\n1. 检查网络连接\n2. 尝试开启VPN\n3. 稍后重试"))
                self.root.after(0, lambda: self.status_label.config(text="就绪"))
        
        threading.Thread(target=download_and_run, daemon=True).start()
    
    def start_cached_tool(self, tool_id):
        """启动已缓存的工具"""
        try:
            exe_path = self.get_cache_file_path(tool_id)
            tool_name = self.tools[tool_id]['name']
            
            if os.path.exists(exe_path):
                process = subprocess.Popen([exe_path], cwd=os.path.dirname(exe_path))
                self.tool_processes[tool_id] = process
                self.status_label.config(text=f"{tool_name} 已启动")
                # 静默启动缓存工具，不输出调试信息
            else:
                messagebox.showerror("错误", f"缓存文件不存在: {exe_path}")
        except Exception as e:
            messagebox.showerror("启动失败", f"启动工具失败: {str(e)}")
            self.status_label.config(text="就绪")

    def safe_exit(self):
        """安全退出程序 - 缓存目录保持不删除"""
        try:
            # 关闭所有工具进程
            for tool_id, process in list(self.tool_processes.items()):
                try:
                    if process.poll() is None:
                        process.terminate()
                except:
                    pass
            
            # 不再清理缓存目录，让缓存持久化一周
            # 静默退出，不输出调试信息
            self.root.quit()
        except Exception as e:
            # 静默处理退出错误
            self.root.quit()

    def run(self):
        """运行程序"""
        try:
            self.create_main_window()
            
            def on_closing():
                self.safe_exit()
            
            self.root.protocol("WM_DELETE_WINDOW", on_closing)
            self.root.mainloop()
            
            return True
            
        except Exception as e:
            if self.root:
                messagebox.showerror("启动失败", f"程序启动失败: {str(e)}")
            else:
                print(f"程序启动失败: {str(e)}")
            return False

def main():
    """主函数"""
    print("=" * 50)
    print("生产力工具整合 - 简化版")
    print("作者: jwwl520")
    print("=" * 50)
    print()
    
    try:
        launcher = SimpleToolLauncher()
        launcher.run()
    except KeyboardInterrupt:
        print("\n用户取消操作")
    except Exception as e:
        print(f"程序异常退出: {e}")
        input("按回车键退出...")

if __name__ == "__main__":
    main()
