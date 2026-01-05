# 前端界面 GitHub 配置指南

## 🎯 目标
将前端界面文件（HTML/CSS/JS）托管到 GitHub，实现动态更新，无需重新打包应用程序。

## 📋 步骤

### 1. 创建 GitHub 仓库

1. 访问 https://github.com/new
2. 创建一个新的**公开仓库**，例如命名为 `Tool-Launcher-Web`
3. 不要初始化 README、.gitignore 或 license

### 2. 上传前端文件

在当前目录执行以下命令（替换 `你的用户名` 为你的 GitHub 用户名）：

```powershell
# 进入 web 目录
cd web

# 初始化 git 仓库
git init

# 添加所有文件
git add index.html style.css script.js

# 提交
git commit -m "Initial commit: 前端界面文件"

# 添加远程仓库（替换 jwwl520 为你的用户名）
git remote add origin https://github.com/jwwl520/Tool-Launcher-Web.git

# 推送到 GitHub
git push -u origin main

# 如果上面的命令失败，尝试：
git push -u origin master
```

### 3. 更新应用配置

打开 `app.py` 文件，找到第 26-35 行的 `web_interface` 配置：

```python
'web_interface': {
    "owner": "jwwl520",  # 改成你的GitHub用户名
    "repo": "Tool-Launcher-Web",  # 改成你的前端仓库名
    "files": [
        {"path": "index.html", "local": "index.html"},
        {"path": "style.css", "local": "style.css"},
        {"path": "script.js", "local": "script.js"}
    ]
}
```

修改 `owner` 为你的 GitHub 用户名。

### 4. 测试

重新运行应用，你会看到类似输出：

```
正在检查前端文件更新...
下载: index.html
下载: style.css
下载: script.js
前端文件准备完成
使用缓存的前端文件: C:\Users\...\Temp\.xxxxx\web
```

## 🔄 更新前端界面

当你需要更新前端界面时：

1. 修改 `web` 目录中的文件
2. 提交并推送到 GitHub：

```powershell
cd web
git add .
git commit -m "更新界面样式"
git push
```

3. 用户重新启动应用，会自动下载最新版本（每24小时检查一次）

## ⚙️ 配置说明

- **工具文件缓存**：7天
- **前端文件缓存**：24小时
- **缓存位置**：
  - Windows: `%LOCALAPPDATA%\Temp\.机器ID_周标识_随机码\`
  - Linux/Mac: `/tmp/.机器ID_周标识_随机码/`

## 🎨 前端文件结构

```
仓库根目录/
├── index.html    # 主界面
├── style.css     # 样式文件
└── script.js     # 脚本文件
```

## 🚀 优势

✅ **无需重新打包**：前端更新后，用户只需重启应用  
✅ **自动缓存**：减少网络请求，提升启动速度  
✅ **降级方案**：网络失败时使用本地 `web/` 目录文件  
✅ **版本控制**：使用 Git 管理前端文件历史

## 🔒 安全提示

- 建议使用**公开仓库**存储前端文件（无需 token）
- 不要在前端文件中硬编码敏感信息
- 前端文件会被缓存到用户本地，注意隐私保护
