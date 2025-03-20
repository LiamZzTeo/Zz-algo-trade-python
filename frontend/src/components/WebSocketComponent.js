import { useEffect, useRef, useState } from 'react';

const WebSocketComponent = () => {
    const socketRef = useRef(null);
    const reconnectAttemptsRef = useRef(0);
    const maxReconnectAttempts = 5;
    const reconnectDelay = 3000;
    const heartbeatIntervalRef = useRef(null);
    const isConnectingRef = useRef(false);
    const [connectionStatus, setConnectionStatus] = useState('disconnected');

    useEffect(() => {
        const connect = () => {
            if (isConnectingRef.current) {
                return; // 避免重复连接
            }

            if (reconnectAttemptsRef.current >= maxReconnectAttempts) {
                console.error('达到最大重连次数，请刷新页面重试');
                return;
            }

            isConnectingRef.current = true;
            setConnectionStatus('connecting');

            try {
                // 关闭现有连接
                if (socketRef.current && socketRef.current.readyState !== WebSocket.CLOSED) {
                    socketRef.current.close();
                }
                
                // 清除现有心跳
                if (heartbeatIntervalRef.current) {
                    clearInterval(heartbeatIntervalRef.current);
                    heartbeatIntervalRef.current = null;
                }
                
                // 创建新连接
                socketRef.current = new WebSocket('ws://localhost:8000/ws');

                socketRef.current.onopen = () => {
                    console.log('WebSocket 连接成功');
                    reconnectAttemptsRef.current = 0;
                    isConnectingRef.current = false;
                    setConnectionStatus('connected');
                    
                    // 设置心跳检测
                    heartbeatIntervalRef.current = setInterval(() => {
                        if (socketRef.current?.readyState === WebSocket.OPEN) {
                            try {
                                socketRef.current.send(JSON.stringify({ event: 'ping', ts: Date.now() }));
                            } catch (error) {
                                console.error('发送心跳失败:', error);
                                // 心跳发送失败，尝试重连
                                if (heartbeatIntervalRef.current) {
                                    clearInterval(heartbeatIntervalRef.current);
                                    heartbeatIntervalRef.current = null;
                                }
                                setConnectionStatus('disconnected');
                                reconnect();
                            }
                        }
                    }, 15000); // 15秒发送一次心跳
                };

                socketRef.current.onmessage = (event) => {
                    try {
                        const data = JSON.parse(event.data);
                        // 忽略心跳响应
                        if (data.event === 'pong') {
                            return;
                        }
                        // 分发数据更新事件
                        window.dispatchEvent(new CustomEvent('wsData', { detail: data }));
                    } catch (error) {
                        console.error('数据解析错误:', error);
                    }
                };

                socketRef.current.onclose = (event) => {
                    console.log('WebSocket 连接关闭:', event.code, event.reason);
                    isConnectingRef.current = false;
                    setConnectionStatus('disconnected');
                    
                    // 清除心跳
                    if (heartbeatIntervalRef.current) {
                        clearInterval(heartbeatIntervalRef.current);
                        heartbeatIntervalRef.current = null;
                    }
                    
                    // 只在非正常关闭时重连
                    if (event.code !== 1000) {
                        reconnect();
                    }
                };

                socketRef.current.onerror = (error) => {
                    console.error('WebSocket 错误:', error);
                    isConnectingRef.current = false;
                    setConnectionStatus('disconnected');
                    reconnect();
                };
            } catch (error) {
                console.error('WebSocket 连接创建失败:', error);
                isConnectingRef.current = false;
                setConnectionStatus('disconnected');
                reconnect();
            }
        };

        const reconnect = () => {
            // 避免重复重连
            if (isConnectingRef.current) {
                return;
            }
            
            reconnectAttemptsRef.current++;
            const delay = reconnectDelay * Math.min(reconnectAttemptsRef.current, 3);
            console.log(`将在 ${delay/1000} 秒后尝试重连... (${reconnectAttemptsRef.current}/${maxReconnectAttempts})`);
            
            setTimeout(() => {
                connect();
            }, delay);
        };

        connect();

        // 组件卸载时清理
        return () => {
            if (heartbeatIntervalRef.current) {
                clearInterval(heartbeatIntervalRef.current);
            }
            
            if (socketRef.current) {
                socketRef.current.close(1000, '组件卸载');
                socketRef.current = null;
            }
        };
    }, []);

    // 渲染连接状态指示器
    return (
        <div className={`connection-status ${connectionStatus}`}>
            <div className="status-indicator"></div>
            {connectionStatus === 'connected' ? '已连接' : 
             connectionStatus === 'connecting' ? '连接中...' : '未连接'}
        </div>
    );
};

export default WebSocketComponent;