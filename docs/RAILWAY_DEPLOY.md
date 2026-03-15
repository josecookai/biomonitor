# Railway Deploy

This repo is deployed to Railway as two services:

1. `biomonitor-api`
2. `biomonitor-web`

## API service

- Root: repo root
- Dockerfile: `/Dockerfile`
- Port: Railway `PORT`
- Recommended vars:
  - `CORS_ORIGINS=https://your-frontend-domain`
  - `STRAVA_CLIENT_ID=...`
  - `STRAVA_CLIENT_SECRET=...`
  - `STRAVA_ACCESS_TOKEN=...`
  - `STRAVA_REFRESH_TOKEN=...`

## Web service

- Root: `dashboard/web`
- Dockerfile: `dashboard/web/Dockerfile`
- Port: Railway `PORT`
- Required build/runtime vars:
  - `NEXT_PUBLIC_API_URL=https://your-api-domain`

## Deploy order

1. Deploy API service
2. Generate Railway domain for API
3. Set `NEXT_PUBLIC_API_URL` on web service
4. Deploy web service
5. Generate Railway domain for web service
6. Update API `CORS_ORIGINS` with web domain and redeploy API
