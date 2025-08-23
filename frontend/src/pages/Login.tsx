import React from 'react';
import Auth from '../components/Auth';
import { useNavigate } from 'react-router-dom';

const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  return (
    <Auth
      onAuthSuccess={(user) => {
        if (user) navigate('/chat');
      }}
    />
  );
};

export default LoginPage;
