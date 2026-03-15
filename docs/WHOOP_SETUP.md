# WHOOP API Setup for ZN

## Overview

WHOOP uses OAuth 2.0. You authorize BioMonitor once and it syncs automatically.
After the initial setup, the server auto-refreshes expired tokens whenever you
call `/api/whoop/sync`.

OAuth flow at a glance:

```
  ZN's browser
      |
      |  1. Visit auth URL
      v
  WHOOP website  ----->  "Authorize BioMonitor?" ----->  ZN clicks Allow
                                                              |
                                                              | 2. WHOOP redirects to
                                                              |    localhost:8000/api/whoop/callback
                                                              |    ?code=AUTH_CODE
                                                              v
                                                     BioMonitor exchanges
                                                     code for tokens
                                                              |
                                                              v
                                                     Tokens saved to config.yaml
                                                     Ready to sync!
```


## Step 1: Create a WHOOP Developer App

1. Go to https://developer.whoop.com
2. Sign in with your WHOOP account credentials
3. Click "Create App" (or "New Application")
4. Fill in the application details:
   - **Name**: BioMonitor
   - **Redirect URI**: `http://localhost:8000/api/whoop/callback`
   - **Scopes**: select all of the following:
     - `read:recovery`
     - `read:sleep`
     - `read:workout`
     - `read:cycles`
     - `read:body_measurement`
5. Save the app and copy your **Client ID** and **Client Secret**


## Step 2: Add credentials to config.yaml

Open `/home/ubuntu/biomonitor/config.yaml` (create it if it does not exist)
and add the following block. Replace the placeholder values:

```yaml
whoop:
  client_id: "YOUR_CLIENT_ID"
  client_secret: "YOUR_CLIENT_SECRET"
  redirect_uri: "http://localhost:8000/api/whoop/callback"
  # access_token and refresh_token are written here automatically after Step 4
```

Restart the BioMonitor API server after saving:

```bash
# If running manually:
cd /home/ubuntu/biomonitor
python api_server.py

# If using a process manager (e.g. systemd), restart the unit:
# sudo systemctl restart biomonitor
```


## Step 3: Get the Authorization URL

```bash
curl -s http://localhost:8000/api/whoop/auth-url
```

Expected response:

```json
{
  "auth_url": "https://api.prod.whoop.com/oauth/oauth2/auth?client_id=YOUR_CLIENT_ID&redirect_uri=http%3A%2F%2Flocalhost%3A8000%2Fapi%2Fwhoop%2Fcallback&scope=read%3Arecovery%20read%3Asleep%20read%3Aworkout%20read%3Acycles%20read%3Abody_measurement&response_type=code"
}
```

Copy the `auth_url` value and open it in your browser.


## Step 4: Authorize BioMonitor in your browser

1. The WHOOP login/authorization page opens.
2. Log in with your WHOOP credentials if prompted.
3. Click **Authorize** to grant BioMonitor access.
4. Your browser is redirected to a URL like:

   ```
   http://localhost:8000/api/whoop/callback?code=ABCDEF123456
   ```

   The server may return a 422/404 error page — that is expected, because the
   callback endpoint expects a POST with a JSON body, not a browser GET.

5. Copy the value of the `code` query parameter from the address bar.


## Step 5: Exchange the code for tokens

Paste the code you copied into this curl command:

```bash
curl -s -X POST http://localhost:8000/api/whoop/callback \
     -H "Content-Type: application/json" \
     -d '{"code": "PASTE_YOUR_CODE_HERE"}'
```

Expected response:

```json
{
  "success": true,
  "message": "WHOOP tokens saved. You can now sync data."
}
```

The tokens are written to `config.yaml` automatically under `whoop.access_token`
and `whoop.refresh_token`. You do not need to handle token refreshes manually —
BioMonitor does this automatically.


## Step 6: Sync your data

```bash
# Sync the last 7 days (default)
curl -s -X POST http://localhost:8000/api/whoop/sync

# Sync the last 30 days
curl -s -X POST "http://localhost:8000/api/whoop/sync?days=30"
```

Expected response:

```json
{
  "success": true,
  "days": 7,
  "saved": {
    "WhoopRecovery": 7,
    "HeartRateVariability": 7,
    "HeartRate": 7,
    "WhoopSleepScore": 7,
    "SleepAnalysis": 7,
    "WhoopStrain": 6
  }
}
```

## Step 7: Query synced data

```bash
# Recovery scores for the last 7 days
curl -s "http://localhost:8000/api/whoop/recovery?days=7"

# Strain scores for the last 14 days
curl -s "http://localhost:8000/api/whoop/strain?days=14"

# All health metrics (includes WHOOP alongside Oura, Apple Health, etc.)
curl -s "http://localhost:8000/api/health-metrics/history?days=7&metric_type=WhoopRecovery"
```


## What data is synced

| Metric              | WHOOP API field                      | BioMonitor metric_type  | Unit    |
|---------------------|--------------------------------------|-------------------------|---------|
| Recovery Score      | score.recovery_score                 | WhoopRecovery           | score   |
| HRV (RMSSD)         | score.hrv_rmssd_milli                | HeartRateVariability    | ms      |
| Resting Heart Rate  | score.resting_heart_rate             | HeartRate               | bpm     |
| Sleep Performance   | score.sleep_performance_percentage   | WhoopSleepScore         | %       |
| Total Sleep Time    | score.total_sleep_time_milli / 3.6M  | SleepAnalysis           | hours   |
| Daily Strain        | score.strain                         | WhoopStrain             | strain  |


## API Reference

| Method | Endpoint                     | Description                             |
|--------|------------------------------|-----------------------------------------|
| GET    | /api/whoop/auth-url          | Get the OAuth authorization URL         |
| POST   | /api/whoop/callback          | Exchange authorization code for tokens  |
| POST   | /api/whoop/sync?days=N       | Sync WHOOP data into the database       |
| GET    | /api/whoop/recovery?days=N   | Fetch recovery scores from database     |
| GET    | /api/whoop/strain?days=N     | Fetch strain scores from database       |


## Troubleshooting

**401 Unauthorized during sync**

The access token has expired. POST to `/api/whoop/sync` — the collector
automatically calls `refresh_access_token()` before retrying. If this still
fails, the refresh token itself may have expired; repeat Steps 3-5 to
re-authorize.

**`WHOOP client_id is not configured` error**

The `whoop` section is missing from `config.yaml`. Complete Step 2.

**Empty `saved` counts after sync**

- WHOOP free tier provides up to 45 days of historical data.
- Verify the date range: if you just created the app today, there may be less
  data available than the `days` parameter requests.
- Check the server logs for `[WhoopCollector]` error lines.

**"Token exchange failed" on /api/whoop/callback**

Authorization codes are single-use and expire after a few minutes. Repeat
Steps 3-5 quickly without delay between generating the URL and exchanging
the code.

**Rate limits**

WHOOP allows approximately 100 requests per minute per app. Normal sync
operations stay well below this limit. If you receive HTTP 429 responses,
wait 60 seconds before retrying.
