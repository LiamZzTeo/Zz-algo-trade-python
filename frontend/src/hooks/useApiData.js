import { useState, useEffect } from 'react';

const useApiData = () => {
  const [lastMessage, setLastMessage] = useState(null);
  const [connectionStatus, setConnectionStatus] = useState('connected');

  useEffect(() => {
    const handleApiData = (event) => {
      if (event && event.detail) {
        setLastMessage(event.detail);
        setConnectionStatus('connected');
      }
    };

    // 监听 API 数据事件
    window.addEventListener('apiData', handleApiData);

    return () => {
      window.removeEventListener('apiData', handleApiData);
    };
  }, []);

  return {
    lastMessage,
    connectionStatus
  };
};

export default useApiData;