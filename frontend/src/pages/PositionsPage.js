import React, { useState, useEffect } from 'react';

function PositionsPage() {
  const [positionsData, setPositionsData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const handleWebSocketData = (event) => {
      if (event.detail && event.detail.type === 'update' && event.detail.data.positions) {
        setPositionsData(event.detail.data.positions);
        setLoading(false);
      }
    };
    
    window.addEventListener('wsData', handleWebSocketData);
    
    return () => {
      window.removeEventListener('wsData', handleWebSocketData);
    };
  }, []);

  if (loading) {
    return <div className="loading">加载持仓数据中...</div>;
  }

  return (
    <div className="page-container">
      <h2 className="page-header">持仓信息</h2>
      
      <div className="positions-info">
        {positionsData && positionsData.length > 0 ? (
          <div className="positions-grid">
            {positionsData.map((position, index) => (
              <div className="position-card" key={index}>
                <h4>{position.instId}</h4>
                <div className="position-details">
                  <p>方向: {position.posSide}</p>
                  <p>数量: {position.pos}</p>
                  <p>开仓价: {position.avgPx}</p>
                  <p>标记价: {position.markPx}</p>
                  <p>未实现盈亏: {position.upl}</p>
                  <p>保证金: {position.margin}</p>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div>暂无持仓</div>
        )}
      </div>
    </div>
  );
}

export default PositionsPage;