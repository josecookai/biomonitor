# 🎯 BioMonitor Demo Guide

## 快速启动 (2分钟)

### 1. 启动后端 API
```bash
cd /path/to/biomonitor
pip install -r requirements.txt  # 如果还没安装 Python 依赖
python3 setup_demo.py
python3 api_server.py
```
API 将在 http://localhost:8000 运行

### 2. 启动前端 Dashboard
```bash
cd dashboard/web
npm install  # 如果还没安装
npm run dev
```
Dashboard 将在 http://localhost:3000 运行

## 📊 Demo 数据

已预置演示数据：
- **CrossFit**: 3 次 (Fran 4:52, Grace 3:15, Murph 42:30)
- **步行**: 7.5 km (3 次)
- **心率数据**: 平均 125 bpm

## 🎬 Demo 流程建议

1. **开场** - 展示 Dashboard 首页
   - 本周概览卡片
   - 活动图表
   - 最近活动列表

2. **CrossFit 详情** - 点击 "View Activity"
   - WOD 列表
   - 个人记录 (PR)
   - 时间趋势

3. **恢复数据** - 点击 Recovery 卡片
   - HRV 趋势
   - 静息心率
   - 睡眠数据

4. **分享功能** - 点击 Share 按钮
   - 生成分享卡片
   - 模拟截图导出

5. **技术亮点** (可选)
   - API 文档: http://localhost:8000/docs
   - Webhook 配置 (Apple Health Auto Export)
   - Strava API 集成

## 🚀 下一步

- 部署到服务器 (24/7 在线)
- Playwright 截图自动化
- Telegram Bot 推送
