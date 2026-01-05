// 设备授权配置
// 管理员：添加授权设备ID到下面的数组中，然后推送到GitHub
// 用户运行程序时会自动从GitHub下载最新的授权配置

const AUTHORIZED_DEVICES = [
    // 在这里添加授权的设备GUID
    // 格式：完整的设备GUID（从Windows"此电脑-属性"获取，或运行程序显示）
    // 不区分大小写
    
    "3dc6a97e-2166-48b5-ab74-92bbc1674ec5",  // 当前设备
    "29AC32F9-0DD1-4C04-8F37-BAD0892D1E84",  // 李奥
    "FB5668CA-B429-4A4F-8CC6-83C6ADEECEAF",  // 靓仔
    
];

// 导出配置（供Python后端使用）
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { AUTHORIZED_DEVICES };
}
