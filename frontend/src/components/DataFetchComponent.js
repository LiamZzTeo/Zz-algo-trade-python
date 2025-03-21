import { useEffect, useRef } from 'react';

const DataFetchComponent = () => {
    const fetchIntervalRef = useRef(null);
    const isActiveRef = useRef(true);
    const fetchDelayMs = 500; // 0.5秒更新一次
    
    // API服务器配置
    const API_SERVER = {
        protocol: 'http',
        host: 'localhost',
        port: '8000',
        path: 'api/data'
    };

    const getApiUrl = () => {
        return `${API_SERVER.protocol}://${API_SERVER.host}:${API_SERVER.port}/${API_SERVER.path}`;
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
                window.dispatchEvent(new CustomEvent('apiData', { 
                    detail: data 
                }));
                
            } catch (error) {
                console.error('获取数据失败:', error);
            }
        };

        const startFetching = () => {
            // 立即获取一次数据
            fetchData();
            
            // 设置定期获取数据的间隔
            if (fetchIntervalRef.current) {
                clearInterval(fetchIntervalRef.current);
            }
            
            fetchIntervalRef.current = setInterval(fetchData, fetchDelayMs);
            console.log('数据获取定时器已启动，间隔:', fetchDelayMs, 'ms');
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