import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Statistic, Typography, Divider, Spin, Table, Tag } from 'antd';
import { 
  DollarCircleOutlined, 
  ArrowUpOutlined, 
  ArrowDownOutlined 
} from '@ant-design/icons';
import '../styles/AccountPage.css';

const { Title } = Typography;

function AccountPage() {
  const [loading, setLoading] = useState(true);
  const [accountData, setAccountData] = useState({});
  const [assetsData, setAssetsData] = useState([]);
  const [positionsData, setPositionsData] = useState([]); // Add positions state
  const [error, setError] = useState(null);

  // 获取账户数据
  const fetchAccountData = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/account');
      const data = await response.json();
      if (data.success) {
        setAccountData(data.data);
        setLoading(false);
      } else {
        setError('获取账户数据失败');
      }
    } catch (error) {
      console.error('获取账户数据错误:', error);
      setError('获取账户数据错误');
    }
  };

  // 获取资产数据
  const fetchAssetsData = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/assets');
      if (!response.ok) {
        console.error('获取资产数据失败:', response.status);
        // 如果资产接口失败，尝试使用账户接口
        fetchAccountData();
        return;
      }
      
      const data = await response.json();
      if (data.success) {
        setAccountData(data.data);
        setLoading(false);
      } else {
        console.error('获取资产数据失败:', data.msg);
      }
    } catch (error) {
      console.error('获取资产数据错误:', error);
    }
  };
  
  // 添加获取持仓数据的函数
  const fetchPositionsData = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/positions');
      if (!response.ok) {
        console.error('获取持仓数据失败:', response.status);
        return;
      }
      
      const data = await response.json();
      if (data.success) {
        setPositionsData(data.data || []);
      } else {
        console.error('获取持仓数据失败:', data.msg);
      }
    } catch (error) {
      console.error('获取持仓数据错误:', error);
    }
  };
  
  // 在 useEffect 中调用
  useEffect(() => {
    // 初始加载
    fetchAssetsData();
    fetchPositionsData();
    
    // 设置定时刷新
    const intervalId = setInterval(() => {
      fetchAssetsData();
      fetchPositionsData();
    }, 10000); // 每10秒刷新一次
    
    // 组件卸载时清除定时器
    return () => clearInterval(intervalId);
  }, []);

  return (
    <div className="page-container">
      <Spin spinning={loading}>
        <Title level={2}>账户信息</Title>
        <Divider />
        
        <Row gutter={[16, 16]}>
          <Col span={24}>
            <Card>
              <Statistic
                title="总资产"
                value={accountData.totalEq ? parseFloat(accountData.totalEq) : 0}
                precision={2}
                prefix={<DollarCircleOutlined />}
                suffix="USDT"
                valueStyle={{ color: '#1890ff', fontSize: '32px' }}
              />
            </Card>
          </Col>
        </Row>
        
        <Divider orientation="left">资产明细</Divider>
        
        <Row gutter={[16, 16]}>
          {accountData.details && accountData.details.map((item, index) => (
            <Col xs={24} sm={12} md={8} lg={6} key={index}>
              <Card hoverable>
                <Statistic
                  title={`${item.ccy} 余额`}
                  value={parseFloat(item.cashBal)}
                  precision={4}
                  valueStyle={{ color: '#3f8600' }}
                />
                <Divider style={{ margin: '12px 0' }} />
                <Row>
                  <Col span={12}>
                    <Statistic
                      title="可用"
                      value={parseFloat(item.availBal)}
                      precision={4}
                      valueStyle={{ fontSize: '14px' }}
                    />
                  </Col>
                  <Col span={12}>
                    <Statistic
                      title="冻结"
                      value={parseFloat(item.frozenBal)}
                      precision={4}
                      valueStyle={{ fontSize: '14px' }}
                    />
                  </Col>
                </Row>
              </Card>
            </Col>
          ))}
          {(!accountData.details || accountData.details.length === 0) && !loading && (
            <Col span={24}>
              <Card>
                <div style={{ textAlign: 'center', padding: '20px' }}>
                  暂无资产明细
                </div>
              </Card>
            </Col>
          )}
        </Row>
        
        {/* 添加持仓信息展示 */}
        <Divider orientation="left">持仓信息</Divider>
        
        <Row gutter={[16, 16]}>
          {positionsData && positionsData.length > 0 ? (
            <Col span={24}>
              <Table 
                dataSource={positionsData}
                rowKey={(record) => record.posId}
                pagination={false}
                columns={[
                  {
                    title: '产品',
                    dataIndex: 'instId',
                    key: 'instId',
                  },
                  // 在 Table 组件的 columns 定义中修改 posSide 的渲染逻辑
                  {
                    title: '方向',
                    dataIndex: 'posSide',
                    key: 'posSide',
                    render: (text, record) => {
                      // 判断持仓方向：结合 posSide 和 pos 值
                      let direction = '';
                      let color = '';
                      
                      if (record.posSide === 'long') {
                        direction = '多';
                        color = 'green';
                      } else if (record.posSide === 'short') {
                        direction = '空';
                        color = 'red';
                      } else if (record.posSide === 'net') {
                        // 净持仓模式下，根据 pos 值判断方向
                        if (parseFloat(record.pos) > 0) {
                          direction = '多';
                          color = 'green';
                        } else if (parseFloat(record.pos) < 0) {
                          direction = '空';
                          color = 'red';
                        } else {
                          direction = '无';
                          color = 'gray';
                        }
                      } else {
                        // 如果没有明确的方向，根据 pos 值判断
                        if (parseFloat(record.pos) > 0) {
                          direction = '多';
                          color = 'green';
                        } else if (parseFloat(record.pos) < 0) {
                          direction = '空';
                          color = 'red';
                        } else {
                          direction = '无';
                          color = 'gray';
                        }
                      }
                      
                      return (
                        <Tag color={color}>
                          {direction}
                        </Tag>
                      );
                    },
                  },
                  {
                    title: '持仓量',
                    dataIndex: 'pos',
                    key: 'pos',
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
                    render: (text) => (
                      <span style={{ color: parseFloat(text) >= 0 ? 'green' : 'red' }}>
                        {text}
                      </span>
                    ),
                  },
                ]}
              />
            </Col>
          ) : (
            <Col span={24}>
              <Card>
                <div style={{ textAlign: 'center', padding: '20px' }}>
                  暂无持仓信息
                </div>
              </Card>
            </Col>
          )}
        </Row>
      </Spin>
    </div>
  );
}

export default AccountPage;