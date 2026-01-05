# 🚀 生产力工具整合平台

一个基于 Eel 框架的现代化桌面应用，集成多个生产力工具，支持自动更新和设备授权管理。

## ✨ 功能特性

### 核心功能
- 🎬 **字幕合并工具** - 专业的字幕文件合并处理
- 🎥 **视频模糊工具** - 高效的视频打码模糊处理
- 📁 **文件整理工具** - 智能文件分类整理

### 技术亮点
- ✅ **现代化界面** - 基于 HTML/CSS/JS 的精美 UI
- ✅ **桌面应用** - Eel 框架提供原生桌面体验
- ✅ **自动更新** - 工具和界面自动从 GitHub 更新
- ✅ **设备授权** - 基于硬件 GUID 的设备绑定
- ✅ **智能缓存** - 7 天缓存机制，减少网络请求
- ✅ **隐藏存储** - 工具文件加密存储在隐藏目录

## 📦 安装

### 环境要求
- Python 3.13+
- Windows 操作系统

### 依赖安装
```powershell
pip install -r requirements.txt
```

## 🚀 使用方法

### 启动应用
```powershell
python app.py
```

### 首次运行
1. 应用会显示当前设备的 GUID
2. 联系管理员将 GUID 添加到授权列表
3. 重启应用即可正常使用

### 使用工具
1. 启动应用后会显示工具卡片界面
2. 点击工具卡片上的"🚀 启动工具"按钮
3. 工具会自动下载（如需要）并启动

### 手动更新
点击界面底部的"🔄 检查更新"按钮，会：
- 更新所有工具到最新版本
- 更新前端界面文件
- 更新授权配置

## 🔐 设备授权管理

### 添加授权设备

#### 1. 获取设备 GUID
运行应用，未授权设备会显示：
```
💻 当前设备GUID: 3dc6a97e-2166-48b5-ab74-92bbc1674ec5
```

#### 2. 添加到配置文件
编辑 `web/config.js`：
```javascript
const AUTHORIZED_DEVICES = [
    "3dc6a97e-2166-48b5-ab74-92bbc1674ec5",  // 设备A
    "29AC32F9-0DD1-4C04-8F37-BAD0892D1E84",  // 设备B
];
```

#### 3. 推送到 GitHub
```powershell
git add web/config.js
git commit -m "添加新授权设备"
git push
```

#### 4. 用户重启应用
授权配置会在下次启动时自动下载，最多 7 天内生效。

### 授权机制
- 基于 Windows 注册表中的 `MachineGuid`（最稳定）
- 不区分大小写
- 列表为空时允许所有设备（开发模式）
- 验证失败立即退出程序

## 🏗️ 技术架构

### 框架
- **后端**: Python + Eel
- **前端**: HTML5 + CSS3 + JavaScript
- **UI渲染**: Chromium (Eel 内置)

### 目录结构
```
.
├── app.py                    # 主程序（Eel 后端）
├── requirements.txt          # Python 依赖
├── web/                      # 前端资源目录
│   ├── index.html           # 主界面
│   ├── style.css            # 样式文件
│   ├── script.js            # 前端逻辑
│   └── config.js            # 授权配置
└── README.md                # 本文档
```

### 缓存机制

#### 缓存位置
- **Windows**: `%LOCALAPPDATA%\Temp\.{机器ID}_{周标识}_{随机码}\`
- **特性**: 隐藏目录、按周清理

#### 缓存结构
```
.a1b2c3d4_2026-W01_9f3e2a1b/    # 隐藏缓存根目录
├── web/                         # 前端文件缓存
│   ├── index.html
│   ├── style.css
│   ├── script.js
│   └── config.js               # 授权配置
├── 专业字幕合并工具.py          # 工具文件缓存
├── 打码工具.py
└── 文件整理工具.py
```

#### 缓存时间
- **工具文件**: 7 天
- **前端文件**: 7 天
- **授权配置**: 7 天

## 🔄 自动更新机制

### GitHub 仓库配置
所有文件都从 GitHub 仓库动态下载：

```python
# 工具仓库
"subtitle_merger": {
    "owner": "jwwl520",
    "repo": "Subtitle-merging",
    "file_path": "专业字幕合并工具.py"
}

# 前端仓库
'web_interface': {
    "owner": "jwwl520",
    "repo": "Productivity-tool-integration",
    "files": ["web/index.html", "web/style.css", "web/script.js", "web/config.js"]
}
```

### 更新流程
1. **启动检查**: 检查缓存文件是否过期（7天）
2. **自动下载**: 过期文件从 GitHub 下载最新版
3. **手动更新**: 点击按钮强制更新所有文件

## 📝 开发指南

### 添加新工具
编辑 `app.py`：

```python
# 1. 添加仓库配置
'repositories': {
    "new_tool": {
        "owner": "your_github",
        "repo": "tool_repo",
        "file_path": "tool.py",
        "local_name": "工具.py",
        "dependencies": ["package1", "package2"]
    }
}

# 2. 添加工具信息
self.tools = {
    "new_tool": {
        "name": "新工具",
        "description": "工具描述",
        "icon": "🔧"
    }
}
```

### 修改前端界面
1. 编辑 `web/` 目录下的文件
2. 推送到 GitHub
3. 用户点击"检查更新"或等待缓存过期

## ⚠️ 注意事项

### 安全
- ✅ 设备授权基于硬件 GUID，重装系统后可能改变
- ✅ 工具文件存储在隐藏目录，普通用户不易发现
- ✅ 按周自动清理旧缓存，节省磁盘空间
- ❌ 不要在公共仓库中硬编码敏感信息

### 网络
- 需要联网下载工具和更新
- 使用 GitHub API，无需 token（公开仓库）
- 下载失败时会使用本地缓存

### 兼容性
- 目前仅支持 Windows 系统
- 需要管理员权限读取注册表（获取 MachineGuid）
- Python 3.13 测试通过

## 🛠️ 故障排除

### 设备未授权
**问题**: 启动时提示"设备未授权"

**解决**:
1. 查看显示的设备 GUID
2. 添加到 `web/config.js`
3. 推送到 GitHub
4. 重启应用

### 下载失败
**问题**: 工具或界面下载失败

**解决**:
1. 检查网络连接
2. 确认 GitHub 仓库可访问
3. 点击"检查更新"重试
4. 查看控制台错误信息

### 工具无法启动
**问题**: 点击启动后工具没有反应

**解决**:
1. 检查依赖是否安装成功
2. 查看进度提示信息
3. 手动运行工具文件测试
4. 检查 Python 版本兼容性

## 📄 许可证

本项目仅供学习交流使用。

## 👥 贡献

欢迎提交 Issue 和 Pull Request！

## 📧 联系方式

如需授权或技术支持，请联系项目管理员。

---

**最后更新**: 2026年1月5日
