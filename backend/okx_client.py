import requests
import json
import hmac
import base64
import datetime
import time
import os
from typing import Optional, Dict, Any

class OKXClient:
    def __init__(self):
        # 从环境变量获取API凭证，如果环境变量不存在则使用默认值
        self.api_key = os.environ.get("OKX_API_KEY", "d1478ccd-87bd-4901-a28b-11f446800d61")
        self.secret_key = os.environ.get("OKX_SECRET_KEY", "70E057877E4B8A5348B7E0FD12097040")
        self.passphrase = os.environ.get("OKX_PASSPHRASE", "Zhangzehang1234!!!")
        self.base_url = os.environ.get("OKX_BASE_URL", "https://www.okx.com")
        self.is_test = os.environ.get("OKX_IS_TEST", "True").lower() == "true"
        self.debug = os.environ.get("OKX_DEBUG", "False").lower() == "true"
        # 添加缓存
        self._cache = {}
        self._cache_time = {}
        self._cache_duration = int(os.environ.get("OKX_CACHE_DURATION", "5"))  # 缓存有效期（秒）

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
        max_retries = 3
        retry_delay = 2
        
        for retry in range(max_retries):
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
                response = requests.request(method, url, headers=headers, data=body_str, timeout=30)  # 增加请求超时时间
                
                if response.status_code == 200:
                    result = response.json()
                    return {
                        "success": result.get("code") == "0",
                        "data": result.get("data", []),
                        "msg": result.get("msg", "success")
                    }
                
                if retry < max_retries - 1:
                    print(f"请求失败 (HTTP {response.status_code})，将在 {retry_delay} 秒后重试...")
                    time.sleep(retry_delay)
                    continue
                
                return {"success": False, "data": [], "msg": f"HTTP Error: {response.status_code}"}
                
            except Exception as e:
                if retry < max_retries - 1:
                    print(f"请求异常，将在 {retry_delay} 秒后重试: {str(e)}")
                    time.sleep(retry_delay)
                    continue
                return {"success": False, "data": [], "msg": str(e)}

    def _get_cached_data(self, key: str) -> Optional[Dict]:
        if key in self._cache:
            last_update = self._cache_time.get(key, 0)
            if time.time() - last_update < self._cache_duration:
                return self._cache[key]
        return None

    def _set_cache(self, key: str, data: Dict):
        self._cache[key] = data
        self._cache_time[key] = time.time()

    def get_account_balance(self):
        cache_key = 'account_balance'
        cached_data = self._get_cached_data(cache_key)
        if cached_data:
            return cached_data

        try:
            result = self._send_request("GET", "/account/balance")
            if result["success"] and result["data"]:
                balance_data = result["data"][0] if isinstance(result["data"], list) and result["data"] else {}
                response = {
                    "success": True,
                    "data": balance_data,
                    "msg": "success"
                }
                self._set_cache(cache_key, response)
                return response
            return result
        except Exception as e:
            print(f"获取账户余额错误: {e}")
            return {"success": False, "data": {}, "msg": str(e)}
    
    def get_positions(self):
        cache_key = 'positions'
        cached_data = self._get_cached_data(cache_key)
        if cached_data:
            return cached_data

        try:
            params = {
                "instType": "SWAP",
            }
            result = self._send_request("GET", "/account/positions", body=params)
            if result["success"]:
                self._set_cache(cache_key, result)
            return result
        except Exception as e:
            print(f"获取持仓信息错误: {e}")
            return {"success": False, "data": [], "msg": str(e)}

    def get_market_data(self, instId: str):
        """获取市场行情数据"""
        cache_key = f'market_data_{instId}'
        cached_data = self._get_cached_data(cache_key)
        if cached_data:
            return cached_data
    
        try:
            # 获取行情数据
            result = self._send_request("GET", f"/market/ticker?instId={instId}")
            if result["success"]:
                self._set_cache(cache_key, result)
            return result
        except Exception as e:
            print(f"获取市场数据错误: {e}")
            return {"success": False, "data": {}, "msg": str(e)}

    def place_order(self, instId: str, tdMode: str, side: str, 
                    ordType: str, sz: str, px: str = None):
        """
        下单交易
        :param instId: 产品ID，如"BTC-USDT-SWAP"
        :param tdMode: 交易模式，如"cross"(全仓),"isolated"(逐仓)
        :param side: 订单方向，"buy"或"sell"
        :param ordType: 订单类型，如"market"(市价单),"limit"(限价单)
        :param sz: 委托数量
        :param px: 委托价格，市价单可不传
        """
        try:
            params = {
                "instId": instId,
                "tdMode": tdMode,
                "side": side,
                "ordType": ordType,
                "sz": sz
            }
            
            if px and ordType == "limit":
                params["px"] = px
                
            result = self._send_request("POST", "/trade/order", params)
            return result
        except Exception as e:
            print(f"下单错误: {e}")
            return {"success": False, "data": {}, "msg": str(e)}

    def cancel_order(self, instId: str, ordId: str = None, clOrdId: str = None):
        """
        撤销订单
        :param instId: 产品ID
        :param ordId: 订单ID
        :param clOrdId: 客户自定义订单ID
        """
        try:
            params = {"instId": instId}
            
            if ordId:
                params["ordId"] = ordId
            elif clOrdId:
                params["clOrdId"] = clOrdId
            else:
                return {"success": False, "data": {}, "msg": "ordId和clOrdId不能同时为空"}
                
            result = self._send_request("POST", "/trade/cancel-order", params)
            return result
        except Exception as e:
            print(f"撤单错误: {e}")
            return {"success": False, "data": {}, "msg": str(e)}

    def get_ticker(self, symbol):
        """获取当前价格"""
        cache_key = f'ticker_{symbol}'
        cached_data = self._get_cached_data(cache_key)
        if cached_data:
            return cached_data
    
        try:
            endpoint = f"/market/ticker?instId={symbol}"
            result = self._send_request("GET", endpoint)
            if result["success"]:
                self._set_cache(cache_key, result)
            return result
        except Exception as e:
            print(f"获取当前价格错误: {str(e)}")
            return {"success": False, "data": [], "msg": str(e)}
            
    def get_kline_data(self, symbol, bar="1m", limit=100):
        """获取K线数据"""
        cache_key = f'kline_{symbol}_{bar}_{limit}'
        cached_data = self._get_cached_data(cache_key)
        if cached_data:
            return cached_data
    
        try:
            endpoint = f"/market/candles?instId={symbol}&bar={bar}&limit={limit}"
            result = self._send_request("GET", endpoint)
            if result["success"]:
                self._set_cache(cache_key, result)
            return result
        except Exception as e:
            print(f"获取K线数据错误: {str(e)}")
            return {"success": False, "data": [], "msg": str(e)}

    def get_instruments(self, inst_types=None):
        """获取所有可交易产品
        
        Args:
            inst_types: 产品类型列表，例如 ["SPOT", "SWAP", "FUTURES", "OPTION"]
                       如果为 None，则获取所有类型
        """
        if inst_types is None:
            inst_types = ["SPOT", "SWAP", "FUTURES", "OPTION"]
        
        all_instruments = []
        
        for inst_type in inst_types:
            cache_key = f'instruments_{inst_type}'
            cached_data = self._get_cached_data(cache_key)
            
            if cached_data and cached_data.get("success"):
                all_instruments.extend(cached_data.get("data", []))
                continue
            
            try:
                endpoint = f"/api/v5/public/instruments?instType={inst_type}"
                result = self._send_request("GET", endpoint)
                
                if result["success"]:
                    self._set_cache(cache_key, result)
                    all_instruments.extend(result.get("data", []))
                else:
                    print(f"获取 {inst_type} 产品列表失败: {result.get('msg')}")
            except Exception as e:
                print(f"获取 {inst_type} 产品列表错误: {str(e)}")
        
        return {
            "success": True,
            "data": all_instruments,
            "msg": f"获取到 {len(all_instruments)} 个交易产品"
        }

    def get_market_data(self, symbol):
        """获取市场数据，包括最新价格、24小时涨跌幅等"""
        cache_key = f'market_data_{symbol}'
        cached_data = self._get_cached_data(cache_key)
        if cached_data:
            return cached_data
        
        try:
            # 获取ticker数据
            ticker_data = self.get_ticker(symbol)
            
            # 获取K线数据
            kline_data = self.get_kline(symbol, "1m", 60)  # 获取1分钟K线，60条数据
            
            market_data = {
                "symbol": symbol,
                "last": ticker_data.get("data", {}).get("last", "0"),
                "open24h": ticker_data.get("data", {}).get("open24h", "0"),
                "high24h": ticker_data.get("data", {}).get("high24h", "0"),
                "low24h": ticker_data.get("data", {}).get("low24h", "0"),
                "volCcy24h": ticker_data.get("data", {}).get("volCcy24h", "0"),
                "change24h": ticker_data.get("data", {}).get("change24h", "0"),
                "kline": kline_data.get("data", [])
            }
            
            result = {"success": True, "data": market_data}
            self._set_cache(cache_key, result)
            return result
        except Exception as e:
            print(f"获取市场数据错误: {str(e)}")
            return {"success": False, "data": {}, "msg": str(e)}

    def get_kline(self, symbol, bar="1m", limit=100):
        """获取K线数据"""
        cache_key = f'kline_{symbol}_{bar}_{limit}'
        cached_data = self._get_cached_data(cache_key)
        if cached_data:
            return cached_data
        
        try:
            endpoint = f"/api/v5/market/candles?instId={symbol}&bar={bar}&limit={limit}"
            result = self._send_request("GET", endpoint)
            if result["success"]:
                self._set_cache(cache_key, result)
            return result
        except Exception as e:
            print(f"获取K线数据错误: {str(e)}")
            return {"success": False, "data": [], "msg": str(e)}

    def get_ticker(self, symbol):
        """获取单个产品的行情数据"""
        cache_key = f'ticker_{symbol}'
        cached_data = self._get_cached_data(cache_key)
        if cached_data:
            return cached_data
        
        try:
            endpoint = f"/api/v5/market/ticker?instId={symbol}"
            result = self._send_request("GET", endpoint)
            if result["success"]:
                self._set_cache(cache_key, result)
            return result
        except Exception as e:
            print(f"获取行情数据错误: {str(e)}")
            return {"success": False, "data": {}, "msg": str(e)}

    def get_market_data(self, symbol):
        """获取市场数据，包括最新价格、24小时涨跌幅等"""
        try:
            # 获取ticker数据
            ticker_data = self.get_ticker(symbol)
            
            if not ticker_data["success"]:
                return ticker_data
                
            # 提取需要的数据
            ticker = ticker_data.get("data", [{}])[0]
            
            market_data = {
                "symbol": symbol,
                "last": ticker.get("last", "0"),
                "open24h": ticker.get("open24h", "0"),
                "high24h": ticker.get("high24h", "0"),
                "low24h": ticker.get("low24h", "0"),
                "volCcy24h": ticker.get("volCcy24h", "0"),
                "change24h": ticker.get("sodUtc0", "0"),  # 根据OKX API文档，这是24小时涨跌幅
            }
            
            return {"success": True, "data": market_data}
        except Exception as e:
            print(f"获取市场数据错误: {str(e)}")
            return {"success": False, "data": {}, "msg": str(e)}

    def get_assets(self):
        """获取资产数据（与账户数据相同，但格式可能不同）"""
        try:
            # 调用已有的获取账户余额方法
            account_data = self.get_account_balance()
            
            if not account_data["success"]:
                return account_data
                
            # 可以根据需要调整数据格式
            assets_data = account_data.get("data", {})
            
            return {"success": True, "data": assets_data}
        except Exception as e:
            print(f"获取资产数据错误: {str(e)}")
            return {"success": False, "data": {}, "msg": str(e)}