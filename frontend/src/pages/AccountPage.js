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
  const [error, setError] = useState(null);

  // 获取账户数据
  const fetchAccountData = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/account');
      const data = await response.json();
      if (data.success) {
        setAccountData(data.data);
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
      const data = await response.json();
      if (data.success) {
        setAssetsData(data.data);
      } else {
        setError('获取资产数据失败');
      }
    } catch (error) {
      console.error('获取资产数据错误:', error);
      setError('获取资产数据错误');
    }
  };

  // 加载所有数据
  const loadAllData = async () => {
    setLoading(true);
    await Promise.all([
      fetchAccountData(),
      fetchAssetsData()
    ]);
    setLoading(false);
  };

  useEffect(() => {
    // 初始加载
    loadAllData();

    // 添加定时刷新机制
    const intervalId = setInterval(() => {
      // 不需要每次都显示加载状态，只需静默更新数据
      Promise.all([
        fetchAccountData(),
        fetchAssetsData()
      ]);
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
      </Spin>
    </div>
  );
}

export default AccountPage;