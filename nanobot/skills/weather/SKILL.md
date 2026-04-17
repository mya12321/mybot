---
name: weather
description: Get current weather and forecasts for any location. Use when users ask about current weather, temperature, rain/wind conditions, or multi-day forecasts. Primary API is QWeather (和风天气), fallback is Seniverse (心知天气).
homepage: https://dev.qweather.com/docs/api/
metadata: {"nanobot":{"emoji":"🌤️","requires":{"bins":["curl"],"env":["QWEATHER_API_KEY"]}}}
---

# Weather

两个天气 API，和风天气为主，心知天气为备选。

## 环境变量

| 变量 | 用途 | 必需 |
|---|---|---|
| `QWEATHER_API_KEY` | 和风天气 API Key | 是 |
| `SENIVERSE_API_KEY` | 心知天气 API Key | 备选 |

## 和风天气 / QWeather（主要）

host使用 `mr65npbeke.re.qweatherapi.com`。

### 1. 城市查询（获取 Location ID）

```bash
curl -s --compressed "https://mr65npbeke.re.qweatherapi.com/geo/v2/city/lookup?location=beijing&key=$QWEATHER_API_KEY" | jq .
```

返回 `location[].id` 即 Location ID（如 `101010100` 为北京），后续接口均使用此 ID。

也可直接用 `经度,纬度` 格式（如 `116.41,39.92`）作为 location 参数。

### 2. 实时天气

```bash
curl -s --compressed "https://mr65npbeke.re.qweatherapi.com/v7/weather/now?location=101010100&key=$QWEATHER_API_KEY" | jq .
```

返回字段：`now.temp`（温度°C）· `now.feelsLike`（体感温度）· `now.text`（天气描述）· `now.windDir`（风向）· `now.windScale`（风力等级）· `now.humidity`（湿度%）· `now.precip`（降水量mm）

### 3. 天气预报

```bash
# 3天预报
curl -s --compressed "https://mr65npbeke.re.qweatherapi.com/v7/weather/3d?location=101010100&key=$QWEATHER_API_KEY" | jq .

# 7天预报
curl -s --compressed "https://mr65npbeke.re.qweatherapi.com/v7/weather/7d?location=101010100&key=$QWEATHER_API_KEY" | jq .
```

返回 `daily[]`：`fxDate`（日期）· `tempMax/tempMin`（最高/最低温）· `textDay/textNight`（白天/夜间天气）· `windDirDay`（风向）· `humidity`（湿度）

### 4. 其他常用接口

```bash
# 逐小时预报（24h）
curl -s --compressed "https://mr65npbeke.re.qweatherapi.com/v7/weather/24h?location=101010100&key=$QWEATHER_API_KEY" | jq .

# 天气预警
curl -s --compressed "https://mr65npbeke.re.qweatherapi.com/v7/warning/now?location=101010100&key=$QWEATHER_API_KEY" | jq .

# 空气质量
curl -s --compressed "https://mr65npbeke.re.qweatherapi.com/v7/air/now?location=101010100&key=$QWEATHER_API_KEY" | jq .

# 生活指数（免费版支持当天）
curl -s --compressed "https://mr65npbeke.re.qweatherapi.com/v7/indices/1d?type=0&location=101010100&key=$QWEATHER_API_KEY" | jq .
```

### 注意事项

- 所有接口返回 `code` 字段：`200` 为成功，`401` 为 Key 无效，`402` 超过调用次数
- 免费版每天 1000 次调用
- 文档：https://dev.qweather.com/docs/api/

## 心知天气 / Seniverse（备选）

当和风天气不可用时使用。免费版支持国内主要城市。

### 1. 实时天气

```bash
curl -s "https://api.seniverse.com/v3/weather/now.json?key=$SENIVERSE_API_KEY&location=beijing&language=zh-Hans&unit=c" | jq .
```

返回：`results[].now.text`（天气描述）· `results[].now.temperature`（温度）

### 2. 未来3天预报

```bash
curl -s "https://api.seniverse.com/v3/weather/daily.json?key=$SENIVERSE_API_KEY&location=beijing&language=zh-Hans&unit=c&start=0&days=3" | jq .
```

返回 `results[].daily[]`：`date` · `text_day` · `text_night` · `high` · `low` · `humidity`

### 3. 生活指数

```bash
curl -s "https://api.seniverse.com/v3/life/suggestion.json?key=$SENIVERSE_API_KEY&location=beijing&language=zh-Hans" | jq .
```

### location 参数格式

- 城市拼音：`beijing`、`shanghai`
- 城市ID：`WX4FBXXFKE4F`
- 经纬度：`39.93:116.40`
- IP地址：`220.181.111.85`（定位到所在城市）

文档：https://seniverse.yuque.com/hyper_data/api_v3
