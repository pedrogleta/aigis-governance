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
  const [connections, setConnections] = useState<UserConnection[]>([]);
  const [selectedConnection, setSelectedConnection] =
    useState<UserConnection | null>(apiService.getSelectedConnection());
  const [formState, setFormState] = useState<UserConnectionCreate>({
    name: '',
    db_type: 'postgres',
  });
  const [editingId, setEditingId] = useState<number | null>(null);
  const [testingId, setTestingId] = useState<number | null>(null);
  // Control sidebar enter/exit animation state so we can fade/slide it
  const [sidebarActive, setSidebarActive] = useState(false);
  const closeTimeoutRef = useRef<number | null>(null);
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

  // keep sidebar animation state in sync with open/close
  useEffect(() => {
    if (connectionsOpen) {
      // ensure mounted -> then activate animation
      // small delay lets the DOM mount with initial classes
      window.setTimeout(() => setSidebarActive(true), 10);
    } else {
      // if being closed, clear any pending timeout
      setSidebarActive(false);
      if (closeTimeoutRef.current) {
        window.clearTimeout(closeTimeoutRef.current);
        closeTimeoutRef.current = null;
      }
    }
  }, [connectionsOpen]);

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
        return (
          <span className="connected">
            {selectedConnection
              ? `Connected: ${selectedConnection.name}`
              : 'Connected'}
          </span>
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

  const handleSelectConnection = (conn: UserConnection | null) => {
    setSelectedConnection(conn);
    apiService.setSelectedConnection(conn);
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
    if (!confirm('Delete this connection?')) return;
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
            <div className="flex items-center space-x-1">
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
                className="hover:text-gray-200 cursor-pointer text-sm flex items-center"
                title="Manage connections"
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
      {(connectionsOpen || sidebarActive) && (
        <div className="fixed inset-0 z-20">
          <div
            className={cn(
              'absolute inset-0 bg-black/50 transition-opacity duration-200',
              sidebarActive ? 'opacity-80' : 'opacity-0 pointer-events-none',
            )}
            onClick={() => {
              // start hide animation and unmount after duration
              setSidebarActive(false);
              if (closeTimeoutRef.current)
                window.clearTimeout(closeTimeoutRef.current);
              closeTimeoutRef.current = window.setTimeout(
                () => setConnectionsOpen(false),
                200,
              );
            }}
            style={{ cursor: 'pointer' }}
          />
          <div
            id="connections-sidebar"
            className={cn(
              'absolute right-0 top-0 h-full w-full sm:w-[420px] bg-gray-900 border-l border-gray-800 p-4 overflow-y-auto transform transition-all duration-200',
              sidebarActive
                ? 'opacity-100 translate-x-0'
                : 'opacity-0 translate-x-6',
            )}
            role="dialog"
            aria-modal="true"
            aria-hidden={!sidebarActive}
          >
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-white">Connections</h2>
              <button
                onClick={() => {
                  setSidebarActive(false);
                  if (closeTimeoutRef.current)
                    window.clearTimeout(closeTimeoutRef.current);
                  closeTimeoutRef.current = window.setTimeout(
                    () => setConnectionsOpen(false),
                    200,
                  );
                }}
                className="text-gray-400 hover:text-gray-200 cursor-pointer"
              >
                Close
              </button>
            </div>

            <div className="space-y-2 mb-6">
              <label className="block text-sm text-gray-300">Name</label>
              <input
                className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2"
                value={formState.name || ''}
                onChange={(e) =>
                  setFormState({ ...formState, name: e.target.value })
                }
                placeholder="My Postgres"
              />
              <label className="block text-sm text-gray-300 mt-3">Type</label>
              <select
                className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2"
                value={formState.db_type}
                onChange={(e) =>
                  setFormState({
                    ...formState,
                    db_type: e.target.value as 'postgres' | 'sqlite',
                  })
                }
              >
                <option value="postgres">PostgreSQL</option>
                <option value="sqlite">SQLite</option>
              </select>

              {formState.db_type === 'sqlite' ? (
                <>
                  <label className="block text-sm text-gray-300 mt-3">
                    File path
                  </label>
                  <input
                    className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2"
                    value={formState.host || ''}
                    onChange={(e) =>
                      setFormState({ ...formState, host: e.target.value })
                    }
                    placeholder="/path/to/db.sqlite"
                  />
                </>
              ) : (
                <>
                  <label className="block text-sm text-gray-300 mt-3">
                    Host
                  </label>
                  <input
                    className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2"
                    value={formState.host || ''}
                    onChange={(e) =>
                      setFormState({ ...formState, host: e.target.value })
                    }
                    placeholder="localhost"
                  />
                  <label className="block text-sm text-gray-300 mt-3">
                    Port
                  </label>
                  <input
                    type="number"
                    className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2"
                    value={formState.port || ''}
                    onChange={(e) =>
                      setFormState({
                        ...formState,
                        port: Number(e.target.value),
                      })
                    }
                    placeholder="5432"
                  />
                  <label className="block text-sm text-gray-300 mt-3">
                    Username
                  </label>
                  <input
                    className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2"
                    value={formState.username || ''}
                    onChange={(e) =>
                      setFormState({ ...formState, username: e.target.value })
                    }
                    placeholder="postgres"
                  />
                  <label className="block text-sm text-gray-300 mt-3">
                    Database
                  </label>
                  <input
                    className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2"
                    value={formState.database_name || ''}
                    onChange={(e) =>
                      setFormState({
                        ...formState,
                        database_name: e.target.value,
                      })
                    }
                    placeholder="example_db"
                  />
                  <label className="block text-sm text-gray-300 mt-3">
                    Password
                  </label>
                  <input
                    type="password"
                    className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2"
                    onChange={(e) =>
                      setFormState({ ...formState, password: e.target.value })
                    }
                    placeholder={
                      editingId ? 'Leave blank to keep current' : 'Password'
                    }
                  />
                </>
              )}

              <div className="flex items-center space-x-2 mt-4">
                <button
                  className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded cursor-pointer"
                  onClick={handleSaveConnection}
                >
                  {editingId ? 'Update' : 'Create'}
                </button>
                <button
                  className="bg-gray-700 hover:bg-gray-600 text-white px-4 py-2 rounded cursor-pointer"
                  onClick={() => {
                    setEditingId(null);
                    setFormState({ name: '', db_type: 'postgres' });
                  }}
                >
                  Clear
                </button>
              </div>
            </div>

            <div>
              <h3 className="text-sm font-semibold text-gray-300 mb-2">
                Your connections
              </h3>
              <div className="space-y-2">
                {connections.map((c) => (
                  <div
                    key={c.id}
                    className={cn(
                      'border border-gray-800 rounded p-3 flex items-center justify-between space-x-3 hover:border-green-600 transition-colors',
                      selectedConnection?.id === c.id &&
                        'border-green-600 bg-gray-800',
                    )}
                  >
                    <div className="flex items-center space-x-3 min-w-0">
                      <div className="flex-1 min-w-0">
                        <div className="text-sm font-medium text-white truncate">
                          {c.name}
                        </div>
                        <div className="text-xs text-gray-400 truncate">
                          {c.db_type} {c.host ? `• ${c.host}` : ''}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <button
                        title={
                          selectedConnection?.id === c.id
                            ? 'Selected'
                            : 'Select'
                        }
                        onClick={() => handleSelectConnection(c)}
                        className={cn(
                          'text-xs px-2 py-1 rounded text-gray-200 hover:bg-gray-800 transition-colors',
                          selectedConnection?.id === c.id &&
                            'bg-green-600 text-white',
                        )}
                        style={{ cursor: 'pointer' }}
                      >
                        {selectedConnection?.id === c.id
                          ? 'Selected'
                          : 'Select'}
                      </button>
                      <button
                        onClick={() => handleTest(c.id)}
                        disabled={testingId === c.id}
                        className="text-xs px-2 py-1 rounded bg-gray-800 hover:bg-gray-700 text-gray-200 transition-colors"
                        style={{ cursor: 'pointer' }}
                        title="Test connection"
                      >
                        {testingId === c.id ? 'Testing...' : 'Test'}
                      </button>
                      <button
                        onClick={() => handleEdit(c)}
                        className="text-xs px-2 py-1 rounded bg-gray-800 hover:bg-gray-700 text-gray-200 transition-colors"
                        style={{ cursor: 'pointer' }}
                        title="Edit"
                      >
                        Edit
                      </button>
                      <button
                        onClick={() => handleDelete(c.id)}
                        className="text-xs px-2 py-1 rounded bg-red-700 hover:bg-red-600 text-white transition-colors"
                        style={{ cursor: 'pointer' }}
                        title="Delete"
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                ))}
                {connections.length === 0 && (
                  <div className="text-xs text-gray-500">
                    No connections yet.
                  </div>
                )}
              </div>
              <div className="mt-3">
                <button
                  className="text-xs text-gray-400 underline cursor-pointer"
                  onClick={refreshConnections}
                >
                  Refresh list
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ChatUI;
