#!/usr/bin/env python3
"""
Strava to Railway BioMonitor Sync Script
将 Strava 数据同步到 Railway 部署的 BioMonitor
"""

import requests
import json
from datetime import datetime, timedelta
from typing import List, Dict

# Railway 部署地址
RAILWAY_API_URL = "https://biomonitor-api-production.up.railway.app"

class StravaToRailwaySync:
    """Sync Strava data to Railway BioMonitor"""
    
    def __init__(self, strava_access_token: str, railway_api_key: str = None):
        self.strava_token = strava_access_token
        self.railway_url = RAILWAY_API_URL
        self.railway_key = railway_api_key
        self.strava_base = "https://www.strava.com/api/v3"
    
    def get_strava_activities(self, days: int = 30) -> List[Dict]:
        """从 Strava 获取活动"""
        after = datetime.now() - timedelta(days=days)
        after_timestamp = int(after.timestamp())
        
        headers = {"Authorization": f"Bearer {self.strava_token}"}
        params = {"after": after_timestamp, "per_page": 50}
        
        response = requests.get(
            f"{self.strava_base}/athlete/activities",
            headers=headers,
            params=params
        )
        response.raise_for_status()
        return response.json()
    
    def transform_strava_to_biomonitor(self, activity: Dict) -> Dict:
        """将 Strava 活动格式转换为 BioMonitor 格式"""
        name = activity.get('name', 'Unknown')
        activity_type = activity.get('type', 'Workout')
        
        # 识别 CrossFit
        is_crossfit = any(keyword in name.lower() for keyword in 
                         ['crossfit', 'wod', 'murph', 'fran', 'grace', 'helen', 'cindy'])
        
        # 识别步行
        is_walking = activity_type == 'Walk' or 'walk' in name.lower()
        
        return {
            "name": name,
            "type": activity_type,
            "start_date": activity.get('start_date'),
            "distance": activity.get('distance', 0),
            "moving_time": activity.get('moving_time', 0),
            "average_heartrate": activity.get('average_heartrate'),
            "max_heartrate": activity.get('max_heartrate'),
            "calories": activity.get('calories', 0),
            "is_crossfit": is_crossfit,
            "is_walking": is_walking,
            "strava_id": activity.get('id')
        }
    
    def sync_to_railway(self, activity: Dict) -> bool:
        """同步单个活动到 Railway"""
        try:
            headers = {"Content-Type": "application/json"}
            if self.railway_key:
                headers["X-API-Key"] = self.railway_key
            
            response = requests.post(
                f"{self.railway_url}/api/activities/sync",
                headers=headers,
                json=activity,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                print(f"✅ Synced: {activity['name']}")
                return True
            else:
                print(f"⚠️  Failed: {activity['name']} - {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error syncing {activity['name']}: {e}")
            return False
    
    def run_sync(self, days: int = 30):
        """运行完整同步"""
        print(f"🚀 Starting Strava → Railway sync (last {days} days)")
        print("=" * 50)
        
        # 获取 Strava 活动
        print("📥 Fetching Strava activities...")
        activities = self.get_strava_activities(days)
        print(f"   Found {len(activities)} activities")
        
        # 转换并同步
        print("\n📤 Syncing to Railway...")
        success_count = 0
        
        for activity in activities:
            biomonitor_activity = self.transform_strava_to_biomonitor(activity)
            if self.sync_to_railway(biomonitor_activity):
                success_count += 1
        
        print("\n" + "=" * 50)
        print(f"✅ Sync complete: {success_count}/{len(activities)} activities synced")
        print(f"🌐 View at: https://biomonitor-web-production.up.railway.app")


def main():
    """主函数 - 交互式配置"""
    print("🔄 Strava → Railway BioMonitor Sync")
    print("=" * 50)
    
    # 获取 Strava Token
    print("\n📋 请提供你的 Strava Access Token:")
    print("   (从 https://www.strava.com/settings/api 获取)")
    strava_token = input("Strava Access Token: ").strip()
    
    if not strava_token:
        print("❌ 需要提供 Strava Token")
        return
    
    # Railway API Key (可选)
    print("\n📋 Railway API Key (可选，按回车跳过):")
    railway_key = input("Railway API Key: ").strip() or None
    
    # 同步天数
    print("\n📋 同步最近多少天的活动? (默认 30)")
    days_input = input("Days [30]: ").strip()
    days = int(days_input) if days_input else 30
    
    # 运行同步
    sync = StravaToRailwaySync(strava_token, railway_key)
    sync.run_sync(days)


if __name__ == "__main__":
    main()
