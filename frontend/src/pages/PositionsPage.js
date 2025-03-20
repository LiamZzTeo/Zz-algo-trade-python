import React, { useState, useEffect } from 'react';

function PositionsPage() {
  const [positionsData, setPositionsData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // 修改事件名称从wsData为apiData
    const handleApiData = (event) => {
      if (event.detail && event.detail.type === 'update' && event.detail.data.positions) {
        setPositionsData(event.detail.data.positions);
        setLoading(false);
      }
    };
    
    window.addEventListener('apiData', handleApiData);
    
    // 初始加载时尝试从API获取数据
    const fetchInitialData = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/positions');
        if (!response.ok) {
          throw new Error(`HTTP错误: ${response.status}`);
        }
        const data = await response.json();
        if (data.success) {
          setPositionsData(data.data);
          setLoading(false);
        }
      } catch (error) {
        console.error('获取初始数据失败:', error);
      }
    };
    
    fetchInitialData();
    
    return () => {
      window.removeEventListener('apiData', handleApiData);
    };
  }, []);

  if (loading) {
    return <div className="loading">加载持仓数据中...</div>;
  }

  return (
    <div className="page-container">
      <h2 className="page-header">持仓信息</h2>
      
      {positionsData && positionsData.length > 0 ? (
        <div className="positions-table-container">
          <table className="positions-table">
            <thead>
              <tr>
                <th>合约</th>
                <th>方向</th>
                <th>杠杆</th>
                <th>持仓量</th>
                <th>开仓均价</th>
                <th>标记价格</th>
                <th>未实现盈亏</th>
              </tr>
            </thead>
            <tbody>
              {positionsData.map((position, index) => (
                <tr key={index} className={position.posSide === 'long' ? 'position-long' : 'position-short'}>
                  <td>{position.instId}</td>
                  <td>{position.posSide === 'long' ? '多' : '空'}</td>
                  <td>{position.lever}x</td>
                  <td>{position.pos}</td>
                  <td>{position.avgPx}</td>
                  <td>{position.markPx}</td>
                  <td className={parseFloat(position.upl) >= 0 ? 'profit' : 'loss'}>
                    {position.upl}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="no-positions">
          <p>暂无持仓数据</p>
        </div>
      )}
    </div>
  );
}

export default PositionsPage;