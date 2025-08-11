import { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Database, BarChart3, Loader2 } from 'lucide-react';
import { cn } from './lib/utils';
import { apiService } from './services/api';
import type { ChatResponse } from './services/api';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface Message {
  id: string;
  type: 'user' | 'agent';
  content: string;
  timestamp: Date;
  plots?: string[];
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

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
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

    try {
      const response: ChatResponse = await apiService.sendMessage(inputValue);

      const agentMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'agent',
        content: response.content,
        timestamp: new Date(),
        plots: response.plots,
      };

      setMessages((prev) => [...prev, agentMessage]);
    } catch (error) {
      console.error('API Error:', error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'agent',
        content:
          'Sorry, I encountered an error while processing your request. Please check your connection and try again.',
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
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
        return 'Connected to BigQuery';
      case 'disconnected':
        return 'Disconnected';
      case 'checking':
        return 'Checking connection...';
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
                      {formatTimestamp(message.timestamp)}
                    </span>
                  </div>
                  <div className="text-gray-200 leading-relaxed prose prose-invert prose-green max-w-none">
                    <ReactMarkdown 
                      remarkPlugins={[remarkGfm]}
                      components={{
                        // Custom styling for code blocks
                        code: ({ className, children, ...props }: any) => {
                          const match = /language-(\w+)/.exec(className || '');
                          const isInline = !match;
                          return !isInline ? (
                            <pre className="bg-gray-800 rounded-lg p-4 border border-gray-700 overflow-x-auto">
                              <code className={className} {...props}>
                                {children}
                              </code>
                            </pre>
                          ) : (
                            <code className="bg-gray-800 px-1 py-0.5 rounded text-green-300 text-sm" {...props}>
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

          {/* Loading indicator */}
          {isLoading && (
            <div className="agent-message mr-12">
              <div className="flex items-start space-x-3">
                <div className="p-2 rounded-full bg-gray-700 text-green-400">
                  <Bot className="h-4 w-4" />
                </div>
                <div className="flex-1">
                  <div className="flex items-center space-x-2 mb-2">
                    <span className="font-medium text-white">AI Assistant</span>
                    <span className="text-xs text-gray-500">Thinking...</span>
                  </div>
                  <div className="flex items-center space-x-2 text-gray-400">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    <span>Analyzing your data...</span>
                  </div>
                </div>
              </div>
            </div>
          )}

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
                  disabled={isLoading || connectionStatus !== 'connected'}
                />
              </div>
              <button
                type="submit"
                disabled={
                  !inputValue.trim() ||
                  isLoading ||
                  connectionStatus !== 'connected'
                }
                className="bg-green-600 hover:bg-green-700 disabled:bg-gray-700 disabled:cursor-not-allowed text-white px-6 py-3 rounded-lg font-medium transition-colors duration-200 flex items-center space-x-2"
              >
                <Send className="h-4 w-4" />
                <span>Send</span>
              </button>
            </div>
            <div className="mt-2 text-xs text-gray-500">
              {connectionStatus === 'connected'
                ? 'Press Enter to send, Shift+Enter for new line'
                : 'Please wait for connection to be established...'}
            </div>
          </form>
        </div>
      </main>
    </div>
  );
}

export default App;
