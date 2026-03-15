# 🍎 Apple Watch Data Integration

BioMonitor 支持从 Apple Watch 获取以下健康数据格式：

## 📊 支持的数据类型

### 1. 基础活动数据 (Activity)
```json
{
  "activity_type": "walking|running|cycling|crossfit|strength_training",
  "start_date": "2026-03-15T08:00:00Z",
  "end_date": "2026-03-15T09:00:00Z",
  "duration": 3600,
  "distance": 5000,
  "distance_unit": "m",
  "calories": 450,
  "elevation_gain": 120
}
```

### 2. 心率数据 (Heart Rate)
```json
{
  "timestamp": "2026-03-15T08:30:00Z",
  "heart_rate": 145,
  "heart_rate_variability": 65,
  "resting_heart_rate": 58,
  "walking_heart_rate_average": 105
}
```

### 3. 睡眠数据 (Sleep)
```json
{
  "date": "2026-03-15",
  "sleep_start": "2026-03-15T23:00:00Z",
  "sleep_end": "2026-03-16T06:30:00Z",
  "total_sleep": 27000,
  "deep_sleep": 7200,
  "rem_sleep": 5400,
  "light_sleep": 14400,
  "awake_time": 600,
  "sleep_efficiency": 92
}
```

### 4. 恢复数据 (Recovery)
```json
{
  "date": "2026-03-15",
  "hrv": 65,
  "resting_hr": 58,
  "respiratory_rate": 14,
  "wrist_temperature": 35.8,
  "blood_oxygen": 98,
  "training_readiness": 85
}
```

### 5. 体能训练详细数据 (Workout Details)
```json
{
  "workout_type": "crossfit",
  "start_time": "2026-03-15T08:00:00Z",
  "duration": 3600,
  "active_energy": 450,
  "average_heart_rate": 145,
  "max_heart_rate": 185,
  "heart_rate_zones": {
    "zone1": 300,
    "zone2": 600,
    "zone3": 1200,
    "zone4": 900,
    "zone5": 600
  },
  "calories": 450,
  "distance": null,
  "elevation": 0,
  "lap_times": [180, 240, 300],
  "route": null
}
```

## 🔌 接入方式

### 方式 1: Health Auto Export App (推荐)
1. 安装 [Health Auto Export](https://apps.apple.com/app/health-auto-export/id1115567069)
2. 配置 Webhook URL: `http://your-server:8000/api/apple-health/webhook`
3. 选择要同步的数据类型
4. 设置自动推送频率

### 方式 2: HealthKit API (开发中)
原生 iOS App 直接读取 HealthKit 数据并推送到 BioMonitor。

### 方式 3: 手动导出
从 Apple Health App 导出 XML/JSON 文件，上传到 BioMonitor。

## 📈 Dashboard 展示

| 数据类型 | 展示方式 | 位置 |
|----------|----------|------|
| 活动数据 | 图表 + 列表 | 首页 / Activity |
| 心率数据 | 趋势图 + 当前值 | Recovery 页面 |
| 睡眠数据 | 睡眠阶段图 | Recovery 页面 |
| HRV | 趋势图 + 恢复建议 | Recovery 页面 |
| 训练负荷 | 累积图表 | 首页 |

## 🔄 数据同步频率

- **实时**: 通过 Webhook 即时接收
- **每小时**: 批量同步更新
- **每日**: 完整数据报告生成

## 📝 注意事项

1. 首次使用需要在 iPhone 上授权 Health 数据访问
2. 心率变异性 (HRV) 需要 Apple Watch Series 3 或更新
3. 睡眠数据需要佩戴 Apple Watch 睡觉
4. 血氧数据仅限 Apple Watch Series 6 及更新
