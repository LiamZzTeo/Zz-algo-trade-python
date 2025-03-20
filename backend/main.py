from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from okx_client import OKXClient
import asyncio
import json
import sys
import time
from typing import List
import starlette.websockets  # 添加这行

app = FastAPI()
okx_client = OKXClient()

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket 连接管理
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.running = True

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"新连接建立，当前连接数: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            print(f"连接断开，当前连接数: {len(self.active_connections)}")

# 创建全局 manager 实例
manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        # 发送初始连接成功消息
        await websocket.send_json({"type": "connected", "message": "WebSocket连接成功"})
        
        while manager.running:
            try:
                # 使用 wait_for 来处理客户端消息，设置较短的超时时间
                try:
                    data = await asyncio.wait_for(websocket.receive_text(), timeout=0.1)
                    # 处理客户端消息
                    try:
                        client_data = json.loads(data)
                        if client_data.get("event") == "ping":
                            await websocket.send_json({"event": "pong", "ts": int(time.time() * 1000)})
                            continue
                    except json.JSONDecodeError:
                        pass
                except asyncio.TimeoutError:
                    # 超时正常，继续处理
                    pass
                except WebSocketDisconnect:
                    # 客户端断开连接
                    print("客户端断开连接")
                    break
                
                # 获取账户数据
                account_data = okx_client.get_account_balance()
                if not account_data["success"]:
                    print(f"获取账户数据失败: {account_data['msg']}")
                    # 设置默认值而不是中断循环
                    account_data = {"data": {}}
                
                # 获取持仓数据
                positions_data = okx_client.get_positions()
                if not positions_data["success"]:
                    print(f"获取持仓数据失败: {positions_data['msg']}")
                    positions_data = {"data": []}

                # 移除了获取交易历史的部分

                message = {
                    "type": "update",
                    "data": {
                        "account": account_data.get("data", {}),
                        "positions": positions_data.get("data", [])
                        # 移除了 trades 字段
                    },
                    "timestamp": int(time.time() * 1000)
                }

                try:
                    # 使用 wait_for 来发送消息，避免长时间阻塞
                    await asyncio.wait_for(websocket.send_json(message), timeout=2.0)
                    # 减少更新间隔，避免长时间阻塞
                    await asyncio.sleep(5)
                except (WebSocketDisconnect, starlette.websockets.WebSocketDisconnect):
                    print("WebSocket 连接已断开")
                    break
                except asyncio.TimeoutError:
                    print("发送消息超时")
                    break
                except Exception as e:
                    print(f"发送数据错误: {str(e)}")
                    break

            except Exception as e:
                print(f"WebSocket 数据处理错误: {str(e)}")
                await asyncio.sleep(2)
                continue
    except Exception as e:
        print(f"WebSocket 连接错误: {str(e)}")
    finally:
        manager.disconnect(websocket)

# 优雅关闭
@app.on_event("shutdown")
async def shutdown_event():
    manager.running = False
    for connection in manager.active_connections:
        await connection.close()
