import React, { useState, useEffect } from 'react';
import { Card, Form, Button, Select, InputNumber, Table, Spin, message, Tabs, Statistic, Row, Col, Divider } from 'antd';
import { ArrowUpOutlined, ArrowDownOutlined } from '@ant-design/icons';
import ReactECharts from 'echarts-for-react';
import axios from 'axios';
import moment from 'moment';

const { TabPane } = Tabs;
const { Option } = Select;

const BacktestPanel = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [strategies, setStrategies] = useState([]);
  const [instruments, setInstruments] = useState([]);
  const [backtestResult, setBacktestResult] = useState(null);
  const [activeTab, setActiveTab] = useState('1');

  // 获取策略列表
  useEffect(() => {
    const fetchStrategies = async () => {
      try {
        const response = await axios.get('http://localhost:8000/api/strategies');
        if (response.data.success) {
          setStrategies(response.data.data);
        }
      } catch (error) {
        console.error('获取策略列表失败:', error);
        message.error('获取策略列表失败');
      }
    };

    const fetchInstruments = async () => {
      try {
        const response = await axios.get('http://localhost:8000/api/instruments');
        if (response.data.success) {
          // 只保留永续合约
          const swapInstruments = response.data.data.filter(
            item => item.instType === 'SWAP'
          );
          setInstruments(swapInstruments);
        }
      } catch (error) {
        console.error('获取交易品种失败:', error);
        message.error('获取交易品种失败');
      }
    };

    fetchStrategies();
    fetchInstruments();
  }, []);

  // 运行回测
  const handleRunBacktest = async (values) => {
    setLoading(true);
    try {
      console.log('发送回测请求:', values);
      const response = await axios.post('http://localhost:8000/api/backtest', {
        strategy_id: values.strategy_id,
        symbol: values.symbol,
        bar: values.bar || '1m',
        initial_capital: parseFloat(values.initial_capital) || 10000
      });
      console.log('回测响应:', response.data);
      if (response.data.success) {
        setBacktestResult(response.data.data);
        message.success('回测完成');
        setActiveTab('2'); // 切换到结果标签页
      } else {
        message.error(`回测失败: ${response.data.msg}`);
      }
    } catch (error) {
      console.error('回测请求失败:', error);
      message.error('回测请求失败');
    } finally {
      setLoading(false);
    }
  };

  // 生成权益曲线图表选项
  const getEquityCurveOptions = () => {
    if (!backtestResult || !backtestResult.equity_curve) {
      return {};
    }

    const timestamps = backtestResult.equity_curve.map(point => 
      moment(point.timestamp).format('YYYY-MM-DD HH:mm:ss')
    );
    const equityValues = backtestResult.equity_curve.map(point => point.equity);

    return {
      title: {
        text: '回测权益曲线',
        left: 'center'
      },
      tooltip: {
        trigger: 'axis',
        formatter: function (params) {
          const time = params[0].axisValue;
          const value = params[0].data;
          return `${time}<br/>权益: ${value.toFixed(2)}`;
        }
      },
      xAxis: {
        type: 'category',
        data: timestamps,
        axisLabel: {
          rotate: 45,
          interval: Math.floor(timestamps.length / 10)
        }
      },
      yAxis: {
        type: 'value',
        name: '权益',
        axisLabel: {
          formatter: '{value}'
        }
      },
      series: [{
        name: '权益',
        type: 'line',
        data: equityValues,
        markPoint: {
          data: [
            { type: 'max', name: '最大值' },
            { type: 'min', name: '最小值' }
          ]
        }
      }],
      dataZoom: [
        {
          type: 'inside',
          start: 0,
          end: 100
        },
        {
          start: 0,
          end: 100
        }
      ],
      grid: {
        left: '3%',
        right: '4%',
        bottom: '15%',
        containLabel: true
      }
    };
  };

  // 交易记录表格列
  const tradeColumns = [
    {
      title: '时间',
      dataIndex: 'timestamp',
      key: 'timestamp',
      render: (timestamp) => moment(timestamp).format('YYYY-MM-DD HH:mm:ss')
    },
    {
      title: '交易对',
      dataIndex: 'symbol',
      key: 'symbol'
    },
    {
      title: '操作',
      dataIndex: 'action',
      key: 'action',
      render: (action) => {
        switch (action) {
          case 'buy':
          case 'long':
            return <span style={{ color: 'green' }}>开多</span>;
          case 'sell':
          case 'short':
            return <span style={{ color: 'red' }}>开空</span>;
          case 'close_long':
            return <span style={{ color: 'orange' }}>平多</span>;
          case 'close_short':
            return <span style={{ color: 'blue' }}>平空</span>;
          default:
            return action;
        }
      }
    },
    {
      title: '价格',
      dataIndex: 'price',
      key: 'price',
      render: (price) => price.toFixed(2)
    },
    {
      title: '数量',
      dataIndex: 'size',
      key: 'size'
    },
    {
      title: '盈亏',
      dataIndex: 'profit',
      key: 'profit',
      render: (profit) => {
        if (!profit) return '-';
        const color = profit > 0 ? 'green' : 'red';
        return <span style={{ color }}>{profit.toFixed(2)}</span>;
      }
    }
  ];

  return (
    <div className="backtest-panel">
      <Tabs activeKey={activeTab} onChange={setActiveTab}>
        <TabPane tab="回测设置" key="1">
          <Card title="回测参数">
            <Form
              form={form}
              layout="vertical"
              onFinish={handleRunBacktest}
              initialValues={{
                bar: '1m',
                initial_capital: 10000
              }}
            >
              <Form.Item
                name="strategy_id"
                label="选择策略"
                rules={[{ required: true, message: '请选择策略' }]}
              >
                <Select placeholder="选择要回测的策略">
                  {strategies.map(strategy => (
                    <Option key={strategy.id} value={strategy.id}>
                      {strategy.name}
                    </Option>
                  ))}
                </Select>
              </Form.Item>

              <Form.Item
                name="symbol"
                label="交易品种"
                rules={[{ required: true, message: '请选择交易品种' }]}
              >
                <Select
                  placeholder="选择交易品种"
                  showSearch
                  filterOption={(input, option) =>
                    option.children.toLowerCase().indexOf(input.toLowerCase()) >= 0
                  }
                >
                  {instruments.map(instrument => (
                    <Option key={instrument.instId} value={instrument.instId}>
                      {instrument.instId}
                    </Option>
                  ))}
                </Select>
              </Form.Item>

              <Form.Item
                name="bar"
                label="K线周期"
                rules={[{ required: true, message: '请选择K线周期' }]}
              >
                <Select placeholder="选择K线周期">
                  <Option value="1m">1分钟</Option>
                  <Option value="5m">5分钟</Option>
                  <Option value="15m">15分钟</Option>
                  <Option value="1H">1小时</Option>
                  <Option value="4H">4小时</Option>
                  <Option value="1D">1天</Option>
                </Select>
              </Form.Item>

              <Form.Item
                name="initial_capital"
                label="初始资金"
                rules={[{ required: true, message: '请输入初始资金' }]}
              >
                <InputNumber
                  style={{ width: '100%' }}
                  min={1}
                  step={1000}
                  formatter={value => `$ ${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
                  parser={value => value.replace(/\$\s?|(,*)/g, '')}
                />
              </Form.Item>

              <Form.Item>
                <Button type="primary" htmlType="submit" loading={loading} block>
                  运行回测
                </Button>
              </Form.Item>
            </Form>
          </Card>
        </TabPane>

        <TabPane tab="回测结果" key="2" disabled={!backtestResult}>
          {backtestResult ? (
            <div>
              <Card title="回测概览">
                <Row gutter={16}>
                  <Col span={8}>
                    <Statistic
                      title="交易品种"
                      value={backtestResult.symbol}
                    />
                  </Col>
                  <Col span={8}>
                    <Statistic
                      title="K线周期"
                      value={backtestResult.bar}
                    />
                  </Col>
                  <Col span={8}>
                    <Statistic
                      title="回测时间段"
                      value={`${backtestResult.start_time} 至 ${backtestResult.end_time}`}
                    />
                  </Col>
                </Row>

                <Divider />

                <Row gutter={16}>
                  <Col span={6}>
                    <Statistic
                      title="初始资金"
                      value={backtestResult.initial_capital}
                      precision={2}
                      prefix="$"
                    />
                  </Col>
                  <Col span={6}>
                    <Statistic
                      title="最终权益"
                      value={backtestResult.final_equity}
                      precision={2}
                      prefix="$"
                    />
                  </Col>
                  <Col span={6}>
                    <Statistic
                      title="总收益率"
                      value={backtestResult.total_return}
                      precision={2}
                      prefix={backtestResult.total_return >= 0 ? <ArrowUpOutlined /> : <ArrowDownOutlined />}
                      suffix="%"
                      valueStyle={{ color: backtestResult.total_return >= 0 ? '#3f8600' : '#cf1322' }}
                    />
                  </Col>
                  <Col span={6}>
                    <Statistic
                      title="最大回撤"
                      value={backtestResult.max_drawdown}
                      precision={2}
                      suffix="%"
                      valueStyle={{ color: '#cf1322' }}
                    />
                  </Col>
                </Row>

                <Divider />

                <Row gutter={16}>
                  <Col span={6}>
                    <Statistic
                      title="总交易次数"
                      value={backtestResult.total_trades}
                    />
                  </Col>
                  <Col span={6}>
                    <Statistic
                      title="盈利交易"
                      value={backtestResult.winning_trades}
                      valueStyle={{ color: '#3f8600' }}
                    />
                  </Col>
                  <Col span={6}>
                    <Statistic
                      title="亏损交易"
                      value={backtestResult.losing_trades}
                      valueStyle={{ color: '#cf1322' }}
                    />
                  </Col>
                  <Col span={6}>
                    <Statistic
                      title="胜率"
                      value={backtestResult.win_rate}
                      precision={2}
                      suffix="%"
                      valueStyle={{ color: backtestResult.win_rate >= 50 ? '#3f8600' : '#cf1322' }}
                    />
                  </Col>
                </Row>

                <Divider />

                <Row gutter={16}>
                  <Col span={8}>
                    <Statistic
                      title="总盈亏"
                      value={backtestResult.total_profit}
                      precision={2}
                      prefix="$"
                      valueStyle={{ color: backtestResult.total_profit >= 0 ? '#3f8600' : '#cf1322' }}
                    />
                  </Col>
                  <Col span={8}>
                    <Statistic
                      title="最大单笔盈利"
                      value={backtestResult.max_profit_trade}
                      precision={2}
                      prefix="$"
                      valueStyle={{ color: '#3f8600' }}
                    />
                  </Col>
                  <Col span={8}>
                    <Statistic
                      title="最大单笔亏损"
                      value={backtestResult.max_loss_trade}
                      precision={2}
                      prefix="$"
                      valueStyle={{ color: '#cf1322' }}
                    />
                  </Col>
                </Row>

                <Divider />

                <Row gutter={16}>
                  <Col span={24}>
                    <Statistic
                      title="夏普比率"
                      value={backtestResult.sharpe_ratio}
                      precision={2}
                      valueStyle={{ color: backtestResult.sharpe_ratio >= 1 ? '#3f8600' : '#cf1322' }}
                    />
                  </Col>
                </Row>
              </Card>

              <Card title="权益曲线" style={{ marginTop: 16 }}>
                <ReactECharts 
                  option={getEquityCurveOptions()} 
                  style={{ height: 400 }} 
                  notMerge={true}
                />
              </Card>

              <Card title="交易记录" style={{ marginTop: 16 }}>
                <Table
                  dataSource={backtestResult.trades}
                  columns={tradeColumns}
                  rowKey={(record, index) => index}
                  pagination={{ pageSize: 10 }}
                  scroll={{ x: 'max-content' }}
                />
              </Card>
            </div>
          ) : (
            <Spin tip="加载中...">
              <div style={{ height: 400 }}></div>
            </Spin>
          )}
        </TabPane>
      </Tabs>
    </div>
  );
};

export default BacktestPanel;