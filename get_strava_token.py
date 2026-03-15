#!/usr/bin/env python3
"""
自动获取 Strava Access Token
使用 Strava OAuth2 流程
"""

import urllib.request
import urllib.parse
import json
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import time

# 配置 - 需要用户填写
CLIENT_ID = input("Enter your Strava Client ID: ").strip()
CLIENT_SECRET = input("Enter your Strava Client Secret: ").strip()

if not CLIENT_ID or not CLIENT_SECRET:
    print("❌ 需要提供 Client ID 和 Client Secret")
    exit(1)

# 回调服务器配置
REDIRECT_PORT = 8080
REDIRECT_URI = f"http://localhost:{REDIRECT_PORT}"

# 全局变量存储 code
auth_code = None

class CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global auth_code
        
        # 解析 URL 参数
        from urllib.parse import urlparse, parse_qs
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        
        if 'code' in params:
            auth_code = params['code'][0]
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"""
                <html>
                <body style="font-family: Arial; text-align: center; padding: 50px;">
                    <h1>✅ Authorization Successful!</h1>
                    <p>You can close this window and return to the terminal.</p>
                </body>
                </html>
            """)
        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Authorization failed")
    
    def log_message(self, format, *args):
        pass  # 隐藏日志

def get_access_token():
    """获取 Strava Access Token"""
    global auth_code
    
    # 启动回调服务器
    server = HTTPServer(('localhost', REDIRECT_PORT), CallbackHandler)
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()
    
    # 构建授权 URL
    auth_url = (
        f"https://www.strava.com/oauth/authorize?"
        f"client_id={CLIENT_ID}&"
        f"response_type=code&"
        f"redirect_uri={REDIRECT_URI}&"
        f"approval_prompt=force&"
        f"scope=read,activity:read"
    )
    
    print("\n" + "=" * 60)
    print("🚀 Step 1: Opening Strava authorization page...")
    print("=" * 60)
    
    # 打开浏览器
    webbrowser.open(auth_url)
    print(f"\nIf browser didn't open, visit:\n{auth_url}\n")
    
    # 等待回调
    print("⏳ Waiting for authorization...")
    timeout = 120
    start = time.time()
    
    while auth_code is None and time.time() - start < timeout:
        time.sleep(1)
    
    server.shutdown()
    
    if auth_code is None:
        print("\n❌ Timeout! Authorization failed.")
        return None
    
    print("✅ Authorization code received!")
    
    # 交换 code 获取 token
    print("\n" + "=" * 60)
    print("🚀 Step 2: Exchanging code for access token...")
    print("=" * 60)
    
    token_data = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'code': auth_code,
        'grant_type': 'authorization_code'
    }
    
    req = urllib.request.Request(
        "https://www.strava.com/oauth/token",
        data=urllib.parse.urlencode(token_data).encode(),
        headers={'Content-Type': 'application/x-www-form-urlencoded'},
        method='POST'
    )
    
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
            
            print("\n" + "=" * 60)
            print("✅ SUCCESS! Here are your tokens:")
            print("=" * 60)
            print(f"\n🔑 Access Token:\n{data.get('access_token')}")
            print(f"\n🔑 Refresh Token:\n{data.get('refresh_token')}")
            print(f"\n👤 Athlete: {data.get('athlete', {}).get('firstname')} {data.get('athlete', {}).get('lastname')}")
            print(f"\n⏰ Expires at: {data.get('expires_at')}")
            
            # 保存到文件
            with open('strava_tokens.json', 'w') as f:
                json.dump(data, f, indent=2)
            print("\n💾 Tokens saved to strava_tokens.json")
            
            # 显示 Railway 配置
            print("\n" + "=" * 60)
            print("🚀 Railway Environment Variables:")
            print("=" * 60)
            print(f"STRAVA_CLIENT_ID={CLIENT_ID}")
            print(f"STRAVA_CLIENT_SECRET={CLIENT_SECRET}")
            print(f"STRAVA_ACCESS_TOKEN={data.get('access_token')}")
            print(f"STRAVA_REFRESH_TOKEN={data.get('refresh_token')}")
            
            return data
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return None

if __name__ == "__main__":
    print("🏃 Strava Token Generator for BioMonitor")
    print("=" * 60)
    
    result = get_access_token()
    
    if result:
        print("\n✅ All done! Copy the tokens above to Railway environment variables.")
    else:
        print("\n❌ Failed to get tokens. Please try again.")
