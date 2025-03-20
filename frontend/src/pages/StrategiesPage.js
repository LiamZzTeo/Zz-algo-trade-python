import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import '../styles/StrategiesPage.css';

function StrategiesPage() {
  const [strategies, setStrategies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [newStrategy, setNewStrategy] = useState({
    strategy_id: '',
    name: '',
    description: '',
    parameters: {
      symbol: 'BTC-USDT-SWAP',
      fast_ma: 5,
      slow_ma: 20,
      position_size: 1
    },
    enabled: false
  });
  const [showForm, setShowForm] = useState(false);

  // 获取策略列表
  const fetchStrategies = async () => {
    try {
      setLoading(true);
      const response = await fetch('http://localhost:8000/api/strategies');
      if (!response.ok) {
        throw new Error(`HTTP错误: ${response.status}`);
      }
      const data = await response.json();
      if (data.success) {
        setStrategies(data.data);
      } else {
        setError(data.msg || '获取策略列表失败');
      }
    } catch (error) {
      console.error('获取策略列表错误:', error);
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  // 组件挂载时获取策略列表
  useEffect(() => {
    fetchStrategies();
    
    // 设置定时刷新
    const refreshInterval = setInterval(fetchStrategies, 5000);
    
    return () => {
      clearInterval(refreshInterval);
    };
  }, []);

  // 处理表单输入变化
  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setNewStrategy({
      ...newStrategy,
      [name]: value
    });
  };

  // 处理参数输入变化
  const handleParameterChange = (e) => {
    const { name, value } = e.target;
    setNewStrategy({
      ...newStrategy,
      parameters: {
        ...newStrategy.parameters,
        [name]: name === 'symbol' ? value : Number(value)
      }
    });
  };

  // 创建新策略
  const handleCreateStrategy = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch('http://localhost:8000/api/strategies', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(newStrategy)
      });
      
      if (!response.ok) {
        throw new Error(`HTTP错误: ${response.status}`);
      }
      
      const data = await response.json();
      if (data.success) {
        // 重置表单并刷新列表
        setNewStrategy({
          strategy_id: '',
          name: '',
          description: '',
          parameters: {
            symbol: 'BTC-USDT-SWAP',
            fast_ma: 5,
            slow_ma: 20,
            position_size: 1
          },
          enabled: false
        });
        setShowForm(false);
        fetchStrategies();
      } else {
        setError(data.msg || '创建策略失败');
      }
    } catch (error) {
      console.error('创建策略错误:', error);
      setError(error.message);
    }
  };

  // 启用/禁用策略
  const toggleStrategyStatus = async (strategyId, currentStatus) => {
    try {
      const endpoint = currentStatus 
        ? `http://localhost:8000/api/strategies/${strategyId}/disable`
        : `http://localhost:8000/api/strategies/${strategyId}/enable`;
        
      const response = await fetch(endpoint, {
        method: 'POST'
      });
      
      if (!response.ok) {
        throw new Error(`HTTP错误: ${response.status}`);
      }
      
      const data = await response.json();
      if (data.success) {
        fetchStrategies();
      } else {
        setError(data.msg || '操作失败');
      }
    } catch (error) {
      console.error('操作错误:', error);
      setError(error.message);
    }
  };

  // 删除策略
  const deleteStrategy = async (strategyId) => {
    if (!window.confirm('确定要删除此策略吗？')) {
      return;
    }
    
    try {
      const response = await fetch(`http://localhost:8000/api/strategies/${strategyId}`, {
        method: 'DELETE'
      });
      
      if (!response.ok) {
        throw new Error(`HTTP错误: ${response.status}`);
      }
      
      const data = await response.json();
      if (data.success) {
        fetchStrategies();
      } else {
        setError(data.msg || '删除策略失败');
      }
    } catch (error) {
      console.error('删除策略错误:', error);
      setError(error.message);
    }
  };

  if (loading && strategies.length === 0) {
    return <div className="loading">加载策略列表中...</div>;
  }

  return (
    <div className="page-container">
      <h2 className="page-header">算法交易策略</h2>
      
      {error && <div className="error-message">{error}</div>}
      
      <div className="strategies-actions">
        <button 
          className="btn btn-primary" 
          onClick={() => setShowForm(!showForm)}
        >
          {showForm ? '取消' : '创建新策略'}
        </button>
      </div>
      
      {showForm && (
        <div className="strategy-form-container">
          <h3>创建新策略</h3>
          <form onSubmit={handleCreateStrategy} className="strategy-form">
            <div className="form-group">
              <label>策略ID:</label>
              <input 
                type="text" 
                name="strategy_id" 
                value={newStrategy.strategy_id} 
                onChange={handleInputChange}
                required
              />
            </div>
            
            <div className="form-group">
              <label>策略名称:</label>
              <input 
                type="text" 
                name="name" 
                value={newStrategy.name} 
                onChange={handleInputChange}
                required
              />
            </div>
            
            <div className="form-group">
              <label>描述:</label>
              <textarea 
                name="description" 
                value={newStrategy.description} 
                onChange={handleInputChange}
              />
            </div>
            
            <h4>策略参数</h4>
            
            <div className="form-group">
              <label>交易品种:</label>
              <input 
                type="text" 
                name="symbol" 
                value={newStrategy.parameters.symbol} 
                onChange={handleParameterChange}
                required
              />
            </div>
            
            <div className="form-group">
              <label>快速均线周期:</label>
              <input 
                type="number" 
                name="fast_ma" 
                value={newStrategy.parameters.fast_ma} 
                onChange={handleParameterChange}
                required
              />
            </div>
            
            <div className="form-group">
              <label>慢速均线周期:</label>
              <input 
                type="number" 
                name="slow_ma" 
                value={newStrategy.parameters.slow_ma} 
                onChange={handleParameterChange}
                required
              />
            </div>
            
            <div className="form-group">
              <label>仓位大小:</label>
              <input 
                type="number" 
                name="position_size" 
                value={newStrategy.parameters.position_size} 
                onChange={handleParameterChange}
                required
              />
            </div>
            
            <div className="form-group checkbox">
              <label>
                <input 
                  type="checkbox" 
                  name="enabled" 
                  checked={newStrategy.enabled} 
                  onChange={(e) => setNewStrategy({...newStrategy, enabled: e.target.checked})}
                />
                创建后立即启用
              </label>
            </div>
            
            <div className="form-actions">
              <button type="submit" className="btn btn-success">创建策略</button>
              <button type="button" className="btn btn-secondary" onClick={() => setShowForm(false)}>取消</button>
            </div>
          </form>
        </div>
      )}
      
      <div className="strategies-list">
        {strategies.length > 0 ? (
          strategies.map((strategy) => (
            <div key={strategy.id} className={`strategy-card ${strategy.enabled ? 'active' : 'inactive'}`}>
              <div className="strategy-header">
                <h3>{strategy.id}</h3>
                <div className="strategy-status">
                  <span className={`status-indicator ${strategy.enabled ? 'active' : 'inactive'}`}>
                    {strategy.enabled ? '运行中' : '已停止'}
                  </span>
                </div>
              </div>
              
              <div className="strategy-details">
                <div className="strategy-params">
                  <h4>参数配置</h4>
                  <ul>
                    {Object.entries(strategy.config).map(([key, value]) => (
                      <li key={key}><strong>{key}:</strong> {value}</li>
                    ))}
                  </ul>
                </div>
                
                <div className="strategy-stats">
                  <h4>运行统计</h4>
                  <ul>
                    <li><strong>运行次数:</strong> {strategy.stats.runs}</li>
                    <li><strong>信号次数:</strong> {strategy.stats.signals}</li>
                    <li><strong>交易次数:</strong> {strategy.stats.trades}</li>
                    <li><strong>最后运行:</strong> {strategy.last_run ? new Date(strategy.last_run * 1000).toLocaleString() : '从未运行'}</li>
                  </ul>
                </div>
              </div>
              
              <div className="strategy-actions">
                <button 
                  className={`btn ${strategy.enabled ? 'btn-warning' : 'btn-success'}`}
                  onClick={() => toggleStrategyStatus(strategy.id, strategy.enabled)}
                >
                  {strategy.enabled ? '停止' : '启动'}
                </button>
                <button 
                  className="btn btn-danger"
                  onClick={() => deleteStrategy(strategy.id)}
                >
                  删除
                </button>
              </div>
            </div>
          ))
        ) : (
          <div className="no-strategies">
            <p>暂无交易策略</p>
            <p>点击"创建新策略"按钮开始添加</p>
          </div>
        )}
      </div>
    </div>
  );
}

export default StrategiesPage;