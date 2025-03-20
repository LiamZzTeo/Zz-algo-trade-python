import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import WebSocketComponent from './components/WebSocketComponent';
import HomePage from './pages/HomePage';
import AccountPage from './pages/AccountPage';
import PositionsPage from './pages/PositionsPage';
import './App.css';

function App() {
  return (
    <Router>
      <div className="App">
        {/* WebSocket 组件不渲染任何 UI，但会处理连接 */}
        <WebSocketComponent />
        
        <div className="main-nav">
          <div className="nav-brand">OKX 交易系统</div>
          <div className="nav-links">
            <Link to="/" className="nav-link">首页</Link>
            <Link to="/account" className="nav-link">账户</Link>
            <Link to="/positions" className="nav-link">持仓</Link>
            {/* 移除了交易历史的导航链接 */}
          </div>
        </div>
        
        <div className="main-content">
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/account" element={<AccountPage />} />
            <Route path="/positions" element={<PositionsPage />} />
            {/* 移除了交易历史的路由 */}
          </Routes>
        </div>
      </div>
    </Router>
  );
}

export default App;
