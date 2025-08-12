import { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Database, BarChart3, Loader2 } from 'lucide-react';
import { cn } from './lib/utils';
import { apiService } from './services/api';
import type { ChatResponse, StreamingChatResponse } from './services/api';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

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
}

function App() {
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
    // Check connection status on component mount
    checkConnection();
  }, []);

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

    // Create a streaming agent message
    const agentMessageId = (Date.now() + 1).toString();
    const streamingAgentMessage: Message = {
      id: agentMessageId,
      type: 'agent',
      content: 'Typing...',
      timestamp: new Date(),
      isStreaming: true,
      startTime: Date.now(),
    };

    setMessages((prev) => [...prev, streamingAgentMessage]);

    // Play notification sound when streaming starts
    playNotificationSound();

    try {
      // Use streaming API
      await apiService.sendMessageStreaming(
        inputValue,
        // onChunk callback - called for each piece of content
        (chunk: StreamingChatResponse) => {
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === agentMessageId
                ? {
                    ...msg,
                    content:
                      msg.content === 'Typing...'
                        ? chunk.content
                        : msg.content + chunk.content,
                    isStreaming: chunk.partial,
                  }
                : msg,
            ),
          );
        },
        // onComplete callback - called when streaming is finished
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
        // onError callback - called if there's an error
        (error: string) => {
          console.error('Streaming Error:', error);
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === agentMessageId
                ? {
                    ...msg,
                    content: `Sorry, I encountered an error while processing your request: ${error}`,
                    isStreaming: false,
                    error: error,
                  }
                : msg,
            ),
          );
        },
      );
    } catch (error) {
      console.error('API Error:', error);
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

  const handleRetry = async (messageId: string, originalContent: string) => {
    // Find the user message that corresponds to this error message
    const messageIndex = messages.findIndex((msg) => msg.id === messageId);
    if (messageIndex === -1) return;

    // Find the previous user message
    let userMessageIndex = -1;
    for (let i = messageIndex - 1; i >= 0; i--) {
      if (messages[i].type === 'user') {
        userMessageIndex = i;
        break;
      }
    }

    if (userMessageIndex === -1) return;

    const userMessage = messages[userMessageIndex];

    // Remove the error message and create a new streaming message
    setMessages((prev) => [
      ...prev.slice(0, messageIndex),
      ...prev.slice(messageIndex + 1),
    ]);

    // Create a new streaming message
    const agentMessageId = (Date.now() + 1).toString();
    const streamingAgentMessage: Message = {
      id: agentMessageId,
      type: 'agent',
      content: 'Typing...',
      timestamp: new Date(),
      isStreaming: true,
      startTime: Date.now(),
    };

    setMessages((prev) => [...prev, streamingAgentMessage]);

    // Play notification sound when retrying
    playNotificationSound();

    try {
      await apiService.sendMessageStreaming(
        userMessage.content,
        (chunk: StreamingChatResponse) => {
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === agentMessageId
                ? {
                    ...msg,
                    content:
                      msg.content === 'Typing...'
                        ? chunk.content
                        : msg.content + chunk.content,
                    isStreaming: chunk.partial,
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
          console.error('Streaming Error:', error);
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === agentMessageId
                ? {
                    ...msg,
                    content: `Sorry, I encountered an error while processing your request: ${error}`,
                    isStreaming: false,
                    error: error,
                  }
                : msg,
            ),
          );
        },
      );
    } catch (error) {
      console.error('API Error:', error);
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

  const formatTimestamp = (date: Date) => {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

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
        return <span className="connected">Connected to BigQuery</span>;
      case 'disconnected':
        return <span className="disconnected">Disconnected</span>;
      case 'checking':
        return <span className="connecting">Checking connection...</span>;
      default:
        return 'Unknown status';
    }
  };

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100 flex flex-col">
      {/* Header */}
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
              <span>{getConnectionStatusText()}</span>
            </div>
            <button
              onClick={checkConnection}
              className="text-xs text-gray-500 hover:text-gray-300 underline"
            >
              Refresh
            </button>
          </div>
        </div>
      </header>

      {/* Main Chat Area */}
      <main className="flex-1 flex flex-col max-w-6xl mx-auto w-full">
        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
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
                    <User className="h-4 w-4" />
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
                    {message.content === 'Typing...' ? (
                      <div className="typing-indicator">
                        <span className="text-sm text-gray-400">
                          AI is thinking
                        </span>
                        <div className="typing-dot"></div>
                        <div className="typing-dot"></div>
                        <div className="typing-dot"></div>
                      </div>
                    ) : (
                      <ReactMarkdown
                        remarkPlugins={[remarkGfm]}
                        components={{
                          // Custom styling for code blocks
                          code: ({ className, children, ...props }: any) => {
                            const match = /language-(\w+)/.exec(
                              className || '',
                            );
                            const isInline = !match;
                            return !isInline ? (
                              <pre className="bg-gray-800 rounded-lg p-4 border border-gray-700 overflow-x-auto">
                                <code className={className} {...props}>
                                  {children}
                                </code>
                              </pre>
                            ) : (
                              <code
                                className="bg-gray-800 px-1 py-0.5 rounded text-green-300 text-sm"
                                {...props}
                              >
                                {children}
                              </code>
                            );
                          },
                          // Custom styling for tables
                          table: ({ children }) => (
                            <div className="overflow-x-auto">
                              <table className="min-w-full border-collapse border border-gray-700">
                                {children}
                              </table>
                            </div>
                          ),
                          th: ({ children }) => (
                            <th className="border border-gray-700 px-3 py-2 text-left bg-gray-800 text-green-400 font-medium">
                              {children}
                            </th>
                          ),
                          td: ({ children }) => (
                            <td className="border border-gray-700 px-3 py-2 text-left">
                              {children}
                            </td>
                          ),
                          // Custom styling for lists
                          ul: ({ children }) => (
                            <ul className="list-disc list-inside space-y-1">
                              {children}
                            </ul>
                          ),
                          ol: ({ children }) => (
                            <ol className="list-decimal list-inside space-y-1">
                              {children}
                            </ol>
                          ),
                          // Custom styling for blockquotes
                          blockquote: ({ children }) => (
                            <blockquote className="border-l-4 border-green-500 pl-4 italic text-gray-300 bg-gray-800 py-2 rounded-r">
                              {children}
                            </blockquote>
                          ),
                        }}
                      >
                        {message.content}
                      </ReactMarkdown>
                    )}

                    {/* Streaming indicator */}
                    {message.isStreaming && message.content !== 'Typing...' && (
                      <div className="inline-flex items-center space-x-1 mt-2 text-green-400">
                        <div className="streaming-dot"></div>
                        <span className="text-sm">Streaming...</span>
                      </div>
                    )}

                    {/* Progress bar for streaming messages */}
                    {message.isStreaming && message.content !== 'Typing...' && (
                      <div className="mt-3">
                        <div className="progress-bar">
                          <div className="progress-fill"></div>
                        </div>
                        <div className="text-xs text-gray-500 mt-2">
                          {message.content.length} characters generated
                        </div>
                      </div>
                    )}

                    {/* Blinking cursor for streaming messages */}
                    {message.isStreaming && message.content !== 'Typing...' && (
                      <span className="streaming-cursor"></span>
                    )}

                    {/* Completion indicator */}
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

                    {/* Retry button for error messages */}
                    {message.error && (
                      <div className="mt-3">
                        <button
                          onClick={() =>
                            handleRetry(message.id, message.content)
                          }
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

                  {/* Plots */}
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

        {/* Input Form */}
        <div className="border-t border-gray-800 p-4">
          <form onSubmit={handleSubmit} className="max-w-4xl mx-auto">
            <div className="flex space-x-3">
              <div className="flex-1 relative">
                <input
                  ref={inputRef}
                  type="text"
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  placeholder="Ask me anything about your BigQuery dataset... (e.g., 'Show me sales trends for Q4' or 'Create a scatter plot of revenue vs. customers')"
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
    </div>
  );
}

export default App;
