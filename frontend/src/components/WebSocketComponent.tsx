import { useEffect, useRef } from 'react';

const WebSocketComponent = () => {
    const socketRef = useRef<WebSocket | null>(null);
    const reconnectAttemptsRef = useRef(0);
    const maxReconnectAttempts = 5;
    const reconnectDelay = 3000;
    const heartbeatIntervalRef = useRef<NodeJS.Timeout | null>(null);
    const isConnectingRef = useRef(false);

    useEffect(() => {
        const connect = () => {
            if (isConnectingRef.current) {
                return; // Avoid duplicate connections
            }

            if (reconnectAttemptsRef.current >= maxReconnectAttempts) {
                console.error('Maximum reconnection attempts reached, please refresh the page');
                return;
            }

            isConnectingRef.current = true;

            try {
                // Close existing connection
                if (socketRef.current && socketRef.current.readyState !== WebSocket.CLOSED) {
                    socketRef.current.close();
                }
                
                // Clear existing heartbeat
                if (heartbeatIntervalRef.current) {
                    clearInterval(heartbeatIntervalRef.current);
                    heartbeatIntervalRef.current = null;
                }
                
                // Create new connection
                socketRef.current = new WebSocket('ws://localhost:8000/ws');

                socketRef.current.onopen = () => {
                    console.log('WebSocket connection successful');
                    reconnectAttemptsRef.current = 0;
                    isConnectingRef.current = false;
                    
                    // Set heartbeat detection
                    heartbeatIntervalRef.current = setInterval(() => {
                        if (socketRef.current?.readyState === WebSocket.OPEN) {
                            try {
                                socketRef.current.send(JSON.stringify({ event: 'ping', ts: Date.now() }));
                            } catch (error) {
                                console.error('Failed to send heartbeat:', error);
                                // Heartbeat failed, try to reconnect
                                if (heartbeatIntervalRef.current) {
                                    clearInterval(heartbeatIntervalRef.current);
                                    heartbeatIntervalRef.current = null;
                                }
                                reconnect();
                            }
                        }
                    }, 15000); // Send heartbeat every 15 seconds
                };

                socketRef.current.onmessage = (event) => {
                    try {
                        const data = JSON.parse(event.data);
                        // Ignore heartbeat responses
                        if (data.event === 'pong') {
                            return;
                        }
                        // Dispatch data update event
                        window.dispatchEvent(new CustomEvent('wsData', { detail: data }));
                    } catch (error) {
                        console.error('Data parsing error:', error);
                    }
                };

                socketRef.current.onclose = (event) => {
                    console.log('WebSocket connection closed:', event.code, event.reason);
                    isConnectingRef.current = false;
                    
                    // Clear heartbeat
                    if (heartbeatIntervalRef.current) {
                        clearInterval(heartbeatIntervalRef.current);
                        heartbeatIntervalRef.current = null;
                    }
                    
                    // Only reconnect on abnormal closure
                    if (event.code !== 1000) {
                        reconnect();
                    }
                };

                socketRef.current.onerror = (error) => {
                    console.error('WebSocket error:', error);
                    isConnectingRef.current = false;
                    reconnect();
                };
            } catch (error) {
                console.error('WebSocket connection creation failed:', error);
                isConnectingRef.current = false;
                reconnect();
            }
        };

        const reconnect = () => {
            // Avoid duplicate reconnections
            if (isConnectingRef.current) {
                return;
            }
            
            reconnectAttemptsRef.current++;
            const delay = reconnectDelay * Math.min(reconnectAttemptsRef.current, 3);
            console.log(`Will try to reconnect in ${delay/1000} seconds... (${reconnectAttemptsRef.current}/${maxReconnectAttempts})`);
            
            setTimeout(() => {
                connect();
            }, delay);
        };

        connect();

        // Cleanup on component unmount
        return () => {
            if (heartbeatIntervalRef.current) {
                clearInterval(heartbeatIntervalRef.current);
            }
            
            if (socketRef.current) {
                socketRef.current.close(1000, 'Component unmounted');
                socketRef.current = null;
            }
        };
    }, []);

    return null;
};

export default WebSocketComponent;