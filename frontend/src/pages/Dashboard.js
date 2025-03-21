import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Statistic, Typography, Divider, Spin, Table, Tag } from 'antd';
import { 
  LineChartOutlined, 
  DollarCircleOutlined, 
  RiseOutlined, 
  FallOutlined,
  ArrowUpOutlined,
  ArrowDownOutlined
} from '@ant-design/icons';
import '../styles/Dashboard.css';

const { Title } = Typography;

// 在 Dashboard 组件中添加当日盈亏计算
function Dashboard() {
  const [loading, setLoading] = useState(true);
  const [accountData, setAccountData] = useState({});
  const [positionsData, setPositionsData] = useState([]);
  const [strategiesData, setStrategiesData] = useState([]);
  const [marketData, setMarketData] = useState({});
  const [error, setError] = useState(null);
  // 添加当日盈亏状态
  const [dailyPnL, setDailyPnL] = useState(0);

  // 获取账户数据
  const fetchAccountData = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/account');
      const data = await response.json();
      if (data.success) {
        setAccountData(data.data);
        // 如果后端返回了当日盈亏数据，直接使用
        if (data.data.dailyPnL) {
          setDailyPnL(parseFloat(data.data.dailyPnL));
        }
      }
    } catch (error) {
      console.error('获取账户数据错误:', error);
    }
  };

  // 获取持仓数据
  const fetchPositionsData = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/positions');
      const data = await response.json();
      if (data.success) {
        setPositionsData(data.data);
        
        // 如果后端没有提供当日盈产，从持仓数据计算
        if (!accountData.dailyPnL) {
          // 计算当日盈亏：所有持仓的未实现盈亏总和
          const totalPnL = data.data.reduce((sum, position) => {
            // 假设持仓数据中有 unrealizedPnL 字段
            return sum + (parseFloat(position.unrealizedPnL) || 0);
          }, 0);
          setDailyPnL(totalPnL);
        }
      }
    } catch (error) {
      console.error('获取持仓数据错误:', error);
    }
  };

  // 获取策略数据
  const fetchStrategiesData = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/strategies');
      const data = await response.json();
      if (data.success) {
        setStrategiesData(data.data);
      } else {
        setError('获取策略数据失败');
      }
    } catch (error) {
      console.error('获取策略数据错误:', error);
      setError('获取策略数据错误');
    }
  };

  // 获取市场数据
  const fetchMarketData = async () => {
    try {
      // 获取BTC市场数据作为示例
      const response = await fetch('http://localhost:8000/api/market-data?symbol=BTC-USDT-SWAP');
      const data = await response.json();
      if (data.success) {
        setMarketData(data.data);
      } else {
        setError('获取市场数据失败');
      }
    } catch (error) {
      console.error('获取市场数据错误:', error);
      setError('获取市场数据错误');
    }
  };

  // 加载所有数据
  const loadAllData = async () => {
    setLoading(true);
    await Promise.all([
      fetchAccountData(),
      fetchPositionsData(),
      fetchStrategiesData(),
      fetchMarketData()
    ]);
    setLoading(false);
  };

  useEffect(() => {
    // 初始加载
    loadAllData();

    // 设置定时刷新
    const intervalId = setInterval(() => {
      loadAllData();
    }, 10000); // 每10秒刷新一次

    // 组件卸载时清除定时器
    return () => clearInterval(intervalId);
  }, []);

  // 计算活跃策略数量
  const activeStrategiesCount = strategiesData.filter(s => s.enabled).length;

  // 持仓数据表格列
  const positionsColumns = [
    {
      title: '交易品种',
      dataIndex: 'instId',
      key: 'instId',
    },
    {
      title: '持仓量',
      dataIndex: 'pos',
      key: 'pos',
      render: (text, record) => {
        const posValue = parseFloat(text);
        return (
          <span style={{ color: posValue > 0 ? '#3f8600' : (posValue < 0 ? '#cf1322' : 'inherit') }}>
            {posValue > 0 ? '+' : ''}{posValue}
          </span>
        );
      }
    },
    {
      title: '开仓均价',
      dataIndex: 'avgPx',
      key: 'avgPx',
    },
    {
      title: '未实现盈亏',
      dataIndex: 'upl',
      key: 'upl',
      render: (text) => {
        const uplValue = parseFloat(text);
        return (
          <span style={{ color: uplValue >= 0 ? '#3f8600' : '#cf1322' }}>
            {uplValue >= 0 ? '+' : ''}{uplValue.toFixed(2)}
          </span>
        );
      }
    }
  ];

  // 策略数据表格列
  const strategiesColumns = [
    {
      title: '策略名称',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '类型',
      dataIndex: 'type',
      key: 'type',
      render: (text) => <Tag color={getStrategyTypeColor(text)}>{text}</Tag>
    },
    {
      title: '状态',
      dataIndex: 'enabled',
      key: 'enabled',
      render: (enabled) => (
        <Tag color={enabled ? 'green' : 'red'}>
          {enabled ? '运行中' : '已停止'}
        </Tag>
      )
    },
    {
      title: '信号数',
      dataIndex: ['stats', 'signals'],
      key: 'signals',
      render: (text) => text || 0
    }
  ];

  // 根据策略类型获取颜色
  const getStrategyTypeColor = (type) => {
    const typeColors = {
      'MomentumStrategy': 'green',
      'GridStrategy': 'blue',
      'MACrossStrategy': 'purple',
      'CustomStrategy': 'orange',
      'default': 'default'
    };
    
    return typeColors[type] || typeColors.default;
  };

  return (
    <div className="dashboard-container">
      <Spin spinning={loading}>
        <div className="dashboard-header">
          <Title level={2}>交易系统仪表盘</Title>
        </div>
        
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={12} md={6}>
            <Card className="stat-card">
              <Statistic
                title="账户总资产"
                value={accountData.totalEq ? parseFloat(accountData.totalEq) : 0}
                precision={2}
                prefix={<DollarCircleOutlined />}
                suffix="USDT"
              />
            </Card>
          </Col>
          
          <Col xs={24} sm={12} md={6}>
            <Card className="stat-card">
              <Statistic
                title="当日盈亏"
                value={dailyPnL}
                precision={2}
                valueStyle={{ color: dailyPnL >= 0 ? '#3f8600' : '#cf1322' }}
                prefix={dailyPnL >= 0 ? <ArrowUpOutlined /> : <ArrowDownOutlined />}
                suffix="USDT"
              />
            </Card>
          </Col>
          
          <Col xs={24} sm={12} md={6}>
            <Card className="stat-card">
              <Statistic
                title="活跃策略数"
                value={activeStrategiesCount}
                prefix={<LineChartOutlined />}
                valueStyle={{ color: '#1890ff' }}
              />
            </Card>
          </Col>
          
          <Col xs={24} sm={12} md={6}>
            <Card className="stat-card">
              <Statistic
                title="持仓数量"
                value={positionsData.length}
                prefix={<RiseOutlined />}
                valueStyle={{ color: positionsData.length > 0 ? '#722ed1' : '#8c8c8c' }}
              />
            </Card>
          </Col>
        </Row>
        
        <Row gutter={[16, 16]} style={{ marginTop: '16px' }}>
          <Col xs={24} md={12}>
            <Card title="市场行情" className="market-card">
              {marketData.last ? (
                <>
                  <Statistic
                    title={marketData.symbol || 'BTC-USDT-SWAP'}
                    value={parseFloat(marketData.last)}
                    precision={2}
                    valueStyle={{ 
                      color: marketData.change >= 0 ? '#3f8600' : '#cf1322',
                      fontSize: '24px'
                    }}
                    prefix={marketData.change >= 0 ? <ArrowUpOutlined /> : <ArrowDownOutlined />}
                    suffix="USDT"
                  />
                  <div style={{ marginTop: '10px' }}>
                    <Row>
                      <Col span={8}>
                        <Statistic 
                          title="24h高" 
                          value={parseFloat(marketData.high24h || 0)} 
                          precision={2}
                          valueStyle={{ fontSize: '14px' }}
                        />
                      </Col>
                      <Col span={8}>
                        <Statistic 
                          title="24h低" 
                          value={parseFloat(marketData.low24h || 0)} 
                          precision={2}
                          valueStyle={{ fontSize: '14px' }}
                        />
                      </Col>
                      <Col span={8}>
                        <Statistic 
                          title="24h量" 
                          value={parseFloat(marketData.vol24h || 0)} 
                          precision={0}
                          valueStyle={{ fontSize: '14px' }}
                        />
                      </Col>
                    </Row>
                  </div>
                </>
              ) : (
                <div className="no-data">暂无市场数据</div>
              )}
            </Card>
          </Col>
          
          <Col xs={24} md={12}>
            <Card title="策略概览" className="strategy-card">
              {strategiesData.length > 0 ? (
                <Table 
                  dataSource={strategiesData.slice(0, 5)} 
                  columns={strategiesColumns} 
                  pagination={false}
                  size="small"
                  rowKey="id"
                />
              ) : (
                <div className="no-data">暂无策略数据</div>
              )}
            </Card>
          </Col>
        </Row>
        
        <Row gutter={[16, 16]} style={{ marginTop: '16px' }}>
          <Col span={24}>
            <Card title="当前持仓" className="positions-card">
              {positionsData.length > 0 ? (
                <Table 
                  dataSource={positionsData} 
                  columns={positionsColumns} 
                  pagination={false}
                  size="small"
                  rowKey="posId"
                />
              ) : (
                <div className="no-data">暂无持仓数据</div>
              )}
            </Card>
          </Col>
        </Row>
      </Spin>
    </div>
  );
}

export default Dashboard;