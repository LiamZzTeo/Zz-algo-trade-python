import React from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import { Layout } from 'antd';
import './App.css';

// 导入组件
import Navbar from './components/Navbar';
import Dashboard from './pages/Dashboard';
import StrategiesPage from './pages/StrategiesPage';
import AccountPage from './pages/AccountPage';

const { Content } = Layout;

function App() {
  return (
    <Router>
      <Layout className="app-layout">
        <Navbar />
        <Content className="app-content">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/strategies" element={<StrategiesPage />} />
            <Route path="/account" element={<AccountPage />} />
          </Routes>
        </Content>
      </Layout>
    </Router>
  );
}

export default App;