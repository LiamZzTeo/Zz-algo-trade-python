import requests
import json
import hmac
import base64
import datetime
import time
from typing import Optional, Dict, Any

class OKXClient:
    def __init__(self):
        self.api_key = "d1478ccd-87bd-4901-a28b-11f446800d61"
        self.secret_key = "70E057877E4B8A5348B7E0FD12097040"
        self.passphrase = "Zhangzehang1234!!!"
        self.base_url = "https://www.okx.com"
        self.is_test = True
        self.debug = False

    def _get_timestamp(self):
        now = datetime.datetime.utcnow()
        return now.isoformat("T", "milliseconds") + "Z"

    def _sign(self, timestamp: str, method: str, request_path: str, body: str = "") -> str:
        # 确保请求路径以 /api/v5 开头
        if not request_path.startswith('/api/v5'):
            request_path = '/api/v5' + request_path
            
        message = timestamp + method.upper() + request_path + (body or "")
        mac = hmac.new(
            bytes(self.secret_key, encoding='utf8'),
            bytes(message, encoding='utf-8'),
            digestmod='sha256'
        )
        return base64.b64encode(mac.digest()).decode()

    def _send_request(self, method: str, request_path: str, body: Optional[Dict] = None) -> Dict[str, Any]:
        # 确保请求路径格式正确
        if not request_path.startswith('/'):
            request_path = '/' + request_path
        
        if not request_path.startswith('/api/v5'):
            request_path = '/api/v5' + request_path
            
        timestamp = self._get_timestamp()
        if body:
            body_str = json.dumps(body)
        else:
            body_str = ''

        sign = self._sign(timestamp, method, request_path, body_str)
        headers = {
            "OK-ACCESS-KEY": self.api_key,
            "OK-ACCESS-SIGN": sign,
            "OK-ACCESS-TIMESTAMP": timestamp,
            "OK-ACCESS-PASSPHRASE": self.passphrase,
            "Content-Type": "application/json",
            "x-simulated-trading": "1"  # 使用模拟交易
        }

        url = f"{self.base_url}{request_path}"
        
        if self.debug:
            print(f"请求URL: {url}")
            print(f"请求头: {headers}")
            print(f"请求体: {body_str}")
            
        try:
            response = requests.request(method, url, headers=headers, data=body_str, timeout=15)
            if self.debug:
                print(f"响应状态码: {response.status_code}")
                print(f"响应内容: {response.text}")
                
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": result.get("code") == "0",
                    "data": result.get("data", []),
                    "msg": result.get("msg", "success")
                }
            return {"success": False, "data": [], "msg": f"HTTP Error: {response.status_code}, {response.text}"}
        except Exception as e:
            if self.debug:
                print(f"请求异常: {str(e)}")
            return {"success": False, "data": [], "msg": str(e)}

    def get_account_balance(self):
        try:
            result = self._send_request("GET", "/account/balance")
            if result["success"] and result["data"]:
                balance_data = result["data"][0] if isinstance(result["data"], list) and result["data"] else {}
                return {
                    "success": True,
                    "data": balance_data,
                    "msg": "success"
                }
            return result
        except Exception as e:
            print(f"获取账户余额错误: {e}")
            return {"success": False, "data": {}, "msg": str(e)}
    
    def get_positions(self):
        try:
            params = {
                "instType": "SWAP",
            }
            result = self._send_request("GET", "/account/positions", body=params)
            return {
                "success": result["success"],
                "data": result["data"] if result["success"] else [],
                "msg": result["msg"]
            }
        except Exception as e:
            print(f"获取持仓信息错误: {e}")
            return {"success": False, "data": [], "msg": str(e)}