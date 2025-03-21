import React from 'react';
import { Layout, Menu } from 'antd';
import { Link, useLocation } from 'react-router-dom';
import { DashboardOutlined, AppstoreOutlined, UserOutlined } from '@ant-design/icons';
import '../styles/Navbar.css';

const { Header } = Layout;

const Navbar = () => {
  const location = useLocation();
  
  return (
    <Header className="navbar">
      <div className="logo">AlgoSysTest</div>
      <Menu
        theme="dark"
        mode="horizontal"
        selectedKeys={[location.pathname]}
        items={[
          {
            key: '/',
            icon: <DashboardOutlined />,
            label: <Link to="/">仪表盘</Link>,
          },
          {
            key: '/strategies',
            icon: <AppstoreOutlined />,
            label: <Link to="/strategies">策略管理</Link>,
          },
          {
            key: '/account',
            icon: <UserOutlined />,
            label: <Link to="/account">账户信息</Link>,
          },
        ]}
      />
    </Header>
  );
};

export default Navbar;