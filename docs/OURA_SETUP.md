# Oura Ring API Setup for Carl

This guide walks you through connecting your Oura Ring to the BioMonitor
dashboard so that readiness, sleep, activity, and biometric data are synced
automatically.

---

## Step 1: Create a Personal Access Token

Open a browser and go to:

    https://cloud.ouraring.com/personal-access-tokens

<!-- SCREENSHOT: Oura developer portal — personal access tokens page -->

```
+--------------------------------------------------+
|  Oura Cloud  — Personal Access Tokens            |
|                                                  |
|  [ + Create New Personal Access Token ]          |
|                                                  |
|  Name          Scopes          Created           |
|  ──────────    ─────────────   ──────────        |
|  (none yet)                                      |
+--------------------------------------------------+
```

1. Log in with your Oura account credentials.
2. Click **"Create New Personal Access Token"**.
3. Give it the name **BioMonitor** (any name works, this is just for your reference).
4. Leave all scopes at their defaults (read access to all your data).
5. Click **"Create"**.

<!-- SCREENSHOT: Token creation dialog with name field filled in as "BioMonitor" -->

```
+--------------------------------------------------+
|  Create Personal Access Token                    |
|                                                  |
|  Name:  [ BioMonitor                          ]  |
|                                                  |
|  [ Cancel ]              [ Create Token ]        |
+--------------------------------------------------+
```

6. **Copy the token now** — it is shown only once and cannot be retrieved later.

<!-- SCREENSHOT: Token value dialog with copy button highlighted -->

```
+--------------------------------------------------+
|  Your new personal access token:                 |
|                                                  |
|  eyJhbGciOiJFUzI1NiIsInR5c...  [ Copy ]         |
|                                                  |
|  Store it somewhere safe. It won't be shown      |
|  again.                                          |
|                                                  |
|  [ Done ]                                        |
+--------------------------------------------------+
```

---

## Step 2: Add the Token to `config.yaml`

Open (or create) `config.yaml` in the BioMonitor project root:

```yaml
strava:
  client_id: "your_strava_client_id"
  client_secret: "your_strava_client_secret"
  access_token: "your_strava_access_token"
  refresh_token: "your_strava_refresh_token"

apple_health:
  export_path: "/tmp/apple_health_exports"
  webhook_enabled: true

oura:
  access_token: "eyJhbGciOiJFUzI1NiIsInR5c..."   # <-- paste your token here
```

Replace the placeholder with the token you copied in Step 1.

> **Security note:** `config.yaml` is listed in `.gitignore` and must never be
> committed to version control. Treat the token like a password.

---

## Step 3: Test the Connection

Restart the BioMonitor API server so it picks up the new config:

```bash
# From the project root
python api_server.py
```

Then trigger a sync for the past 7 days:

```bash
curl -X POST "http://localhost:8000/api/oura/sync?days=7"
```

If `BIOMONITOR_API_KEY` is configured, add the header:

```bash
curl -X POST "http://localhost:8000/api/oura/sync?days=7" \
  -H "X-API-Key: your-secret-key"
```

A successful response looks like:

```json
{
  "success": true,
  "days": 7,
  "synced": {
    "OuraReadiness": 7,
    "OuraSleepScore": 7,
    "OuraSleepDuration": 7,
    "OuraActivityScore": 7,
    "HeartRate": 1440,
    "HeartRateVariability": 84
  }
}
```

Each key shows how many records were written to the database.

---

## Step 4: Verify Data in the Dashboard

Open the dashboard at `http://localhost:3000` and check the health metrics
panels.  You can also query the API directly:

```bash
# Latest readiness scores (past 7 days)
curl "http://localhost:8000/api/oura/readiness?days=7"

# Sleep scores + duration (past 14 days)
curl "http://localhost:8000/api/oura/sleep?days=14"

# All health metrics history (any metric_type)
curl "http://localhost:8000/api/health-metrics/history?days=7&metric_type=OuraReadiness"
```

<!-- SCREENSHOT: Dashboard showing Oura readiness and sleep score charts -->

```
+────────────────────────────────────────+
│  Oura Readiness   [7-day avg: 82]      │
│                                        │
│  100 ┤                   *             │
│   85 ┤        *   *   *     *   *      │
│   70 ┤   *                             │
│      └──────────────────────────────── │
│      Mon Tue Wed Thu Fri Sat Sun        │
+────────────────────────────────────────+
│  Sleep Score      [7-day avg: 78]      │
│                                        │
│  100 ┤                                 │
│   80 ┤   *   *       *   *   *         │
│   60 ┤           *                     │
│      └──────────────────────────────── │
│      Mon Tue Wed Thu Fri Sat Sun        │
+────────────────────────────────────────+
```

---

## Available Data

All metrics are stored in the `health_metrics` table with `source = "oura"`.

| Metric Type            | Description                                    | Unit    |
|------------------------|------------------------------------------------|---------|
| `OuraReadiness`        | Daily readiness score (0–100)                  | score   |
| `OuraSleepScore`       | Daily sleep score (0–100)                      | score   |
| `OuraSleepDuration`    | Total sleep duration                           | seconds |
| `OuraActivityScore`    | Daily activity score (0–100)                   | score   |
| `HeartRate`            | Continuous heart rate samples                  | bpm     |
| `HeartRateVariability` | HRV samples from sleep (5-min averages, RMSSD) | ms      |

Query the full history at any time:

```bash
curl "http://localhost:8000/api/health-metrics/history?days=30&metric_type=HeartRateVariability"
```

---

## Troubleshooting

### 401 Unauthorized

Your access token is invalid or has been revoked.

- Verify the token in `config.yaml` matches exactly what was shown in Step 1.
- Generate a new token at https://cloud.ouraring.com/personal-access-tokens and update `config.yaml`.
- Restart the API server after any config change.

### Empty data / zero records synced

- Check that your Oura ring has synced with the Oura app on your phone.
- Try a wider date range: `?days=30`
- Confirm the ring was worn during the requested period.

### 503 "Oura access token is not configured"

The `oura.access_token` key is missing from `config.yaml`.  Follow Step 2 above.

### Rate limits

The Oura v2 API allows approximately 5,000 requests per day per token.
BioMonitor performs one request per data type per sync call (6 requests total),
so rate limiting is extremely unlikely in normal use.

### Sync command fails with connection error

- Confirm the BioMonitor API server is running: `curl http://localhost:8000/api/health`
- Check network connectivity from the server to `api.ouraring.com`.
- The collector uses a 5-second connect timeout and 30-second read timeout.
  Transient network issues will surface as connection errors in the API response.
