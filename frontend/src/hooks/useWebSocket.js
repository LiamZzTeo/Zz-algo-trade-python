import { useState, useEffect } from 'react';

const useWebSocket = () => {
  const [lastMessage, setLastMessage] = useState(null);
  const [connectionStatus, setConnectionStatus] = useState('disconnected');

  useEffect(() => {
    const handleWebSocketMessage = (event) => {
      if (event && event.detail) {
        setLastMessage(event.detail);
        setConnectionStatus('connected');
      }
    };

    // 监听 WebSocket 消息事件
    window.addEventListener('wsData', handleWebSocketMessage);

    return () => {
      window.removeEventListener('wsData', handleWebSocketMessage);
    };
  }, []);

  return {
    lastMessage,
    connectionStatus
  };
};

export default useWebSocket;