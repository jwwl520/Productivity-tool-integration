// 工具数据（将从 Python 后端加载）
let tools = {};

// 页面加载完成后初始化
window.addEventListener('DOMContentLoaded', async () => {
    await loadTools();
    renderTools();
});

// 从后端加载工具列表
async function loadTools() {
    try {
        tools = await eel.get_tools_list()();
        console.log('工具列表加载成功:', tools);
    } catch (error) {
        console.error('加载工具列表失败:', error);
        showMessage('错误', '无法加载工具列表');
    }
}

// 渲染工具卡片
function renderTools() {
    const grid = document.getElementById('toolsGrid');
    grid.innerHTML = '';
    
    for (const [toolId, toolInfo] of Object.entries(tools)) {
        const card = createToolCard(toolId, toolInfo);
        grid.appendChild(card);
    }
}

// 创建工具卡片元素
function createToolCard(toolId, toolInfo) {
    const card = document.createElement('div');
    card.className = 'tool-card';
    card.style.animationDelay = `${Object.keys(tools).indexOf(toolId) * 0.1}s`;
    
    card.innerHTML = `
        <span class="tool-icon">${toolInfo.icon}</span>
        <h2 class="tool-name">${toolInfo.name}</h2>
        <p class="tool-description">${toolInfo.description}</p>
        <button class="launch-btn" onclick="launchTool('${toolId}')">
            <span>🚀</span>
            <span>启动工具</span>
        </button>
    `;
    
    return card;
}

// 启动工具
async function launchTool(toolId) {
    console.log('启动工具:', toolId);
    
    // 显示进度模态框
    showProgressModal('正在准备工具...');
    
    try {
        // 调用后端启动工具
        const result = await eel.launch_tool(toolId)();
        
        if (result.success) {
            closeProgressModal();
            showMessage('成功', `${tools[toolId].name} 已启动`);
        } else {
            closeProgressModal();
            showMessage('错误', result.message || '启动失败');
        }
    } catch (error) {
        console.error('启动工具失败:', error);
        closeProgressModal();
        showMessage('错误', '启动工具时发生错误');
    }
}

// 检查更新
async function checkUpdates() {
    showProgressModal('正在检查更新...');
    
    try {
        const result = await eel.check_and_update_all()();
        
        closeProgressModal();
        
        if (result.success) {
            showMessage('更新完成', result.message || '所有工具已更新到最新版本');
        } else {
            showMessage('更新失败', result.message || '检查更新时发生错误');
        }
    } catch (error) {
        console.error('检查更新失败:', error);
        closeProgressModal();
        showMessage('错误', '检查更新时发生错误');
    }
}

// 更新进度回调
function updateProgress(percent, status) {
    const progressBar = document.getElementById('progressBar');
    const progressText = document.getElementById('progressText');
    const progressStatus = document.getElementById('progressStatus');
    
    if (progressBar) {
        progressBar.style.width = `${percent}%`;
    }
    
    if (progressText) {
        progressText.textContent = `${Math.round(percent)}%`;
    }
    
    if (progressStatus && status) {
        progressStatus.textContent = status;
    }
}

// 显示进度模态框
function showProgressModal(title) {
    const modal = document.getElementById('progressModal');
    const titleElement = document.getElementById('progressTitle');
    
    if (titleElement) {
        titleElement.textContent = title;
    }
    
    // 重置进度
    updateProgress(0, '准备中...');
    
    modal.style.display = 'flex';
}

// 关闭进度模态框
function closeProgressModal() {
    const modal = document.getElementById('progressModal');
    modal.style.display = 'none';
}

// 显示消息模态框
function showMessage(title, message) {
    const modal = document.getElementById('messageModal');
    const titleElement = document.getElementById('messageTitle');
    const messageElement = document.getElementById('messageText');
    
    if (titleElement) {
        titleElement.textContent = title;
    }
    
    if (messageElement) {
        messageElement.textContent = message;
    }
    
    modal.style.display = 'flex';
}

// 关闭消息模态框
function closeMessageModal() {
    const modal = document.getElementById('messageModal');
    modal.style.display = 'none';
}

// Eel 暴露的函数供 Python 调用
eel.expose(updateProgress);

// 键盘快捷键
document.addEventListener('keydown', (e) => {
    // ESC 关闭模态框
    if (e.key === 'Escape') {
        closeProgressModal();
        closeMessageModal();
    }
    
    // Ctrl/Cmd + R 刷新
    if ((e.ctrlKey || e.metaKey) && e.key === 'r') {
        e.preventDefault();
        location.reload();
    }
});
