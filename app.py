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
    
    # 禁用 print 输出（避免弹出命令行窗口）
    sys.stdout = open(os.devnull, 'w')
    sys.stderr = open(os.devnull, 'w')
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
            self._python_interpreter = sys.executable
        else:
            self._python_interpreter = sys.executable
        
        return self._python_interpreter

    def download_file_from_github(self, owner, repo, file_path, local_path, progress_callback=None):
        """从GitHub下载文件（使用raw.githubusercontent.com，无速率限制）"""
        try:
            # 确保父目录存在
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            
            # 使用 raw.githubusercontent.com 直接下载（避免API速率限制）
            raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/main/{file_path}"
            
            headers = {
                'User-Agent': 'Python-Tool-Launcher'
            }
            
            log_print(f"   → 下载: {file_path}")
            
            response = requests.get(raw_url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                file_content = response.content
                
                with open(local_path, 'wb') as f:
                    f.write(file_content)
                
                log_print(f"   ✓ 成功: {os.path.basename(local_path)} ({len(file_content)} bytes)")
                
                if progress_callback:
                    try:
                        progress_callback(100, f"文件下载完成")
                    except:
                        pass  # 忽略回调错误（可能Eel未初始化）
                
                return True
            else:
                error_msg = f"HTTP {response.status_code}"
                log_print(f"   ✗ 失败: {error_msg}")
                if progress_callback:
                    try:
                        progress_callback(0, f"下载失败: {error_msg}")
                    except:
                        pass
                return False
                
        except Exception as e:
            log_print(f"   ✗ 异常: {str(e)}")
            if progress_callback:
                try:
                    progress_callback(0, f"下载异常: {str(e)}")
                except:
                    pass
            return False

    def download_web_interface(self):
        """从GitHub下载前端界面文件"""
        try:
            web_config = self._internal_config.get('web_interface')
            if not web_config:
                return True  # 如果没有配置，使用本地文件
            
            log_print("正在检查前端文件更新...")
            
            for file_info in web_config['files']:
                local_path = os.path.join(self.web_cache_dir, file_info['local'])
                
                # 检查缓存是否有效
                cache_valid = False
                if os.path.exists(local_path):
                    file_age = time.time() - os.path.getmtime(local_path)
                    cache_valid = file_age < self.web_cache_duration
                
                # 如果缓存无效，下载新版本
                if not cache_valid:
                    log_print(f"下载: {file_info['path']}")
                    success = self.download_file_from_github(
                        web_config['owner'],
                        web_config['repo'],
                        file_info['path'],
                        local_path
                    )
                    
                    if not success:
                        log_print(f"警告: 无法下载 {file_info['path']}, 将使用本地文件")
                        # 如果下载失败且本地也没有，从web目录复制
                        if not os.path.exists(local_path):
                            local_web_file = os.path.join('web', file_info['local'])
                            if os.path.exists(local_web_file):
                                shutil.copy2(local_web_file, local_path)
                else:
                    log_print(f"使用缓存: {file_info['path']}")
            
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
def check_and_update_all():
    """检查并更新所有工具"""
    return launcher.check_and_update_all()


def main():
    """主函数"""
    global launcher
    
    # 创建启动器实例
    launcher = EelToolLauncher()
    
    # 下载最新的前端界面文件（静默下载，不触发Eel调用）
    log_print("\n" + "="*60)
    launcher.download_web_interface()
    log_print("="*60 + "\n")
    
    # 初始化Eel，使用缓存的web目录
    if os.path.exists(launcher.web_cache_dir) and os.listdir(launcher.web_cache_dir):
        eel.init(launcher.web_cache_dir)
        log_print(f"✓ 使用缓存的前端文件: {launcher.web_cache_dir}")
    else:
        # 如果缓存不存在，使用本地web目录
        eel.init('web')
        log_print("✓ 使用本地前端文件")
    
    log_print("\n🚀 正在启动应用...\n")
    
    # 启动应用
    try:
        eel.start('index.html', size=(1280, 720), port=0)
    except (SystemExit, MemoryError, KeyboardInterrupt):
        pass


if __name__ == '__main__':
    main()
