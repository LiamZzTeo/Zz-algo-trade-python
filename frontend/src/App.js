import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import DataFetchComponent from './components/DataFetchComponent';
import HomePage from './pages/HomePage';
import AccountPage from './pages/AccountPage';
import PositionsPage from './pages/PositionsPage';
import StrategiesPage from './pages/StrategiesPage';
import './App.css';

function App() {
  return (
    <Router>
      <div className="App">
        {/* 数据获取组件不渲染任何UI，但会处理数据获取 */}
        <DataFetchComponent />
        
        <div className="main-nav">
          <div className="nav-brand">OKX 交易系统</div>
          <div className="nav-links">
            <Link to="/" className="nav-link">首页</Link>
            <Link to="/account" className="nav-link">账户</Link>
            <Link to="/positions" className="nav-link">持仓</Link>
            <Link to="/strategies" className="nav-link">策略</Link>
          </div>
        </div>
        
        <div className="main-content">
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/account" element={<AccountPage />} />
            <Route path="/positions" element={<PositionsPage />} />
            <Route path="/strategies" element={<StrategiesPage />} />
          </Routes>
        </div>
      </div>
    </Router>
  );
}

export default App;