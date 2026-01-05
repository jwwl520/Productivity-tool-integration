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
import logging
import multiprocessing

# 配置日志系统（打包后不显示命令行窗口）
if getattr(sys, 'frozen', False):
    # 打包后：将日志输出到文件
    log_dir = os.path.join(os.getenv('LOCALAPPDATA', os.path.expanduser('~')), 'Temp', 'ProductivityTools')
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, 'app.log')
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
        ]
    )
    
    # 重定向标准输出到空设备（避免弹出命令行窗口）
    class NullWriter:
        def write(self, text): pass
        def flush(self): pass
    
    sys.stdout = NullWriter()
    sys.stderr = NullWriter()
else:
    # 开发模式：输出到控制台
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )
    
    # 设置控制台输出编码为UTF-8
    if sys.stdout is not None and hasattr(sys.stdout, 'encoding') and sys.stdout.encoding != 'utf-8':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    if sys.stderr is not None and hasattr(sys.stderr, 'encoding') and sys.stderr.encoding != 'utf-8':
        import io
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 定义 print 函数的替代品
def log_print(*args, **kwargs):
    """替代 print 的日志函数"""
    message = ' '.join(str(arg) for arg in args)
    logging.info(message)

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
                "owner": "jwwl520",
                "repo": "Productivity-tool-integration",
                "files": [
                    {"path": "web/index.html", "local": "index.html"},
                    {"path": "web/style.css", "local": "style.css"},
                    {"path": "web/script.js", "local": "script.js"},
                    {"path": "web/config.js", "local": "config.js"}  # 授权配置文件
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
        self.cache_duration = 7 * 24 * 60 * 60  # 工具文件：7天
        self.web_cache_duration = 7 * 24 * 60 * 60  # 前端文件：7天（按周缓存）
        self.machine_id = self.get_machine_id()
        
        self.cache_dir = self.get_or_create_hidden_cache_dir()
        self.web_cache_dir = os.path.join(self.cache_dir, 'web')
        self.ensure_cache_directory()
        self.cleanup_old_cache_directories()
        
        # 设备授权验证（在下载前端文件之前先用本地配置验证）
        if not self.verify_device_authorization():
            log_print("\n" + "="*60)
            log_print("🚫 设备未授权")
            log_print(f"📱 当前设备ID: {self.machine_id}")
            log_print("📧 请联系管理员获取授权")
            log_print("="*60 + "\n")
            sys.exit(1)
        
        self.tool_processes = {}
        self._python_interpreter = None

    def get_machine_id(self):
        """获取Windows设备ID（系统属性中显示的设备ID）"""
        system = platform.system()
        try:
            if system == "Windows":
                # 方法1：通过注册表获取MachineGuid（最稳定）
                try:
                    import winreg
                    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                                        r'SOFTWARE\Microsoft\Cryptography', 
                                        0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY)
                    machine_guid = winreg.QueryValueEx(key, 'MachineGuid')[0]
                    winreg.CloseKey(key)
                    uuid_str = machine_guid
                    # 保存原始GUID供显示用
                    self._original_guid = uuid_str
                except:
                    # 方法2：通过WMIC获取UUID
                    result = subprocess.check_output(['wmic', 'csproduct', 'get', 'UUID'], 
                                                    stderr=subprocess.DEVNULL)
                    uuid_str = result.decode().split('\n')[1].strip()
                    self._original_guid = uuid_str
            elif system == "Darwin":
                result = subprocess.check_output(['ioreg', '-rd1', '-c', 'IOPlatformExpertDevice'], 
                                                stderr=subprocess.DEVNULL)
                uuid_str = result.decode()
                self._original_guid = uuid_str
            elif system == "Linux":
                with open('/etc/machine-id', 'r') as f:
                    uuid_str = f.read().strip()
                self._original_guid = uuid_str
            else:
                uuid_str = str(uuid.uuid4())
                self._original_guid = uuid_str
            
            # 返回完整的SHA256哈希的前16位
            machine_hash = hashlib.sha256(uuid_str.encode()).hexdigest()
            return machine_hash[:16]
        except Exception as e:
            log_print(f"警告: 无法获取设备ID: {e}")
            fallback = str(uuid.uuid4())
            self._original_guid = fallback
            return hashlib.sha256(fallback.encode()).hexdigest()[:16]

    def verify_device_authorization(self):
        """验证设备是否授权（从GitHub下载的config.js读取）"""
        try:
            # 从缓存的web目录读取config.js
            config_path = os.path.join(self.web_cache_dir, 'config.js')
            
            # 如果缓存不存在，尝试从本地web目录读取
            if not os.path.exists(config_path):
                config_path = os.path.join('web', 'config.js')
            
            if not os.path.exists(config_path):
                log_print("⚠️  警告: 授权配置文件不存在")
                log_print(f"💡 当前设备ID: {self.machine_id}")
                log_print("   请创建 web/config.js 并添加授权设备\n")
                return True  # 开发模式，允许运行
            
            # 读取配置文件
            with open(config_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 提取AUTHORIZED_DEVICES数组中的GUID
            import re
            pattern_guid = r'"([A-F0-9]{8}-[A-F0-9]{4}-[A-F0-9]{4}-[A-F0-9]{4}-[A-F0-9]{12})"'
            authorized_guids = re.findall(pattern_guid, content, re.IGNORECASE)
            
            # 转换为小写以便比对
            authorized_guids_lower = [g.lower() for g in authorized_guids]
            current_guid_lower = getattr(self, '_original_guid', '').lower()
            
            log_print(f"📋 从配置读取到 {len(authorized_guids)} 个授权设备")
            for guid in authorized_guids:
                log_print(f"   {guid}")
            
            log_print(f"\n💻 当前设备GUID: {getattr(self, '_original_guid', '未知')}")
            
            if not authorized_guids:
                log_print("\n⚠️  警告: 未配置授权设备列表")
                log_print("   请将设备GUID添加到 web/config.js 的 AUTHORIZED_DEVICES 数组中")
                log_print("   格式: \"3dc6a97e-2166-48b5-ab74-92bbc1674ec5\"")
                log_print("   然后推送到GitHub，其他用户重启程序即可获得授权\n")
                return True  # 开发模式，允许运行
            
            # 直接比对原始GUID（不区分大小写）
            if current_guid_lower in authorized_guids_lower:
                log_print(f"✅ 设备已授权\n")
                return True
            else:
                log_print(f"\n❌ 设备未在授权列表中")
                log_print(f"💡 请将以下GUID添加到 web/config.js：")
                log_print(f'   "{getattr(self, "_original_guid", "未知")}"')
                return False
                
        except Exception as e:
            log_print(f"❌ 授权验证错误: {e}")
            import traceback
            traceback.print_exc()
            log_print(f"💡 当前设备ID: {self.machine_id}\n")
            return False
    
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
            # 打包后：需要使用系统的 Python 解释器，而不是 EXE 本身
            # 尝试查找系统 Python
            possible_pythons = [
                'python',  # PATH 中的 python
                'python3',  # PATH 中的 python3
                r'C:\Windows\py.exe',  # Python Launcher
                r'C:\Python39\python.exe',
                r'C:\Python310\python.exe',
                r'C:\Python311\python.exe',
                r'C:\Python312\python.exe',
                r'C:\Python313\python.exe',
            ]
            
            for py in possible_pythons:
                try:
                    # 测试是否可用
                    result = subprocess.run(
                        [py, '--version'], 
                        capture_output=True, 
                        timeout=2,
                        creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == 'Windows' else 0
                    )
                    if result.returncode == 0:
                        self._python_interpreter = py
                        log_print(f"   ✓ 找到Python解释器: {py}")
                        return self._python_interpreter
                except:
                    continue
            
            # 如果都找不到，尝试使用 py launcher
            self._python_interpreter = 'python'
            log_print("   ⚠ 未找到Python解释器，使用默认: python")
        else:
            self._python_interpreter = sys.executable
        
        return self._python_interpreter

    def get_pythonw_interpreter(self):
        """获取 pythonw.exe 路径（用于启动GUI工具，不显示控制台）"""
        if getattr(sys, 'frozen', False):
            # 打包后：查找 pythonw.exe
            possible_pythonws = [
                'pythonw',  # PATH 中的 pythonw
                'pythonw.exe',
            ]
            
            # 先尝试直接使用 pythonw
            for pyw in possible_pythonws:
                try:
                    result = subprocess.run(
                        [pyw, '--version'], 
                        capture_output=True, 
                        timeout=2,
                        creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == 'Windows' else 0
                    )
                    if result.returncode == 0:
                        return pyw
                except:
                    continue
            
            # 如果找不到 pythonw，尝试从 python.exe 路径推导 pythonw.exe
            python_cmd = self.get_python_interpreter()
            if python_cmd and python_cmd.endswith('python.exe'):
                pythonw_cmd = python_cmd.replace('python.exe', 'pythonw.exe')
                if os.path.exists(pythonw_cmd):
                    return pythonw_cmd
            elif python_cmd and python_cmd == 'python':
                # 尝试 pythonw
                try:
                    result = subprocess.run(
                        ['pythonw', '--version'],
                        capture_output=True,
                        timeout=2,
                        creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == 'Windows' else 0
                    )
                    if result.returncode == 0:
                        return 'pythonw'
                except:
                    pass
        
        # 如果找不到 pythonw，返回普通的 python
        return self.get_python_interpreter()

    def download_file_from_github(self, owner, repo, file_path, local_path, progress_callback=None):
        """从GitHub下载文件（使用raw.githubusercontent.com，无速率限制）"""
        # 确保父目录存在
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        
        # 使用 raw.githubusercontent.com 直接下载（避免API速率限制）
        raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/main/{file_path}"
        
        headers = {
            'User-Agent': 'Python-Tool-Launcher'
        }
        
        # 重试机制：最多3次
        max_retries = 3
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    log_print(f"      重试下载 ({attempt+1}/{max_retries})...")
                    time.sleep(2)  # 等待2秒再重试
                
                response = requests.get(raw_url, headers=headers, timeout=30)
                
                if response.status_code == 200:
                    file_content = response.content
                    
                    with open(local_path, 'wb') as f:
                        f.write(file_content)
                    
                    log_print(f"      下载完成: {len(file_content)} bytes")
                    
                    if progress_callback:
                        try:
                            progress_callback(100, f"文件下载完成")
                        except:
                            pass  # 忽略回调错误（可能Eel未初始化）
                    
                    return True
                else:
                    error_msg = f"HTTP {response.status_code}"
                    log_print(f"      下载失败: {error_msg}")
                    if attempt == max_retries - 1:  # 最后一次尝试
                        if progress_callback:
                            try:
                                progress_callback(0, f"下载失败: {error_msg}")
                            except:
                                pass
                        return False
                    
            except Exception as e:
                error_msg = str(e)
                log_print(f"      下载异常: {error_msg}")
                if attempt == max_retries - 1:  # 最后一次尝试
                    if progress_callback:
                        try:
                            progress_callback(0, f"下载失败，请检查网络连接")
                        except:
                            pass
                    return False
        
        return False

    def download_web_interface(self):
        """从GitHub下载前端界面文件（仅在缓存无效时）"""
        try:
            web_config = self._internal_config.get('web_interface')
            if not web_config:
                return True  # 如果没有配置，使用本地文件
            
            # 检查是否所有文件都已缓存且有效
            all_cached = True
            for file_info in web_config['files']:
                local_path = os.path.join(self.web_cache_dir, file_info['local'])
                if not os.path.exists(local_path):
                    all_cached = False
                    break
                file_age = time.time() - os.path.getmtime(local_path)
                if file_age >= self.web_cache_duration:
                    all_cached = False
                    break
            
            # 如果所有文件都有效，直接使用缓存
            if all_cached:
                log_print("✓ 前端文件缓存有效")
                log_print(f"✓ 使用缓存的前端文件: {self.web_cache_dir}")
                return True
            
            # 缓存无效，需要下载
            log_print("正在检查前端文件更新...")
            
            for file_info in web_config['files']:
                local_path = os.path.join(self.web_cache_dir, file_info['local'])
                
                # 检查缓存是否有效
                cache_valid = False
                if os.path.exists(local_path):
                    file_age = time.time() - os.path.getmtime(local_path)
                    cache_valid = file_age < self.web_cache_duration
                    if cache_valid:
                        days_old = file_age / (24 * 60 * 60)
                        log_print(f"   ✓ 缓存有效: {file_info['local']} (已缓存 {days_old:.1f} 天)")
                
                # 如果缓存无效，下载新版本
                if not cache_valid:
                    log_print(f"   → 下载: {file_info['path']}")
                    success = self.download_file_from_github(
                        web_config['owner'],
                        web_config['repo'],
                        file_info['path'],
                        local_path
                    )
                    
                    if not success:
                        log_print(f"   ⚠ 下载失败，尝试使用本地文件: {file_info['path']}")
                        # 如果下载失败且本地也没有，从web目录复制
                        if not os.path.exists(local_path):
                            local_web_file = os.path.join('web', file_info['local'])
                            if os.path.exists(local_web_file):
                                shutil.copy2(local_web_file, local_path)
                                log_print(f"   ✓ 已从本地复制: {file_info['local']}")
                    else:
                        log_print(f"   ✓ 下载成功: {file_info['local']}")
            
            log_print("前端文件准备完成")
            return True
            
        except Exception as e:
            log_print(f"下载前端文件失败: {str(e)}")
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

    def check_for_updates(self):
        """手动检查更新 - 清除所有缓存的工具文件"""
        try:
            log_print("")
            log_print("============================================================")
            log_print("🔄 开始检查更新...")
            log_print("============================================================")
            
            # 清除工具文件缓存
            tools_cleared = 0
            if os.path.exists(self.cache_dir):
                for file in os.listdir(self.cache_dir):
                    if file.endswith('.py'):
                        file_path = os.path.join(self.cache_dir, file)
                        try:
                            os.remove(file_path)
                            log_print(f"   ✓ 已清除: {file}")
                            tools_cleared += 1
                        except Exception as e:
                            log_print(f"   ✗ 清除失败: {file} - {str(e)}")
            
            # 清除前端文件缓存
            web_cleared = 0
            if os.path.exists(self.web_cache_dir):
                for file in os.listdir(self.web_cache_dir):
                    file_path = os.path.join(self.web_cache_dir, file)
                    try:
                        os.remove(file_path)
                        log_print(f"   ✓ 已清除: web/{file}")
                        web_cleared += 1
                    except Exception as e:
                        log_print(f"   ✗ 清除失败: web/{file} - {str(e)}")
            
            log_print("")
            log_print(f"✅ 更新检查完成！")
            log_print(f"   清除了 {tools_cleared} 个工具文件")
            log_print(f"   清除了 {web_cleared} 个前端文件")
            log_print(f"   下次启动工具时将自动下载最新版本")
            log_print("============================================================")
            log_print("")
            
            return {
                "success": True,
                "message": f"已清除 {tools_cleared} 个工具缓存，下次启动将自动更新",
                "tools_cleared": tools_cleared,
                "web_cleared": web_cleared
            }
            
        except Exception as e:
            error_msg = f"检查更新失败: {str(e)}"
            log_print(f"✗ {error_msg}")
            return {
                "success": False,
                "message": error_msg
            }

    def check_and_install_dependencies(self, tool_id):
        """检查并安装依赖"""
        repo_config = self._internal_config['repositories'].get(tool_id)
        if not repo_config or not repo_config.get('dependencies'):
            log_print("   → 无需依赖")
            return True
        
        log_print(f"   → 检查依赖: {', '.join(repo_config['dependencies'])}")
        python_cmd = self.get_python_interpreter()
        
        for i, package in enumerate(repo_config['dependencies']):
            try:
                percent = (i / len(repo_config['dependencies'])) * 30
                eel.updateProgress(percent, f"检查依赖: {package}")
            except:
                pass
            
            try:
                result = subprocess.run(
                    [python_cmd, '-m', 'pip', 'show', package],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=30,
                    creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == 'Windows' else 0
                )
                
                if result.returncode != 0:
                    log_print(f"      → 安装依赖: {package}")
                    try:
                        eel.updateProgress(percent, f"安装依赖: {package}")
                    except:
                        pass
                    
                    # 使用清华镜像源加速下载，延长超时时间（opencv-python 较大）
                    install_result = subprocess.run(
                        [python_cmd, '-m', 'pip', 'install', package, 
                         '-i', 'https://pypi.tuna.tsinghua.edu.cn/simple',
                         '--trusted-host', 'pypi.tuna.tsinghua.edu.cn'],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        timeout=600,  # 增加到 10 分钟
                        creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == 'Windows' else 0
                    )
                    
                    if install_result.returncode != 0:
                        error_msg = f"依赖安装失败: {package}"
                        log_print(f"      ✗ {error_msg}")
                        if install_result.stderr:
                            log_print(f"         错误: {install_result.stderr.decode('utf-8', errors='ignore')}")
                        try:
                            eel.updateProgress(0, error_msg)
                        except:
                            pass
                        return False
                    else:
                        log_print(f"      ✓ 安装成功: {package}")
                else:
                    log_print(f"      ✓ 已安装: {package}")
            except Exception as e:
                log_print(f"      ✗ 检查依赖失败: {package} - {str(e)}")
                return False
        
        log_print("   ✓ 依赖检查完成")
        try:
            eel.updateProgress(30, "依赖检查完成")
        except:
            pass
        
        return True

    def get_tools_list(self):
        """获取工具列表"""
        return self.tools

    def launch_tool(self, tool_id):
        """启动工具"""
        try:
            # 检查并安装依赖
            if not self.check_and_install_dependencies(tool_id):
                return {"success": False, "message": "依赖安装失败"}
            
            try:
                eel.updateProgress(40, "准备工具文件...")
            except:
                pass
            
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
                if cache_valid:
                    days_old = file_age / (24 * 60 * 60)
                    log_print(f"   ✓ 使用缓存: {repo_config['local_name']} (已缓存 {days_old:.1f} 天)")
            
            # 如果缓存无效，下载新版本
            if not cache_valid:
                log_print(f"   → 下载工具: {repo_config['local_name']}")
                try:
                    eel.updateProgress(50, "正在下载工具...")
                except:
                    pass
                success = self.download_file_from_github(
                    repo_config['owner'],
                    repo_config['repo'],
                    repo_config['file_path'],
                    local_file
                )
                
                if not success:
                    return {"success": False, "message": "工具下载失败"}
            
            try:
                eel.updateProgress(90, "启动工具...")
            except:
                pass
            
            # 启动工具（在新进程中）
            # 设置环境变量标记，防止子进程重新初始化 Eel
            env = os.environ.copy()
            env['_TOOL_LAUNCHER_SUBPROCESS'] = '1'
            
            # 使用 pythonw.exe 启动GUI工具，不显示控制台窗口
            python_cmd = self.get_pythonw_interpreter()
            log_print(f"   → 使用解释器: {python_cmd}")
            
            process = subprocess.Popen(
                [python_cmd, local_file],
                env=env
            )
            
            self.tool_processes[tool_id] = process
            
            log_print(f"   ✓ 工具已启动: {self.tools[tool_id]['name']}")
            
            try:
                eel.updateProgress(100, "启动成功")
            except:
                pass
            
            return {"success": True, "message": f"{self.tools[tool_id]['name']} 已启动"}
            
        except Exception as e:
            error_msg = f"启动失败: {str(e)}"
            log_print(f"   ✗ {error_msg}")
            import traceback
            log_print(traceback.format_exc())
            return {"success": False, "message": error_msg}

    def check_and_update_all(self):
        """检查并更新所有工具和前端界面"""
        try:
            # 1. 更新前端文件
            try:
                eel.updateProgress(10, "正在更新前端界面...")
            except:
                pass  # Eel 未初始化时忽略
            
            web_config = self._internal_config.get('web_interface')
            if web_config:
                for file_info in web_config['files']:
                    local_path = os.path.join(self.web_cache_dir, file_info['local'])
                    success = self.download_file_from_github(
                        web_config['owner'],
                        web_config['repo'],
                        file_info['path'],
                        local_path
                    )
                    if not success:
                        log_print(f"警告: 更新前端文件 {file_info['path']} 失败")
            
            # 2. 更新工具文件
            total_tools = len(self._internal_config['repositories'])
            
            for i, (tool_id, repo_config) in enumerate(self._internal_config['repositories'].items()):
                percent = 20 + (i / total_tools) * 80  # 20-100%
                try:
                    eel.updateProgress(percent, f"更新 {self.tools[tool_id]['name']}...")
                except:
                    pass  # Eel 未初始化时忽略
                
                local_file = os.path.join(self.cache_dir, repo_config['local_name'])
                
                success = self.download_file_from_github(
                    repo_config['owner'],
                    repo_config['repo'],
                    repo_config['file_path'],
                    local_file
                )
                
                if not success:
                    return {"success": False, "message": f"更新 {self.tools[tool_id]['name']} 失败"}
            
            try:
                eel.updateProgress(100, "更新完成")
            except:
                pass  # Eel 未初始化时忽略
            
            return {"success": True, "message": "所有工具和界面已更新到最新版本"}
            
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
def check_for_updates():
    """检查更新 - 清除缓存的工具文件"""
    return launcher.check_for_updates()


@eel.expose
def check_and_update_all():
    """检查并更新所有工具"""
    return launcher.check_and_update_all()


def main():
    """主函数"""
    global launcher
    
    # Windows 多进程支持
    multiprocessing.freeze_support()
    
    # 检查是否为子进程（防止启动工具时重复初始化主应用）
    if os.environ.get('_TOOL_LAUNCHER_SUBPROCESS') == '1':
        # 这是子进程，直接退出，不启动 Eel
        return
    
    try:
        log_print("="*60)
        log_print("生产力工具整合 - 正在初始化...")
        log_print("="*60)
        
        # 创建启动器实例
        launcher = EelToolLauncher()
        log_print("✓ 启动器实例创建成功")
        
        # 下载最新的前端界面文件（静默下载，不触发Eel调用）
        log_print("正在检查前端文件更新...")
        launcher.download_web_interface()
        log_print("✓ 前端文件准备完成")
        
        # 初始化Eel，使用缓存的web目录
        web_dir = None
        if os.path.exists(launcher.web_cache_dir) and os.listdir(launcher.web_cache_dir):
            web_dir = launcher.web_cache_dir
            log_print(f"✓ 使用缓存的前端文件: {web_dir}")
        else:
            # 如果缓存不存在，使用本地web目录
            web_dir = 'web'
            log_print("✓ 使用本地前端文件")
        
        eel.init(web_dir)
        
        log_print("="*60)
        log_print("🚀 正在启动应用...")
        log_print("="*60)
        
        # 启动应用
        eel.start('index.html', 
                  size=(1280, 720), 
                  port=0,
                  close_callback=lambda page, sockets: log_print("应用已关闭"))
                  
    except Exception as e:
        log_print(f"❌ 启动失败: {str(e)}")
        import traceback
        error_details = traceback.format_exc()
        log_print(error_details)
        
        # 如果是打包模式，显示错误对话框
        if getattr(sys, 'frozen', False):
            try:
                import tkinter as tk
                from tkinter import messagebox
                root = tk.Tk()
                root.withdraw()
                error_msg = f"应用启动失败:\n\n{str(e)}\n\n请查看日志文件获取详细信息:\n{os.path.join(os.getenv('LOCALAPPDATA'), 'Temp', 'ProductivityTools', 'app.log')}"
                messagebox.showerror("启动失败", error_msg)
                root.destroy()
            except:
                pass
        raise


if __name__ == '__main__':
    main()
