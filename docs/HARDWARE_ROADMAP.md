# 🔌 Wellness Hardware Integration Roadmap

BioMonitor 计划集成以下智能硬件和平台：

## ✅ 已支持

### Apple Watch
- **型号**: Series 3 及更新
- **数据**: 心率、HRV、睡眠、活动、血氧、体温
- **状态**: ✅ 已集成 (Health Auto Export)

### Strava
- **类型**: 运动社交平台
- **数据**: 活动记录、GPS轨迹、心率、功率
- **状态**: ✅ 已集成

---

## 🚧 开发中

### Garmin Connect
**支持设备系列**:
- Fenix 系列 (Fenix 7/8/Pro)
- Epix 系列 (Epix Gen 2)
- Forerunner 系列 (255/265/955/965)
- Venu 系列
- Instinct 系列

**数据字段**:
- 高级训练指标 (Training Readiness, Body Battery)
- 详细睡眠分析
- 跑步动态 (步频、触地时间、垂直振幅)
- 多频段 GPS 轨迹

**API**: Garmin Health API / Connect IQ

---

## 📋 计划中

### Xiaomi / 小米手环
**支持设备**:
- 小米手环 9 / 9 Pro
- 小米 Watch S3 / S4
- Redmi Watch 系列

**数据**:
- 基础活动追踪
- 心率监测
- 睡眠分析
- SpO2 血氧

**集成方式**: Zepp Life App → API / 数据导出

---

### Oura Ring
**数据亮点**:
- 睡眠评分 (Sleep Score)
- 准备度评分 (Readiness Score)
- 活动评分 (Activity Score)
- 体温趋势
- 恢复分析

**API**: Oura Cloud API v2

**状态**: 📝 规划中

---

### WHOOP 4.0
**数据亮点**:
- 应变评分 (Strain Score)
- 恢复评分 (Recovery Score)
- 睡眠表现 (Sleep Performance)
- 皮肤温度
- 血氧饱和度

**API**: WHOOP API v1

**状态**: 📝 规划中

---

### 🏆 Concept2 (PM5 面板) - Hyrox 杀手锏

**针对 Hyrox 比赛的专项支持**

**支持设备**:
- Concept2 RowErg (划船机)
- Concept2 SkiErg (滑雪机)
- Concept2 BikeErg (单车机)

**PM5 面板数据**:
```json
{
  "workout_type": "rowing|skiing|cycling",
  "date": "2026-03-15",
  "duration": 2400,
  "distance": 5000,
  "pace": "2:24.0",
  "spm": 28,
  "calories": 320,
  "watts": 185,
  "heart_rate": 165,
  "drag_factor": 115,
  "intervals": [
    {"time": 600, "distance": 1250, "pace": "2:24.0"}
  ]
}
```

**Hyrox 专项功能**:
- 🏃 比赛数据自动识别
- 📊 8x1km 跑步 + 8 工作站数据分段
- 🎯 配速策略分析
- 📈 历史成绩对比
- 🏅 全球排行榜对接

**集成方式**:
1. **ErgData App**: 自动同步到 BioMonitor
2. **PM5 USB/Bluetooth**: 直接读取
3. **Logbook API**: Concept2 官方 API

**状态**: 🏗️ 高优先级开发中

---

## 🔮 未来考虑

| 设备/平台 | 类型 | 优先级 | 预计时间 |
|-----------|------|--------|----------|
| Polar | 心率带/手表 | 中 | Q3 2026 |
| Suunto | 运动手表 | 中 | Q3 2026 |
| Fitbit | 健康手环 | 低 | Q4 2026 |
| Withings | 智能体重秤 | 低 | Q4 2026 |
| Wahoo | 骑行/跑步 | 低 | 2027 |
| Peloton | 室内健身 | 低 | 2027 |

---

## 🏗️ 架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                    BioMonitor Collectors                     │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Apple Watch  │  │    Garmin    │  │   Xiaomi     │      │
│  │   Collector  │  │   Collector  │  │  Collector   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │    Oura      │  │    WHOOP     │  │  Concept2    │      │
│  │   Collector  │  │   Collector  │  │  Collector   │◄──Hyrox│
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│  ┌──────────────┐                                           │
│  │    Strava    │  (Already Implemented)                    │
│  │   Collector  │                                           │
│  └──────────────┘                                           │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              Unified Data Model (Standardized)               │
│         Activity | HeartRate | Sleep | Recovery | Power      │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    BioMonitor Dashboard                      │
│         Cross-platform visualization & analysis              │
└─────────────────────────────────────────────────────────────┘
```

---

## 🤝 贡献

想要支持新的硬件设备？查看 [CONTRIBUTING.md](../CONTRIBUTING.md) 了解如何添加新的 Collector。

## 📧 反馈

如果你有特定的设备需求，请提交 [Issue](https://github.com/josecookai/biomonitor/issues) 或联系开发团队。
