import { useEffect, useRef } from 'react';

const DataFetchComponent = () => {
    const fetchIntervalRef = useRef<NodeJS.Timeout | null>(null);
    const isActiveRef = useRef<boolean>(true);
    const fetchDelayMs = 500; // 0.5秒更新一次
    
    // API服务器配置
    const API_SERVER = {
        protocol: window.location.protocol,
        host: window.location.hostname,
        port: '8000',
        path: 'api/data'
    };

    const getApiUrl = () => {
        return `${API_SERVER.protocol}//${API_SERVER.host}:${API_SERVER.port}/${API_SERVER.path}`;
    };

    useEffect(() => {
        const fetchData = async () => {
            if (!isActiveRef.current) return;
            
            try {
                const response = await fetch(getApiUrl());
                if (!response.ok) {
                    throw new Error(`HTTP错误: ${response.status}`);
                }
                
                const data = await response.json();
                
                // 分发数据更新事件
                window.dispatchEvent(new CustomEvent('apiData', { detail: data }));
                
            } catch (error) {
                console.error('获取数据失败:', error);
            }
        };

        const startFetching = () => {
            // 立即获取一次数据
            fetchData();
            
            // 设置定期获取数据的间隔
            fetchIntervalRef.current = setInterval(fetchData, fetchDelayMs);
        };

        // 开始获取数据
        startFetching();

        // 组件卸载时清理
        return () => {
            isActiveRef.current = false;
            if (fetchIntervalRef.current) {
                clearInterval(fetchIntervalRef.current);
                fetchIntervalRef.current = null;
            }
        };
    }, []);

    return null;
};

export default DataFetchComponent;