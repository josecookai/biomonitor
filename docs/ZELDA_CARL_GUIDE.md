# 🏃 Biomonitor 使用指南 - Zelda & Carl 专用版

针对两位不同设备用户的使用教程。

---

## 👩 Zelda - 小米手环 + Codex 流程

### 你的设备
- **小米手环** (Mi Band / 小米运动健康)
- **同步方式**: Gadgetbridge App 或 小米运动健康导出

### 快速配置

#### 方法 1: Gadgetbridge 实时同步 (推荐)

**Step 1: 安装 Gadgetbridge**
- Android: [F-Droid下载](https://f-droid.org/packages/nodomain.freeyourgadget.gadgetbridge/)
- 配对小米手环

**Step 2: 配置 HTTP 推送**
```
Gadgetbridge → 设置 → HTTP 服务器 → 启用
URL: https://biomonitor-api-production.up.railway.app/api/xiaomi/webhook
```

**Step 3: 验证同步**
```bash
# 查看最新数据
curl https://biomonitor-api-production.up.railway.app/api/xiaomi/stats?days=7
```

#### 方法 2: 手动导出同步

**Step 1: 导出数据**
```
小米运动健康 App → 我的 → 设置 → 导出数据
格式: JSON 或 CSV
```

**Step 2: 使用 Codex 脚本处理**

创建一个数据处理脚本：

```bash
# 创建项目目录
mkdir ~/zelda-biomonitor && cd ~/zelda-biomonitor
git init

# 使用 Codex 生成同步脚本
bash pty:true command:"codex exec --full-auto 'Create a Python script that reads Xiaomi Mi Band exported JSON/CSV data and POSTs it to https://biomonitor-api-production.up.railway.app/api/xiaomi/upload'"
```

**Step 3: 运行同步**
```bash
python3 sync_xiaomi.py --file ~/Downloads/mi_band_export.json
```

### 查看数据

```bash
# 使用 Codex 查询 API
bash pty:true command:"codex exec 'Fetch https://biomonitor-api-production.up.railway.app/api/xiaomi/stats?days=7 and display step count, heart rate, and sleep analysis in a formatted table'"
```

---

## 👨 Carl - Oura Ring + OpenClaw (Claude/Codex) 流程

### 你的设备
- **Oura Ring Gen 3**
- **同步方式**: Oura API v2

### 快速配置

#### Step 1: 获取 Oura API Token

```bash
# 使用 Codex 帮你完成 OAuth 流程
bash pty:true command:"codex exec 'Create a Python script that guides user through Oura OAuth2 flow: 
1. Open browser to https://cloud.ouraring.com/oauth/authorize?client_id=... 
2. Start local callback server on port 8080
3. Exchange code for access token
4. Save token to oura_token.json'"
```

或者直接手动：
1. 访问 https://cloud.ouraring.com/oauth/applications
2. 创建 Application
3. 复制 Client ID 和 Secret

#### Step 2: 配置 Biomonitor

**Railway 环境变量配置:**
```
OURA_CLIENT_ID=your_client_id
OURA_CLIENT_SECRET=your_client_secret
OURA_ACCESS_TOKEN=your_token
```

#### Step 3: 同步数据

**API 触发同步:**
```bash
# 同步最近 7 天
curl -X POST "https://biomonitor-api-production.up.railway.app/api/oura/sync?days=7"

# 查看就绪度分数
curl "https://biomonitor-api-production.up.railway.app/api/oura/readiness?days=7"

# 查看睡眠数据
curl "https://biomonitor-api-production.up.railway.app/api/oura/sleep?days=7"
```

**使用 OpenClaw (Claude Code) 分析:**

```bash
# 启动 Claude Code 分析 Oura 数据
bash pty:true workdir:~/carl-biomonitor command:"claude 'Fetch Oura readiness and sleep data from Biomonitor API for the last 30 days, identify trends, and suggest recovery optimizations based on HRV patterns'"
```

---

## 🎯 两人共用的 Coding Agent 工作流

### 场景 1: 生成周报告

```bash
# Zelda 的小米数据 + Carl 的 Oura 数据 合并分析
bash pty:true command:"codex exec 'Write a Python script that:
1. Fetches /api/xiaomi/stats for Zelda (steps, sleep, HR)
2. Fetches /api/oura/readiness for Carl (readiness, HRV, sleep score)
3. Generates a comparative weekly report
4. Outputs markdown with insights'"
```

### 场景 2: 设置自动同步 Cron

```bash
# 使用 Codex 创建定时任务
bash pty:true command:"codex exec 'Create a shell script that:
1. Calls Biomonitor sync APIs every morning at 8 AM
2. Sends Telegram notification if sync fails
3. Logs to ~/biomonitor-sync.log
4. Set up cron job automatically'"
```

### 场景 3: 异常检测

```bash
# 检测数据异常
bash pty:true command:"claude 'Write a Python script that monitors Biomonitor API:
- Check if Carl HRV drops below 40ms (alert overtraining)
- Check if Zelda steps < 5000/day (alert sedentary)
- Send Telegram alerts via Bot API
- Run every 6 hours via cron'"
```

---

## 📱 Telegram Bot 快捷指令

添加到你的 Bot：

```
/status - 查看 Biomonitor 状态
/sync - 手动触发同步
/stats - 获取今日统计
/weekly - 生成周报告
/compare - Zelda vs Carl 对比
```

**使用 Codex 生成 Bot:**

```bash
bash pty:true command:"codex exec --full-auto 'Create a Telegram bot webhook handler that:
1. Listens for /status, /sync, /stats commands
2. Queries Biomonitor API
3. Returns formatted responses
4. Deploy to Railway'"
```

---

## 🔧 故障排查

### 小米手环同步失败
```bash
# 检查 Gadgetbridge 日志
adb logcat | grep Gadgetbridge

# 验证 webhook 可达性
curl -X POST https://biomonitor-api-production.up.railway.app/api/xiaomi/webhook \
  -H "Content-Type: application/json" \
  -d '{"heart_rate": 75, "steps": 1000}'
```

### Oura Token 过期
```bash
# 刷新 Token
curl -X POST "https://biomonitor-api-production.up.railway.app/api/oura/refresh"

# 或使用 Codex 自动刷新
bash pty:true command:"codex exec 'Create Python script to refresh Oura token using refresh_token and update Railway env vars via Railway CLI'"
```

---

## 📚 快速参考

| 任务 | Zelda (小米) | Carl (Oura) |
|-----|-------------|-------------|
| 查看数据 | `/api/xiaomi/stats` | `/api/oura/readiness` |
| 同步触发 | Gadgetbridge HTTP | `/api/oura/sync` |
| 睡眠数据 | 自动同步 | `/api/oura/sleep` |
| 心率数据 | 实时 webhook | API 查询 |

---

**需要帮助？**
- Biomonitor Web: https://biomonitor-web-production.up.railway.app
- API Docs: https://biomonitor-api-production.up.railway.app/docs
- GitHub: https://github.com/josecookai/biomonitor