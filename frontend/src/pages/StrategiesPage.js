import React, { useState, useEffect } from 'react';
import { 
  Card, Table, Button, Modal, Form, Input, Select, Switch, 
  Tabs, message, Tooltip, Spin, Typography, Space, Tag, Divider, Statistic 
} from 'antd';
import { 
  PlusOutlined, EditOutlined, DeleteOutlined, PlayCircleOutlined, 
  PauseCircleOutlined, CodeOutlined, LineChartOutlined, SettingOutlined 
} from '@ant-design/icons';
import '../styles/StrategiesPage.css';

const { Title, Text } = Typography;
const { TabPane } = Tabs;
const { Option } = Select;
const { TextArea } = Input;

function StrategiesPage() {
  const [strategies, setStrategies] = useState([]);
  const [strategyTypes, setStrategyTypes] = useState([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingStrategy, setEditingStrategy] = useState(null);
  const [form] = Form.useForm();
  const [activeTab, setActiveTab] = useState('1');
  const [codeValue, setCodeValue] = useState('');
  const [accountData, setAccountData] = useState({});
  const [positionsData, setPositionsData] = useState([]);

  // 获取策略列表
  const fetchStrategies = async () => {
    setLoading(true);
    try {
      // 修改为正确的API路径，确保包含完整的URL
      const response = await fetch('http://localhost:8000/api/strategies');
      const data = await response.json();
      if (data.success) {
        setStrategies(data.data);
      } else {
        message.error('获取策略列表失败');
      }
    } catch (error) {
      console.error('获取策略列表错误:', error);
      message.error('获取策略列表错误');
    } finally {
      setLoading(false);
    }
  };

  // 获取账户数据
  const fetchAccountData = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/account');
      const data = await response.json();
      if (data.success) {
        setAccountData(data.data);
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
      }
    } catch (error) {
      console.error('获取持仓数据错误:', error);
    }
  };

  // 获取可用策略类型
  const fetchStrategyTypes = async () => {
    try {
      // 修改为正确的API路径，确保包含完整的URL
      const response = await fetch('http://localhost:8000/api/strategy-types');
      const data = await response.json();
      if (data.success) {
        setStrategyTypes(data.data);
      } else {
        message.error('获取策略类型失败');
      }
    } catch (error) {
      console.error('获取策略类型错误:', error);
      message.error('获取策略类型错误');
    }
  };

  // 定期刷新数据
  useEffect(() => {
    // 初始加载
    fetchStrategies();
    fetchStrategyTypes();
    fetchAccountData();
    fetchPositionsData();

    // 设置定时刷新
    const intervalId = setInterval(() => {
      fetchStrategies();
      fetchAccountData();
      fetchPositionsData();
    }, 10000); // 每10秒刷新一次

    // 组件卸载时清除定时器
    return () => clearInterval(intervalId);
  }, []);

  // 创建或更新策略
  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      
      // 如果是自定义策略，添加代码
      if (values.strategy_type === 'custom') {
        values.parameters = {
          ...values.parameters,
          code: codeValue
        };
      }
      
      const url = editingStrategy 
        ? `http://localhost:8000/api/strategies/${editingStrategy.id}` 
        : 'http://localhost:8000/api/strategies';
      
      const method = editingStrategy ? 'PUT' : 'POST';
      
      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(values)
      });
      
      const data = await response.json();
      
      if (data.success) {
        message.success(`${editingStrategy ? '更新' : '创建'}策略成功`);
        setModalVisible(false);
        fetchStrategies();
      } else {
        message.error(`${editingStrategy ? '更新' : '创建'}策略失败: ${data.msg || '未知错误'}`);
      }
    } catch (error) {
      console.error('表单提交错误:', error);
      message.error('表单验证失败，请检查输入');
    }
  };

  // 删除策略
  const handleDelete = async (strategyId) => {
    try {
      const response = await fetch(`http://localhost:8000/api/strategies/${strategyId}`, {
        method: 'DELETE'
      });
      
      const data = await response.json();
      
      if (data.success) {
        message.success('删除策略成功');
        fetchStrategies();
      } else {
        message.error(`删除策略失败: ${data.msg || '未知错误'}`);
      }
    } catch (error) {
      console.error('删除策略错误:', error);
      message.error('删除策略错误');
    }
  };

  // 启用/禁用策略
  const handleToggleEnabled = async (strategy) => {
    try {
      // 使用专门的启用/禁用端点
      const endpoint = strategy.enabled 
        ? `http://localhost:8000/api/strategies/${strategy.id}/disable`
        : `http://localhost:8000/api/strategies/${strategy.id}/enable`;
      
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        }
        // 添加策略参数到请求体
        // body: JSON.stringify({ parameters: strategy.parameters })
      });
      
      const data = await response.json();
      console.log(`${strategy.enabled ? '禁用' : '启用'}策略响应:`, data);
      
      if (data.success) {
        message.success(`${strategy.enabled ? '禁用' : '启用'}策略成功`);
        fetchStrategies();
      } else {
        message.error(`${strategy.enabled ? '禁用' : '启用'}策略失败: ${data.msg || '未知错误'}`);
      }
    } catch (error) {
      console.error('切换策略状态错误:', error);
      message.error('切换策略状态错误');
    }
  };

  // 打开编辑模态框
  const handleEdit = (strategy) => {
    setEditingStrategy(strategy);
    form.setFieldsValue({
      strategy_id: strategy.id,
      name: strategy.name,
      description: strategy.description,
      parameters: strategy.parameters,
      enabled: strategy.enabled,
      strategy_type: strategy.type.toLowerCase()
    });
    
    // 如果是自定义策略，设置代码
    if (strategy.type.toLowerCase() === 'custom') {
      setCodeValue(strategy.parameters.code || '');
    }
    
    setModalVisible(true);
    setActiveTab('1');
  };

  // 打开创建模态框
  const handleCreate = () => {
    setEditingStrategy(null);
    form.resetFields();
    setCodeValue('');
    setModalVisible(true);
    setActiveTab('1');
  };

  // 表格列定义
  const columns = [
    {
      title: '策略ID',
      dataIndex: 'id',
      key: 'id',
      width: 120,
    },
    {
      title: '名称',
      dataIndex: 'name',
      key: 'name',
      render: (text, record) => (
        <Space>
          <Text strong>{text}</Text>
          <Tag color={getStrategyTypeColor(record.type)}>{record.type}</Tag>
        </Space>
      )
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
    },
    {
      title: '参数',
      dataIndex: 'parameters',
      key: 'parameters',
      render: (params) => (
        <Tooltip 
          title={
            <div>
              {Object.entries(params).map(([key, value]) => (
                <div key={key}>
                  <strong>{key}:</strong> {typeof value === 'object' ? JSON.stringify(value) : value}
                </div>
              ))}
            </div>
          }
        >
          <Button type="link" icon={<SettingOutlined />}>查看参数</Button>
        </Tooltip>
      )
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
      title: '统计',
      dataIndex: 'stats',
      key: 'stats',
      render: (stats) => (
        <Space>
          <Tooltip title="运行次数">
            <Tag color="blue">运行: {stats?.runs || 0}</Tag>
          </Tooltip>
          <Tooltip title="信号次数">
            <Tag color="purple">信号: {stats?.signals || 0}</Tag>
          </Tooltip>
          <Tooltip title="交易次数">
            <Tag color="orange">交易: {stats?.trades || 0}</Tag>
          </Tooltip>
        </Space>
      )
    },
    {
      title: '操作',
      key: 'action',
      width: 200,
      render: (_, record) => (
        <Space size="small">
          <Button 
            type="primary" 
            icon={record.enabled ? <PauseCircleOutlined /> : <PlayCircleOutlined />}
            onClick={() => handleToggleEnabled(record)}
            size="small"
          >
            {record.enabled ? '停止' : '启动'}
          </Button>
          <Button 
            icon={<EditOutlined />} 
            onClick={() => handleEdit(record)}
            size="small"
          >
            编辑
          </Button>
          <Button 
            danger 
            icon={<DeleteOutlined />} 
            onClick={() => handleDelete(record.id)}
            size="small"
          >
            删除
          </Button>
        </Space>
      ),
    },
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

  // 策略类型变更处理
  const handleStrategyTypeChange = (value) => {
    // 找到对应的策略类型
    const selectedType = strategyTypes.find(type => type.type === value);
    
    if (selectedType) {
      // 设置默认参数
      form.setFieldsValue({
        parameters: selectedType.default_parameters
      });
      
      // 如果是自定义策略，设置默认代码
      if (value === 'custom') {
        setCodeValue(selectedType.default_parameters.code || '');
      }
    }
  };

  // 渲染参数输入控件
  const renderParameterInputs = () => {
    const parameters = form.getFieldValue('parameters') || {};
    
    return (
      <div className="parameters-container">
        {Object.entries(parameters).map(([key, value]) => {
          // 跳过代码参数，它在代码编辑器中编辑
          if (key === 'code') return null;
          
          return (
            <Form.Item 
              key={key} 
              label={key} 
              className="parameter-item"
            >
              {renderParameterInput(key, value)}
            </Form.Item>
          );
        })}
      </div>
    );
  };
  
  // 根据参数类型渲染不同的输入控件
  // 在 StrategiesPage 组件中添加状态
  const [instruments, setInstruments] = useState([]);
  
  // 添加获取可交易产品的函数
  const fetchInstruments = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/instruments');
      if (!response.ok) {
        console.error('获取可交易产品失败:', response.status);
        return;
      }
      
      const data = await response.json();
      if (data.success) {
        setInstruments(data.data);
        console.log(`获取到 ${data.data.length} 个交易品种`);
      } else {
        console.error('获取可交易产品失败:', data.msg);
      }
    } catch (error) {
      console.error('获取可交易产品错误:', error);
    }
  };
  
  // 在 useEffect 中调用
  useEffect(() => {
    // 初始加载
    fetchStrategies();
    fetchStrategyTypes();
    fetchAccountData();
    fetchPositionsData();
    fetchInstruments(); // 添加这一行
  
    // 设置定时刷新
    const intervalId = setInterval(() => {
      fetchStrategies();
      fetchAccountData();
      fetchPositionsData();
    }, 10000); // 每10秒刷新一次
  
    // 组件卸载时清除定时器
    return () => clearInterval(intervalId);
  }, []);
  
  // 修改 renderParameterInput 函数中的交易品种选择部分
  const renderParameterInput = (key, value) => {
    const handleChange = (newValue) => {
      const currentParams = form.getFieldValue('parameters') || {};
      form.setFieldsValue({
        parameters: {
          ...currentParams,
          [key]: newValue
        }
      });
    };
    
    // 如果是交易品种参数，从API获取的产品列表中提供选择
    if (typeof value === 'string' && (key.toLowerCase().includes('symbol') || key.toLowerCase().includes('instid'))) {
      // 从API获取的产品列表中提取可用品种
      const availableSymbols = instruments.length > 0 
        ? [...new Set(instruments.map(inst => inst.instId))]  // 使用Set去重
        : [];
      
      return (
        <Select 
          defaultValue={value} 
          onChange={handleChange}
          showSearch
          style={{ width: '100%' }}
          placeholder="选择交易品种"
          optionFilterProp="children"
          filterOption={(input, option) =>
            option.children.toLowerCase().indexOf(input.toLowerCase()) >= 0
          }
        >
          {availableSymbols.length > 0 ? (
            availableSymbols.map(symbol => (
              <Option key={symbol} value={symbol}>{symbol}</Option>
            ))
          ) : (
            // 如果没有获取到产品数据，提供默认选项
            <>
              <Option value="BTC-USDT-SWAP">BTC-USDT-SWAP</Option>
              <Option value="ETH-USDT-SWAP">ETH-USDT-SWAP</Option>
              <Option value="LTC-USDT-SWAP">LTC-USDT-SWAP</Option>
              <Option value="EOS-USDT-SWAP">EOS-USDT-SWAP</Option>
            </>
          )}
        </Select>
      );
    } else if (typeof value === 'number') {
      return (
        <Input 
          type="number" 
          defaultValue={value} 
          onChange={(e) => handleChange(parseFloat(e.target.value))}
        />
      );
    } else if (typeof value === 'boolean') {
      return (
        <Select 
          defaultValue={value} 
          onChange={handleChange}
        >
          <Option value={true}>是</Option>
          <Option value={false}>否</Option>
        </Select>
      );
    } else {
      return (
        <Input 
          defaultValue={value} 
          onChange={(e) => handleChange(e.target.value)}
        />
      );
    }
  };

  // 渲染代码编辑器
  const renderCodeEditor = () => {
    // 如果没有安装 react-monaco-editor，使用普通文本框
    // 注释提到未安装react-monaco-editor，但package.json中包含此依赖
    // 可以考虑实际使用Monaco编辑器或移除此依赖
    return (
      <div className="code-editor-container">
        <TextArea
          value={codeValue}
          onChange={(e) => setCodeValue(e.target.value)}
          placeholder="在这里编写策略代码..."
          autoSize={{ minRows: 15, maxRows: 30 }}
          className="code-editor"
        />
        <div className="code-editor-tips">
          <p>策略代码必须包含 execute_strategy 函数，该函数接收以下参数：</p>
          <ul>
            <li>market_data: 市场数据</li>
            <li>positions: 当前持仓</li>
            <li>account: 账户信息</li>
            <li>parameters: 策略参数</li>
            <li>logger: 日志记录器</li>
          </ul>
          <p>函数应返回交易信号对象或 None</p>
        </div>
      </div>
    );
  };

  return (
    <div className="strategies-page">
      <div className="page-header">
        <Title level={2}>策略管理</Title>
        <Space>
          {/* 显示账户余额信息 */}
          {accountData && accountData.totalEq && (
            <Card className="account-info-card">
              <Statistic
                title="账户总资产"
                value={parseFloat(accountData.totalEq)}
                precision={2}
                suffix="USDT"
              />
            </Card>
          )}
          <Button 
            type="primary" 
            icon={<PlusOutlined />} 
            onClick={handleCreate}
            className="create-button"
          >
            创建策略
          </Button>
        </Space>
      </div>
      
      <Divider />
      
      {/* 显示持仓信息 */}
      {positionsData && positionsData.length > 0 && (
        <div className="positions-overview">
          <Title level={4}>当前持仓</Title>
          <div className="positions-list">
            {positionsData.map((position, index) => (
              <Card key={index} className="position-card">
                <Statistic
                  title={position.instId}
                  value={parseFloat(position.pos)}
                  precision={4}
                  valueStyle={{ 
                    color: parseFloat(position.pos) > 0 ? '#3f8600' : 
                           parseFloat(position.pos) < 0 ? '#cf1322' : '#8c8c8c' 
                  }}
                  suffix={
                    parseFloat(position.pos) > 0 ? '多' : 
                    parseFloat(position.pos) < 0 ? '空' : '无'
                  }
                />
                <div>开仓价: {position.avgPx}</div>
                <div>未实现盈亏: {position.upl}</div>
              </Card>
            ))}
          </div>
        </div>
      )}
      
      <Card className="strategies-card" bordered={false}>
        <Spin spinning={loading}>
          <Table 
            columns={columns} 
            dataSource={strategies} 
            rowKey="id"
            pagination={{ pageSize: 10 }}
            className="strategies-table"
          />
        </Spin>
      </Card>
      
      <Modal
        title={editingStrategy ? '编辑策略' : '创建策略'}
        visible={modalVisible}
        onCancel={() => setModalVisible(false)}
        footer={[
          <Button key="cancel" onClick={() => setModalVisible(false)}>
            取消
          </Button>,
          <Button key="submit" type="primary" onClick={handleSubmit}>
            保存
          </Button>
        ]}
        width={800}
        destroyOnClose
      >
        <Tabs activeKey={activeTab} onChange={setActiveTab}>
          <TabPane tab="基本信息" key="1">
            <Form
              form={form}
              layout="vertical"
              initialValues={{
                enabled: false,
                parameters: {}
              }}
            >
              <Form.Item
                name="strategy_id"
                label="策略ID"
                rules={[{ required: true, message: '请输入策略ID' }]}
              >
                <Input placeholder="输入唯一的策略ID" disabled={!!editingStrategy} />
              </Form.Item>
              
              <Form.Item
                name="name"
                label="策略名称"
                rules={[{ required: true, message: '请输入策略名称' }]}
              >
                <Input placeholder="输入策略名称" />
              </Form.Item>
              
              <Form.Item
                name="description"
                label="策略描述"
              >
                <TextArea placeholder="输入策略描述" rows={3} />
              </Form.Item>
              
              <Form.Item
                name="strategy_type"
                label="策略类型"
                rules={[{ required: true, message: '请选择策略类型' }]}
              >
                <Select 
                  placeholder="选择策略类型" 
                  onChange={handleStrategyTypeChange}
                  disabled={!!editingStrategy}
                >
                  {strategyTypes.map(type => (
                    <Option key={type.type} value={type.type}>
                      {type.name}
                    </Option>
                  ))}
                </Select>
              </Form.Item>
              
              <Form.Item
                name="enabled"
                label="启用策略"
                valuePropName="checked"
              >
                <Switch />
              </Form.Item>
              
              <Form.Item
                name="parameters"
                hidden
              >
                <Input />
              </Form.Item>
            </Form>
          </TabPane>
          
          <TabPane tab="参数配置" key="2">
            {renderParameterInputs()}
          </TabPane>
          
          {form.getFieldValue('strategy_type') === 'custom' && (
            <TabPane tab="策略代码" key="3">
              {renderCodeEditor()}
            </TabPane>
          )}
        </Tabs>
      </Modal>
    </div>
  );
}

export default StrategiesPage;

// 在启用策略的函数中添加错误处理和日志
const enableStrategy = async (strategyId) => {
  try {
    setLoading(true);
    const response = await fetch(`http://localhost:8000/api/strategies/${strategyId}/enable`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      }
    });
    
    const data = await response.json();
    console.log('启用策略响应:', data);
    
    if (data.success) {
      message.success('策略启用成功');
      fetchStrategies(); // 刷新策略列表
    } else {
      message.error(`启用策略失败: ${data.msg || '未知错误'}`);
    }
  } catch (error) {
    console.error('启用策略出错:', error);
    message.error(`启用策略出错: ${error.message}`);
  } finally {
    setLoading(false);
  }
};