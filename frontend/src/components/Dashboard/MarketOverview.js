// ... 现有代码 ...

// 修改市场行情的涨跌标志逻辑
const renderPriceChange = (price, prevPrice) => {
  if (!price || !prevPrice) return null;
  
  const change = ((price - prevPrice) / prevPrice) * 100;
  const isPositive = change >= 0;
  
  return (
    <span className={`price-change ${isPositive ? 'positive' : 'negative'}`}>
      {isPositive ? <ArrowUpOutlined /> : <ArrowDownOutlined />}
      {Math.abs(change).toFixed(2)}%
    </span>
  );
};

// ... 现有代码 ...

// 在渲染市场数据时使用
{marketData.map((item, index) => (
  <div key={index} className="market-item">
    <div className="symbol">{item.symbol}</div>
    <div className="price">{parseFloat(item.last).toFixed(2)}</div>
    {renderPriceChange(parseFloat(item.last), parseFloat(item.prevClose))}
  </div>
))}

// ... 现有代码 ...