import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User as UserIcon, Database, BarChart3 } from 'lucide-react';
import { cn } from '../lib/utils';
import {
  apiService,
  type UserConnection,
  type UserConnectionCreate,
} from '../services/api';
import type { ChatResponse, StreamingMessage } from '../services/api';
import {
  StreamingMessageComponent,
  StreamingTextComponent,
} from './MessageComponents';
import ConnectionsSidebar from './ConnectionsSidebar';
import ModelSidebar from './ModelSidebar';

interface Message {
  id: string;
  type: 'user' | 'agent';
  content: string;
  timestamp: Date;
  plots?: string[];
  isStreaming?: boolean;
  error?: string;
  startTime?: number;
  endTime?: number;
  streamingMessages?: StreamingMessage[];
}

const ChatUI: React.FC = () => {
  const [currentUser, setCurrentUser] = useState<any | null>(
    apiService.getCurrentUser(),
  );
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      type: 'agent',
      content:
        "Hello! I'm your AI Data Science Assistant. I can help you analyze BigQuery datasets and create visualizations. What would you like to know about your data?",
      timestamp: new Date(),
    },
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<
    'connected' | 'disconnected' | 'checking'
  >('checking');
  const [connectionsOpen, setConnectionsOpen] = useState(false);
  const [modelsOpen, setModelsOpen] = useState(false);
  const [connections, setConnections] = useState<UserConnection[]>([]);
  const [selectedConnection, setSelectedConnection] =
    useState<UserConnection | null>(apiService.getSelectedConnection());
  const [selectedCustomIds, setSelectedCustomIds] = useState<number[]>(
    apiService.getSelectedConnectionIds?.() || [],
  );
  const [formState, setFormState] = useState<UserConnectionCreate>({
    name: '',
    db_type: 'postgres',
  });
  const [editingId, setEditingId] = useState<number | null>(null);
  const [testingId, setTestingId] = useState<number | null>(null);
  // sidebar handled in separate component
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const audioContextRef = useRef<AudioContext | null>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const playNotificationSound = () => {
    try {
      if (!audioContextRef.current) {
        audioContextRef.current = new (window.AudioContext ||
          (window as any).webkitAudioContext)();
      }
      const oscillator = audioContextRef.current.createOscillator();
      const gainNode = audioContextRef.current.createGain();
      oscillator.connect(gainNode);
      gainNode.connect(audioContextRef.current.destination);
      oscillator.frequency.setValueAtTime(
        800,
        audioContextRef.current.currentTime,
      );
      oscillator.frequency.setValueAtTime(
        600,
        audioContextRef.current.currentTime + 0.1,
      );
      gainNode.gain.setValueAtTime(0.1, audioContextRef.current.currentTime);
      gainNode.gain.exponentialRampToValueAtTime(
        0.01,
        audioContextRef.current.currentTime + 0.2,
      );
      oscillator.start(audioContextRef.current.currentTime);
      oscillator.stop(audioContextRef.current.currentTime + 0.2);
    } catch (error) {
      console.warn('Could not play notification sound:', error);
    }
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    checkConnection();
    createThread();
    if (apiService.getToken()) refreshConnections();
  }, []);

  // sidebar animation state is handled by ConnectionsSidebar

  const checkConnection = async () => {
    setConnectionStatus('checking');
    try {
      const isHealthy = await apiService.getHealth();
      const isBigQueryConnected = await apiService.checkBigQueryConnection();
      setConnectionStatus(
        isHealthy && isBigQueryConnected ? 'connected' : 'disconnected',
      );
    } catch {
      setConnectionStatus('disconnected');
    }
  };

  const createThread = async () => {
    try {
      await apiService.ensureThread();
    } catch (error) {
      console.error('Error creating chat thread:', error);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputValue.trim() || isLoading) return;
    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: inputValue,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    const agentMessageId = (Date.now() + 1).toString();
    const streamingAgentMessage: Message = {
      id: agentMessageId,
      type: 'agent',
      content: 'Typing...',
      timestamp: new Date(),
      isStreaming: true,
      startTime: Date.now(),
      streamingMessages: [],
    };

    setMessages((prev) => [...prev, streamingAgentMessage]);
    playNotificationSound();

    try {
      await apiService.sendMessageStreaming(
        inputValue,
        (chunk: StreamingMessage) => {
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === agentMessageId
                ? {
                    ...msg,
                    streamingMessages: [
                      ...(msg.streamingMessages || []),
                      chunk,
                    ],
                    content:
                      chunk.type === 'text' && chunk.partial
                        ? msg.content === 'Typing...'
                          ? chunk.content
                          : msg.content + chunk.content
                        : msg.content,
                    isStreaming: chunk.type === 'text' ? chunk.partial : true,
                  }
                : msg,
            ),
          );
        },
        (finalResponse: ChatResponse) => {
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === agentMessageId
                ? {
                    ...msg,
                    content: finalResponse.content,
                    plots: finalResponse.plots,
                    isStreaming: false,
                    endTime: Date.now(),
                  }
                : msg,
            ),
          );
        },
        (error: string) => {
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === agentMessageId
                ? {
                    ...msg,
                    content: `Sorry, I encountered an error while processing your request: ${error}`,
                    isStreaming: false,
                    error,
                  }
                : msg,
            ),
          );
        },
      );
    } catch (error) {
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === agentMessageId
            ? {
                ...msg,
                content:
                  'Sorry, I encountered an error while processing your request. Please check your connection and try again.',
                isStreaming: false,
              }
            : msg,
        ),
      );
    } finally {
      setIsLoading(false);
    }
  };

  const handleRetry = async (messageId: string) => {
    const messageIndex = messages.findIndex((msg) => msg.id === messageId);
    if (messageIndex === -1) return;
    let userMessageIndex = -1;
    for (let i = messageIndex - 1; i >= 0; i--)
      if (messages[i].type === 'user') {
        userMessageIndex = i;
        break;
      }
    if (userMessageIndex === -1) return;
    const userMessage = messages[userMessageIndex];
    setMessages((prev) => [
      ...prev.slice(0, messageIndex),
      ...prev.slice(messageIndex + 1),
    ]);
    const agentMessageId = (Date.now() + 1).toString();
    const streamingAgentMessage: Message = {
      id: agentMessageId,
      type: 'agent',
      content: 'Typing...',
      timestamp: new Date(),
      isStreaming: true,
      startTime: Date.now(),
      streamingMessages: [],
    };
    setMessages((prev) => [...prev, streamingAgentMessage]);
    playNotificationSound();
    try {
      await apiService.sendMessageStreaming(
        userMessage.content,
        (chunk: StreamingMessage) => {
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === agentMessageId
                ? {
                    ...msg,
                    streamingMessages: [
                      ...(msg.streamingMessages || []),
                      chunk,
                    ],
                    isStreaming: chunk.type === 'text' ? chunk.partial : true,
                  }
                : msg,
            ),
          );
        },
        (finalResponse: ChatResponse) => {
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === agentMessageId
                ? {
                    ...msg,
                    content: finalResponse.content,
                    plots: finalResponse.plots,
                    isStreaming: false,
                    endTime: Date.now(),
                  }
                : msg,
            ),
          );
        },
        (error: string) => {
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === agentMessageId
                ? {
                    ...msg,
                    content: `Sorry, I encountered an error while processing your request: ${error}`,
                    isStreaming: false,
                    error,
                  }
                : msg,
            ),
          );
        },
      );
    } catch (error) {
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === agentMessageId
            ? {
                ...msg,
                content:
                  'Sorry, I encountered an error while processing your request. Please check your connection and try again.',
                isStreaming: false,
                error: 'Connection error',
              }
            : msg,
        ),
      );
    }
  };

  const formatTimestamp = (date: Date) =>
    date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

  const getConnectionStatusColor = () => {
    switch (connectionStatus) {
      case 'connected':
        return 'bg-green-500';
      case 'disconnected':
        return 'bg-red-500';
      case 'checking':
        return 'bg-yellow-500';
      default:
        return 'bg-gray-500';
    }
  };

  const getConnectionStatusText = () => {
    switch (connectionStatus) {
      case 'connected':
        // Show the selected connection name when connected; otherwise prompt to choose one
        return selectedConnection ? (
          <span className="connected text-green-200 font-medium">
            Connected to:{' '}
            <span className="text-white font-semibold ml-1 truncate">
              {selectedConnection.name}
            </span>
          </span>
        ) : selectedCustomIds.length > 0 ? (
          <span className="connected text-green-200 font-medium">
            Custom:{' '}
            <span className="text-white font-semibold ml-1">
              {selectedCustomIds.length} selected
            </span>
          </span>
        ) : (
          <span className="text-gray-300">Choose a connection</span>
        );
      case 'disconnected':
        return <span className="disconnected">Disconnected</span>;
      case 'checking':
        return <span className="connecting">Checking connection...</span>;
      default:
        return 'Unknown status';
    }
  };

  const refreshConnections = async () => {
    try {
      const list = await apiService.listConnections();
      setConnections(list);
      // Re-hydrate selected connection reference from list (in case it changed)
      const sel = apiService.getSelectedConnection();
      if (sel) {
        const refreshed = list.find((c) => c.id === sel.id) || null;
        setSelectedConnection(refreshed);
        apiService.setSelectedConnection(refreshed);
      }
    } catch (e) {
      console.warn('Failed to load connections', e);
    }
  };

  const handleSelectConnection = async (conn: UserConnection | null) => {
    // Selecting a non-custom clears custom multi-selection
    if (conn && conn.db_type !== 'custom') {
      if (selectedCustomIds.length > 0) {
        setSelectedCustomIds([]);
        apiService.setSelectedConnectionIds([]);
      }
    }
    setSelectedConnection(conn);
    apiService.setSelectedConnection(conn);
    try {
      if (conn?.id != null) {
        await apiService.updateThreadConnection(conn.id);
      }
    } catch (e) {
      console.warn('Failed to update thread connection', e);
    }
  };

  const handleToggleCustom = async (id: number) => {
    // Toggling a custom connection should deselect any non-custom selection
    if (selectedConnection && selectedConnection.db_type !== 'custom') {
      setSelectedConnection(null);
      apiService.setSelectedConnection(null);
    }

    setSelectedCustomIds((prev) => {
      const next = prev.includes(id)
        ? prev.filter((x) => x !== id)
        : [...prev, id];
      apiService.setSelectedConnectionIds(next);
      // Push update to backend with the list (if empty, do nothing)
      if (next.length > 0) {
        apiService
          .updateThreadConnections(next)
          .catch((e) => console.warn('Failed to update multi connections', e));
      }
      return next;
    });
  };

  const handleSaveConnection = async () => {
    try {
      if (editingId) {
        await apiService.updateConnection(editingId, formState);
        setEditingId(null);
      } else {
        await apiService.createConnection(formState);
      }
      setFormState({ name: '', db_type: 'postgres' });
      await refreshConnections();
    } catch (e) {
      alert((e as Error).message);
    }
  };

  const handleEdit = (conn: UserConnection) => {
    setEditingId(conn.id);
    setFormState({
      name: conn.name,
      db_type: (conn.db_type as 'postgres' | 'sqlite') || 'postgres',
      host: conn.host || undefined,
      port: conn.port || undefined,
      username: conn.username || undefined,
      database_name: conn.database_name || undefined,
    });
  };

  const handleDelete = async (id: number) => {
    try {
      await apiService.deleteConnection(id);
      if (selectedConnection?.id === id) handleSelectConnection(null);
      await refreshConnections();
    } catch (e) {
      alert((e as Error).message);
    }
  };

  const handleTest = async (id: number) => {
    setTestingId(id);
    try {
      const ok = await apiService.testConnection(id);
      alert(ok ? 'Connection OK' : 'Connection failed');
    } finally {
      setTestingId(null);
    }
  };

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100 flex flex-col">
      <header className="bg-gray-900 border-b border-gray-800 p-4">
        <div className="max-w-6xl mx-auto flex items-center space-x-3">
          <div className="bg-green-600 p-2 rounded-lg">
            <Database className="h-6 w-6 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-white">Aigis Governance</h1>
            <p className="text-sm text-gray-400">AI Data Science Assistant</p>
          </div>
          <div className="ml-auto flex items-center space-x-2 text-sm text-gray-400">
            {/* Model selector button (left of connections button) */}
            <div className="flex items-center">
              <button
                onClick={() => setModelsOpen(true)}
                aria-expanded={modelsOpen}
                aria-controls="models-sidebar"
                className={cn(
                  'text-sm px-4 py-2 rounded transition-colors flex items-center focus:outline-none cursor-pointer mr-2',
                  apiService.getSelectedModelName()
                    ? 'bg-gray-800 text-white hover:bg-gray-700 focus:ring-2 focus:ring-green-500'
                    : 'bg-red-900/60 text-red-200 hover:bg-red-900/70 focus:ring-2 focus:ring-red-500 border border-red-800',
                )}
                title={apiService.getSelectedModelName() ? 'Select LLM model' : 'No model selected — click to choose one'}
                role="button"
              >
                <span className="truncate">
                  {apiService.getSelectedModelName() || 'No model selected'}
                </span>
              </button>
            </div>
            <div className="flex items-center space-x-2">
              <div
                className={cn(
                  'w-2 h-2 rounded-full',
                  getConnectionStatusColor(),
                )}
              ></div>
              <button
                onClick={() => setConnectionsOpen(true)}
                aria-expanded={connectionsOpen}
                aria-controls="connections-sidebar"
                className="text-sm px-4 py-2 rounded bg-gray-800 text-white hover:bg-gray-700 transition-colors flex items-center focus:outline-none focus:ring-2 focus:ring-green-500 cursor-pointer"
                title="Manage connections"
                role="button"
              >
                {getConnectionStatusText()}
              </button>
            </div>
            <button
              onClick={checkConnection}
              className="text-xs text-gray-500 hover:text-gray-300 underline cursor-pointer"
            >
              Refresh
            </button>
            <div className="pl-4">
              <div className="text-xs text-gray-300">
                {currentUser?.username || currentUser?.email}
              </div>
              <button
                onClick={() => {
                  apiService.clearAuth();
                  setCurrentUser(null);
                  // reload to let router redirect
                  window.location.href = '/login';
                }}
                className="text-xs text-gray-400 hover:text-gray-300 underline cursor-pointer"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="flex-1 flex flex-col max-w-6xl mx-auto w-full">
        <div className="flex-1 overflow-y-auto p-4 pb-32 space-y-4">
          {messages.map((message) => (
            <div
              key={message.id}
              className={cn(
                'chat-message',
                message.type === 'user'
                  ? 'user-message ml-12'
                  : 'agent-message mr-12',
                !message.isStreaming &&
                  message.type === 'agent' &&
                  'message-complete',
                'message-entrance',
                !message.isStreaming &&
                  message.type === 'agent' &&
                  message.endTime &&
                  'completion-pulse',
                message.isStreaming &&
                  message.type === 'agent' &&
                  'content-update',
              )}
            >
              <div className="flex items-start space-x-3">
                <div
                  className={cn(
                    'p-2 rounded-full',
                    message.type === 'user'
                      ? 'bg-green-600 text-white'
                      : 'bg-gray-700 text-green-400',
                  )}
                >
                  {message.type === 'user' ? (
                    <UserIcon className="h-4 w-4" />
                  ) : (
                    <Bot className="h-4 w-4" />
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center space-x-2 mb-2">
                    <span className="font-medium text-white">
                      {message.type === 'user' ? 'You' : 'AI Assistant'}
                    </span>
                    <span className="text-xs text-gray-500">
                      {message.isStreaming
                        ? 'Streaming...'
                        : formatTimestamp(message.timestamp)}
                    </span>
                  </div>
                  <div className="text-gray-200 leading-relaxed prose prose-invert prose-green max-w-none">
                    {message.streamingMessages &&
                    message.streamingMessages.length > 0 ? (
                      <div className="space-y-3">
                        {message.content && message.content !== 'Typing...' && (
                          <StreamingTextComponent
                            content={message.content}
                            isStreaming={message.isStreaming || false}
                          />
                        )}
                        {message.streamingMessages
                          .filter((msg) => msg.type !== 'text')
                          .map((streamingMsg, index) => (
                            <StreamingMessageComponent
                              key={`${streamingMsg.type}-${index}`}
                              message={streamingMsg}
                              isStreaming={message.isStreaming}
                            />
                          ))}
                      </div>
                    ) : message.content === 'Typing...' ? (
                      <div className="typing-indicator">
                        <span className="text-sm text-gray-400">
                          AI is thinking
                        </span>
                        <div className="typing-dot"></div>
                        <div className="typing-dot"></div>
                        <div className="typing-dot"></div>
                      </div>
                    ) : (
                      <div>{message.content}</div>
                    )}

                    {message.isStreaming && message.content !== 'Typing...' && (
                      <div className="inline-flex items-center space-x-1 mt-2 text-green-400">
                        <div className="streaming-dot"></div>
                        <span className="text-sm">Streaming...</span>
                      </div>
                    )}

                    {message.isStreaming &&
                      message.content !== 'Typing...' &&
                      message.streamingMessages &&
                      message.streamingMessages.length > 0 && (
                        <div className="mt-3">
                          <div className="progress-bar">
                            <div className="progress-fill"></div>
                          </div>
                          <div className="text-xs text-gray-500 mt-2">
                            {message.streamingMessages.length} messages received
                          </div>
                        </div>
                      )}

                    {message.isStreaming && message.content !== 'Typing...' && (
                      <span className="streaming-cursor"></span>
                    )}

                    {!message.isStreaming &&
                      message.type === 'agent' &&
                      message.content &&
                      message.content !== 'Typing...' && (
                        <div className="mt-2 text-xs text-green-400 flex items-center space-x-1">
                          <div className="w-2 h-2 bg-green-400 rounded-full"></div>
                          <span className="complete">
                            Response complete
                            {message.startTime && message.endTime && (
                              <span className="text-gray-400 ml-1">
                                ({(message.endTime - message.startTime) / 1000}
                                s)
                              </span>
                            )}
                          </span>
                        </div>
                      )}

                    {message.error && (
                      <div className="mt-3">
                        <button
                          onClick={() => handleRetry(message.id)}
                          className="bg-red-600 hover:bg-red-700 text-white px-6 py-2 rounded-lg text-sm font-medium transition-colors duration-200"
                        >
                          Retry Request
                        </button>
                        <div className="mt-2 text-xs error">
                          Error: {message.error}
                        </div>
                      </div>
                    )}
                  </div>

                  {message.plots && message.plots.length > 0 && (
                    <div className="mt-3">
                      <div className="plot-container">
                        <div className="flex items-center space-x-2 mb-2">
                          <BarChart3 className="h-4 w-4 text-green-400" />
                          <span className="text-sm font-medium text-green-400">
                            Generated Plots
                          </span>
                        </div>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          {message.plots.map((_, index) => (
                            <div
                              key={index}
                              className="bg-gray-800 rounded-lg p-4 border border-gray-700"
                            >
                              <div className="aspect-video bg-gray-700 rounded flex items-center justify-center">
                                <span className="text-gray-500 text-sm">
                                  Plot {index + 1}
                                </span>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>

        <div className="fixed bottom-0 left-0 right-0 bg-gray-950 border-t border-gray-800 p-4 z-10">
          <form onSubmit={handleSubmit} className="max-w-4xl mx-auto">
            <div className="flex space-x-3">
              <div className="flex-1 relative">
                <input
                  ref={inputRef}
                  type="text"
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  placeholder="Ask me anything..."
                  className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-3 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent"
                  disabled={
                    isLoading ||
                    connectionStatus !== 'connected' ||
                    messages.some((msg) => msg.isStreaming)
                  }
                />
              </div>
              <button
                type="submit"
                disabled={
                  !inputValue.trim() ||
                  isLoading ||
                  connectionStatus !== 'connected' ||
                  messages.some((msg) => msg.isStreaming)
                }
                className="bg-green-600 hover:bg-green-700 disabled:bg-gray-700 disabled:cursor-not-allowed text-white px-6 py-3 rounded-lg font-medium transition-colors duration-200 flex items-center space-x-2"
              >
                <Send className="h-4 w-4" />
                <span>Send</span>
              </button>
            </div>
            <div className="mt-2 text-xs text-gray-500">
              {connectionStatus === 'connected' ? (
                isLoading ? (
                  <span className="sending">Sending request...</span>
                ) : messages.some((msg) => msg.isStreaming) ? (
                  <span className="receiving">
                    Streaming response... Please wait.
                  </span>
                ) : (
                  'Press Enter to send, Shift+Enter for new line'
                )
              ) : (
                'Please wait for connection to be established...'
              )}
            </div>
            {inputValue.trim() &&
              connectionStatus === 'connected' &&
              !isLoading &&
              !messages.some((msg) => msg.isStreaming) && (
                <div className="mt-1 text-xs typing-active">
                  Press Enter to send
                </div>
              )}
          </form>
        </div>
      </main>
      {/* Connections sidebar */}
      <ConnectionsSidebar
        open={connectionsOpen}
        onClose={() => setConnectionsOpen(false)}
        connections={connections}
        selectedConnection={selectedConnection}
        selectedCustomIds={selectedCustomIds}
        formState={formState}
        editingId={editingId}
        testingId={testingId}
        setFormState={(s) => setFormState(s)}
        setEditingId={(id) => setEditingId(id)}
        onSelect={handleSelectConnection}
        onToggleCustom={handleToggleCustom}
        onSave={handleSaveConnection}
        onEdit={handleEdit}
        onDelete={handleDelete}
        onTest={handleTest}
        onRefresh={refreshConnections}
      />
      {/* Models sidebar */}
      <ModelSidebar open={modelsOpen} onClose={() => setModelsOpen(false)} />
    </div>
  );
};

export default ChatUI;
