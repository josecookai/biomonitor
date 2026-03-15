# 🔌 Strava API 接入 Railway 部署指南

## 🎯 目标
将 Strava 数据同步到 Railway 部署的 BioMonitor:
- Web: https://biomonitor-web-production.up.railway.app
- API: https://biomonitor-api-production.up.railway.app

---

## 方案一: 环境变量配置 (推荐)

### 1. 获取 Strava API 凭证

1. 访问 https://www.strava.com/settings/api
2. 创建应用:
   - Application Name: `BioMonitor`
   - Category: `Training`
   - Website: `https://biomonitor-web-production.up.railway.app`
   - Authorization Callback Domain: `biomonitor-web-production.up.railway.app`
3. 记下:
   - Client ID
   - Client Secret

### 2. 获取 Access Token

**方法 A - 使用 Strava 官方流程:**
访问: `https://www.strava.com/oauth/authorize?client_id=YOUR_CLIENT_ID&response_type=code&redirect_uri=http://localhost&approval_prompt=force&scope=read,activity:read`

**方法 B - 使用我提供的脚本:**
```bash
python3 get_strava_token.py
```

### 3. 配置 Railway 环境变量

在 Railway Dashboard 中设置以下环境变量:

```bash
STRAVA_CLIENT_ID=你的ClientID
STRAVA_CLIENT_SECRET=你的ClientSecret
STRAVA_ACCESS_TOKEN=你的AccessToken
STRAVA_REFRESH_TOKEN=你的RefreshToken
```

### 4. 重启 Railway 服务

环境变量设置后，Railway 会自动重启服务，Strava 数据就会开始同步。

---

## 方案二: 手动同步脚本

### 1. 安装依赖

```bash
pip install requests
```

### 2. 运行同步脚本

```bash
python3 sync_strava_to_railway.py
```

按提示输入:
- Strava Access Token
- Railway API Key (可选)
- 同步天数 (默认 30)

### 3. 查看结果

访问 https://biomonitor-web-production.up.railway.app 查看同步的数据

---

## 方案三: API 直接推送

如果你有 Strava 数据，可以直接调用 Railway API:

```bash
curl -X POST https://biomonitor-api-production.up.railway.app/api/activities/sync \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Morning Run",
    "type": "Run",
    "start_date": "2026-03-15T08:00:00Z",
    "distance": 5000,
    "moving_time": 1800,
    "average_heartrate": 145,
    "is_crossfit": false,
    "is_walking": false
  }'
```

---

## 📊 数据映射

| Strava 字段 | BioMonitor 字段 | 说明 |
|-------------|-----------------|------|
| `name` | `name` | 活动名称 |
| `type` | `type` | 活动类型 |
| `start_date` | `start_date` | 开始时间 |
| `distance` | `distance` | 距离(米) |
| `moving_time` | `moving_time` | 运动时长(秒) |
| `average_heartrate` | `average_heartrate` | 平均心率 |
| `max_heartrate` | `max_heartrate` | 最大心率 |
| `calories` | `calories` | 消耗卡路里 |

---

## 🔧 自动同步设置

### 使用 GitHub Actions (推荐)

创建 `.github/workflows/sync-strava.yml`:

```yaml
name: Sync Strava to Railway

on:
  schedule:
    - cron: '0 */6 * * *'  # 每6小时同步一次
  workflow_dispatch:

jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Install dependencies
        run: pip install requests
      
      - name: Sync Strava data
        run: python sync_strava_to_railway.py
        env:
          STRAVA_ACCESS_TOKEN: ${{ secrets.STRAVA_ACCESS_TOKEN }}
          RAILWAY_API_KEY: ${{ secrets.RAILWAY_API_KEY }}
```

然后在 GitHub Settings → Secrets 中添加:
- `STRAVA_ACCESS_TOKEN`
- `RAILWAY_API_KEY`

---

## ⚡ 快速测试

同步完成后，测试 API 是否正常工作:

```bash
# 检查健康状态
curl https://biomonitor-api-production.up.railway.app/api/health

# 获取活动列表
curl https://biomonitor-api-production.up.railway.app/api/activities

# 获取统计数据
curl https://biomonitor-api-production.up.railway.app/api/stats
```

---

## 🆘 故障排除

### Token 过期
Strava Access Token 每 6 小时过期，使用 Refresh Token 自动更新。

### CORS 错误
如果 Web 页面显示 CORS 错误，需要更新 Railway 的 CORS 配置:
```python
allow_origins=["https://biomonitor-web-production.up.railway.app"]
```

### 数据未显示
1. 检查 API 是否有数据: `/api/activities`
2. 检查 Dashboard 是否正确连接 API
3. 清除浏览器缓存

---

需要帮助？在 GitHub 提交 Issue 或联系开发团队。
