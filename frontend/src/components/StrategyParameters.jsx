import React, { useEffect, useState } from 'react';
import { Form, Input, InputNumber, Select, Divider, Typography, Button, Space } from 'antd';
import { PlusOutlined, MinusCircleOutlined } from '@ant-design/icons';
import '../styles/StrategyParameters.css';

const { Title, Text } = Typography;
const { Option } = Select;

const StrategyParameters = ({ form }) => {
  const [parameters, setParameters] = useState({});

  useEffect(() => {
    // 监听表单参数变化
    const params = form.getFieldValue('parameters') || {};
    setParameters(params);

    // 订阅表单字段变化
    const unsubscribe = form.getFieldInstance(['parameters'])?.props?.onChange?.subscribe?.(value => {
      setParameters(value || {});
    });

    return () => {
      if (unsubscribe) unsubscribe();
    };
  }, [form]);

  const handleParamChange = (key, value) => {
    const newParams = { ...parameters, [key]: value };
    form.setFieldsValue({ parameters: newParams });
    setParameters(newParams);
  };

  const renderParamInput = (key, value) => {
    // 根据值类型渲染不同的输入控件
    if (typeof value === 'number') {
      return (
        <InputNumber
          value={value}
          onChange={(val) => handleParamChange(key, val)}
          className="param-input"
        />
      );
    } else if (typeof value === 'boolean') {
      return (
        <Select
          value={value}
          onChange={(val) => handleParamChange(key, val)}
          className="param-input"
        >
          <Option value={true}>是</Option>
          <Option value={false}>否</Option>
        </Select>
      );
    } else if (typeof value === 'string' && (key.toLowerCase().includes('symbol') || key.toLowerCase().includes('instid'))) {
      return (
        <Select
          value={value}
          onChange={(val) => handleParamChange(key, val)}
          className="param-input"
        >
          <Option value="BTC-USDT-SWAP">BTC-USDT-SWAP</Option>
          <Option value="ETH-USDT-SWAP">ETH-USDT-SWAP</Option>
          <Option value="LTC-USDT-SWAP">LTC-USDT-SWAP</Option>
          <Option value="EOS-USDT-SWAP">EOS-USDT-SWAP</Option>
        </Select>
      );
    } else {
      return (
        <Input
          value={value}
          onChange={(e) => handleParamChange(key, e.target.value)}
          className="param-input"
        />
      );
    }
  };

  return (
    <div className="strategy-parameters">
      <Form.Item
        name="parameters"
        hidden
      >
        <Input />
      </Form.Item>

      <div className="parameters-list">
        {Object.entries(parameters).map(([key, value]) => {
          // 跳过代码参数，它在代码编辑器中编辑
          if (key === 'code') return null;
          
          return (
            <div key={key} className="parameter-item">
              <Text strong className="param-label">{key}:</Text>
              {renderParamInput(key, value)}
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default StrategyParameters;