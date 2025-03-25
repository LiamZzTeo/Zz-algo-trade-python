// ... 现有代码 ...

// 修改回测概览部分，确保正确显示交易品种和K线周期
// 回测概览组件
const BacktestOverview = ({ result }) => {
  if (!result || !result.overview) return null;
  
  const { overview } = result;
  
  // 添加调试信息
  console.log("回测概览数据:", overview);
  console.log("交易品种:", overview.symbol, typeof overview.symbol);
  console.log("K线周期:", overview.timeframe, typeof overview.timeframe);
  
  return (
    <Card title="回测概览" className="backtest-overview-card">
      <Row gutter={[16, 16]}>
        <Col span={8}>
          <Statistic title="交易品种" value={overview.symbol || "未知"} />
        </Col>
        <Col span={8}>
          <Statistic title="K线周期" value={overview.timeframe || "未知"} />
        </Col>
        <Col span={8}>
          <Statistic title="回测区间" value={`${overview.start_time} 至 ${overview.end_time}`} />
        </Col>
        {/* 其他统计信息 */}
      </Row>
    </Card>
  );
};

// ... 现有代码 ...