import React, { useState } from 'react';
import { Layout, Menu } from 'antd';
import { Link, useLocation } from 'react-router-dom';
import { DashboardOutlined, CodeOutlined, UserOutlined, ExperimentOutlined } from '@ant-design/icons';

const { Header } = Layout;

const Navbar = () => {
  const location = useLocation();
  const [current, setCurrent] = useState(location.pathname);

  const handleClick = (e) => {
    setCurrent(e.key);
  };

  // 在菜单项中添加回测页面
  const menuItems = [
    {
      key: '/',
      icon: <DashboardOutlined />,
      label: '仪表盘',
    },
    {
      key: '/strategies',
      icon: <CodeOutlined />,
      label: '策略管理',
    },
    {
      key: '/backtest',
      icon: <ExperimentOutlined />,
      label: '策略回测',
    },
    {
      key: '/account',
      icon: <UserOutlined />,
      label: '账户信息',
    },
  ];

  return (
    <Header className="app-header" style={{ display: 'flex', alignItems: 'center' }}>
      <div className="logo" style={{ marginRight: '20px', color: 'white', fontSize: '18px', fontWeight: 'bold' }}>
        AlgoSysTest
      </div>
      <Menu
        theme="dark"
        mode="horizontal"
        selectedKeys={[current]}
        onClick={handleClick}
        style={{ flex: 1, minWidth: 0 }}
        items={menuItems.map(item => ({
          ...item,
          label: <Link to={item.key}>{item.label}</Link>
        }))}
      />
    </Header>
  );
};

export default Navbar;