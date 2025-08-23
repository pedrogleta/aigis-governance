import React from 'react';
import { apiService } from '../services/api';
import ChatUI from '../components/ChatUI';
import { Navigate } from 'react-router-dom';

const ChatPage: React.FC = () => {
  const currentUser = apiService.getCurrentUser();
  if (!currentUser) return <Navigate to="/login" replace />;
  return <ChatUI />;
};

export default ChatPage;
