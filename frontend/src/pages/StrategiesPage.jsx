import React, { useState, useEffect } from 'react';
import { 
  Card, Table, Button, Modal, Form, Input, Select, Switch, 
  Tabs, message, Tooltip, Spin, Typography, Space, Tag, Divider 
} from 'antd';
import { 
  PlusOutlined, EditOutlined, DeleteOutlined, PlayCircleOutlined, 
  PauseCircleOutlined, CodeOutlined, LineChartOutlined, SettingOutlined 
} from '@ant-design/icons';
import CodeEditor from '../components/CodeEditor';
import StrategyParameters from '../components/StrategyParameters';
import '../styles/StrategiesPage.css';

const { Title, Text } = Typography;
const { TabPane } = Tabs;
const { Option } = Select;

const StrategiesPage = () => {
  const [strategies, setStrategies] = useState([]);
  const [strategyTypes, setStrategyTypes] = useState([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingStrategy, setEditingStrategy] = useState(null);
  const [form] = Form.useForm();
  const [activeTab, setActiveTab] = useState('1');
  const [codeValue, setCodeValue] = useState('');

  // 获取策略列表
  const fetchStrategies = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/strategies');
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

  // 获取可用策略类型
  const fetchStrategyTypes = async () => {
    try {
      const response = await fetch('/api/strategy-types');
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

  useEffect(() => {
    fetchStrategies();
    fetchStrategyTypes();
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
        ? `/api/strategies/${editingStrategy.id}` 
        : '/api/strategies';
      
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
      const response = await fetch(`/api/strategies/${strategyId}`, {
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
      const response = await fetch(`/api/strategies/${strategy.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          ...strategy,
          enabled: !strategy.enabled
        })
      });
      
      const data = await response.json();
      
      if (data.success) {
        message.success(`${!strategy.enabled ? '启用' : '禁用'}策略成功`);
        fetchStrategies();
      } else {
        message.error(`${!strategy.enabled ? '启用' : '禁用'}策略失败: ${data.msg || '未知错误'}`);
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
            <Tag color="blue">运行: {stats.runs}</Tag>
          </Tooltip>
          <Tooltip title="信号次数">
            <Tag color="purple">信号: {stats.signals}</Tag>
          </Tooltip>
          <Tooltip title="交易次数">
            <Tag color="orange">交易: {stats.trades}</Tag>
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

  return (
    <div className="strategies-page">
      <div className="page-header">
        <Title level={2}>策略管理</Title>
        <Button 
          type="primary" 
          icon={<PlusOutlined />} 
          onClick={handleCreate}
          className="create-button"
        >
          创建策略
        </Button>
      </div>
      
      <Divider />
      
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
                <Input.TextArea placeholder="输入策略描述" rows={3} />
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
            </Form>
          </TabPane>
          
          <TabPane tab="参数配置" key="2">
            <StrategyParameters form={form} />
          </TabPane>
          
          {form.getFieldValue('strategy_type') === 'custom' && (
            <TabPane tab="策略代码" key="3">
              <CodeEditor
                value={codeValue}
                onChange={setCodeValue}
                language="python"
                height="400px"
              />
            </TabPane>
          )}
        </Tabs>
      </Modal>
    </div>
  );
};

export default StrategiesPage;