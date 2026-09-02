import * as React from 'react';
import { HashRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AppProvider } from './context/AppContext';
import { installApiAuthInterceptor } from './services/api';
import LandingPage from './pages/LandingPage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import UsersPage from './pages/UsersPage';
import POSPage from './pages/POSPage';
import ShiftPage from './pages/ShiftPage';
import SettingsPage from './pages/SettingsPage';
import InventoryPage from './pages/InventoryPage';
import AlertsPage from './pages/AlertsPage';
import AdminDashboard from './pages/AdminDashboard';
import Layout from './components/Layout';

installApiAuthInterceptor();

const App: React.FC = () => {
  return (
    <AppProvider>
      <Router>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          
          {/* Protected Admin Routes */}
          <Route path="/users" element={
            <Layout userRole="ADMIN">
              <UsersPage />
            </Layout>
          } />
          <Route path="/dashboard" element={
            <Layout userRole="ADMIN">
              <AdminDashboard />
            </Layout>
          } />
          <Route path="/inventory" element={
            <Layout userRole="ADMIN">
              <InventoryPage />
            </Layout>
          } />
          <Route path="/alerts" element={
            <Layout userRole="ADMIN">
              <AlertsPage />
            </Layout>
          } />
          <Route path="/shifts" element={
            <Layout userRole="ADMIN">
              <ShiftPage />
            </Layout>
          } />
          <Route path="/settings" element={
            <Layout userRole="ADMIN">
              <SettingsPage />
            </Layout>
          } />
          
          {/* Protected POS Routes */}
          <Route path="/pos" element={
            <Layout userRole="CASHIER">
              <POSPage />
            </Layout>
          } />
          <Route path="/shifts-cashier" element={
            <Layout userRole="CASHIER">
              <ShiftPage />
            </Layout>
          } />
          
          {/* Fallback */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Router>
    </AppProvider>
  );
};

export default App;