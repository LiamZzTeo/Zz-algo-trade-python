// 添加市场数据状态
const [marketData, setMarketData] = useState({});

// 添加获取市场数据的函数
const fetchMarketData = async (symbol = "BTC-USDT-SWAP") => {
  try {
    const response = await fetch(`http://localhost:8000/api/market-data?symbol=${symbol}`);
    if (!response.ok) {
      console.error('获取市场数据失败:', response.status);
      return;
    }
    
    const data = await response.json();
    if (data.success) {
      setMarketData(prevData => ({
        ...prevData,
        [symbol]: data.data
      }));
    } else {
      console.error('获取市场数据失败:', data.msg);
    }
  } catch (error) {
    console.error('获取市场数据错误:', error);
  }
};

// 在 useEffect 中调用
useEffect(() => {
  // 初始加载
  fetchAccountData();
  fetchPositionsData();
  fetchMarketData("BTC-USDT-SWAP");
  
  // 设置定时刷新
  const intervalId = setInterval(() => {
    fetchAccountData();
    fetchPositionsData();
    fetchMarketData("BTC-USDT-SWAP");
  }, 10000); // 每10秒刷新一次
  
  // 组件卸载时清除定时器
  return () => clearInterval(intervalId);
}, []);

// 在仪表盘中显示市场数据
// 在适当的位置添加如下代码
{marketData["BTC-USDT-SWAP"] && (
  <Card title="BTC-USDT-SWAP 市场数据" className="market-data-card">
    <Statistic
      title="最新价格"
      value={parseFloat(marketData["BTC-USDT-SWAP"].last)}
      precision={2}
      suffix="USDT"
    />
    <Statistic
      title="24小时涨跌幅"
      value={parseFloat(marketData["BTC-USDT-SWAP"].change24h) * 100}
      precision={2}
      valueStyle={{
        color: parseFloat(marketData["BTC-USDT-SWAP"].change24h) >= 0 ? '#3f8600' : '#cf1322',
      }}
      suffix="%"
      prefix={parseFloat(marketData["BTC-USDT-SWAP"].change24h) >= 0 ? '↑' : '↓'}
    />
    <div>24小时最高: {marketData["BTC-USDT-SWAP"].high24h}</div>
    <div>24小时最低: {marketData["BTC-USDT-SWAP"].low24h}</div>
    <div>24小时成交量: {marketData["BTC-USDT-SWAP"].volCcy24h}</div>
  </Card>
)}