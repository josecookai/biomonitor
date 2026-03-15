#!/usr/bin/env python3
"""
一键设置 Strava 集成到 Railway
用法: python setup_strava.py
"""

import json
import os
import sys

def main():
    print("🏃 BioMonitor Strava 集成设置")
    print("=" * 60)
    
    # 检查现有 tokens
    tokens_file = "strava_tokens.json"
    tokens = {}
    
    if os.path.exists(tokens_file):
        print(f"\n📄 发现已保存的 tokens: {tokens_file}")
        with open(tokens_file) as f:
            tokens = json.load(f)
        use_existing = input("使用现有 tokens? (Y/n): ").strip().lower() != 'n'
    else:
        use_existing = False
    
    if not use_existing:
        print("\n👉 请运行: python get_strava_token.py")
        print("   获取 tokens 后重新运行此脚本")
        sys.exit(0)
    
    # 显示 Railway 配置
    print("\n" + "=" * 60)
    print("🚂 Railway 环境变量配置")
    print("=" * 60)
    print("\n请访问: https://railway.app/dashboard")
    print("进入你的项目 → Variables → New Variable")
    print("\n添加以下变量:\n")
    
    client_id = input("Strava Client ID: ").strip()
    client_secret = input("Strava Client Secret: ").strip()
    
    print(f"\nSTRAVA_CLIENT_ID={client_id}")
    print(f"STRAVA_CLIENT_SECRET={client_secret}")
    print(f"STRAVA_ACCESS_TOKEN={tokens.get('access_token', '')}")
    print(f"STRAVA_REFRESH_TOKEN={tokens.get('refresh_token', '')}")
    
    print("\n" + "=" * 60)
    print("✅ 下一步")
    print("=" * 60)
    print("1. 复制上面的变量到 Railway Dashboard")
    print("2. Railway 会自动重新部署")
    print("3. 访问: https://biomonitor-web-production.up.railway.app")
    print("4. 测试同步: curl -X POST https://biomonitor-api-production.up.railway.app/api/strava/sync?days=30")

if __name__ == "__main__":
    main()