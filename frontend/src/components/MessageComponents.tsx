import React from 'react';
import { Code, CheckCircle, Image } from 'lucide-react';
import type {
  FunctionCallMessage,
  FunctionResponseMessage,
  TextMessage,
  PlotMessage,
  StreamingMessage,
} from '../services/api';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface MessageProps {
  message: StreamingMessage;
  isStreaming?: boolean;
}

// Component for handling streaming text content intelligently
export const StreamingTextComponent: React.FC<{
  content: string;
  isStreaming: boolean;
}> = ({ content, isStreaming }) => {
  // Only render markdown when not streaming to avoid breaking up structured content
  if (isStreaming) {
    return <div className="whitespace-pre-wrap">{content}</div>;
  }

  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      components={{
        // Custom styling for code blocks
        code: ({
          className,
          children,
          ...props
        }: React.ComponentProps<'code'>) => {
          const match = /language-(\w+)/.exec(className || '');
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
          <ul className="list-disc list-inside space-y-1">{children}</ul>
        ),
        ol: ({ children }) => (
          <ol className="list-decimal list-inside space-y-1">{children}</ol>
        ),
        // Custom styling for blockquotes
        blockquote: ({ children }) => (
          <blockquote className="border-l-4 border-green-500 pl-4 italic text-gray-300 bg-gray-800 py-2 rounded-r">
            {children}
          </blockquote>
        ),
      }}
    >
      {content}
    </ReactMarkdown>
  );
};

// Component for displaying function calls
export const FunctionCallComponent: React.FC<{
  message: FunctionCallMessage;
}> = ({ message }) => {
  return (
    <div className="bg-blue-900/20 border border-blue-700/50 rounded-lg p-4 mb-3">
      <div className="flex items-center space-x-2 mb-3">
        <div className="bg-blue-600 p-2 rounded-full">
          <Code className="h-4 w-4 text-white" />
        </div>
        <div>
          <span className="font-medium text-blue-300">Function Call</span>
          <span className="text-xs text-blue-400 ml-2">{message.name}</span>
        </div>
      </div>

      <div className="space-y-2">
        <div>
          <span className="text-sm text-blue-200 font-medium">Function:</span>
          <span className="text-blue-100 ml-2 font-mono">{message.name}</span>
        </div>

        <div>
          <span className="text-sm text-blue-200 font-medium">Arguments:</span>
          <div className="mt-1 bg-blue-950/50 rounded p-2 border border-blue-800/50">
            <pre className="text-xs text-blue-100 overflow-x-auto">
              {JSON.stringify(message.args, null, 2)}
            </pre>
          </div>
        </div>

        <div className="text-xs text-blue-400">
          {message.timestamp.toLocaleTimeString()}
        </div>
      </div>
    </div>
  );
};

// Component for displaying function responses
export const FunctionResponseComponent: React.FC<{
  message: FunctionResponseMessage;
}> = ({ message }) => {
  return (
    <div className="bg-green-900/20 border border-green-700/50 rounded-lg p-4 mb-3">
      <div className="flex items-center space-x-2 mb-3">
        <div className="bg-green-600 p-2 rounded-full">
          <CheckCircle className="h-4 w-4 text-white" />
        </div>
        <div>
          <span className="font-medium text-green-300">Function Response</span>
          <span className="text-xs text-green-400 ml-2">{message.name}</span>
        </div>
      </div>

      <div className="space-y-2">
        <div>
          <span className="text-sm text-green-200 font-medium">Function:</span>
          <span className="text-green-100 ml-2 font-mono">{message.name}</span>
        </div>

        <div>
          <span className="text-sm text-green-200 font-medium">Result:</span>
          <div className="mt-1 bg-green-950/50 rounded p-2 border border-green-800/50">
            <div className="text-green-100 text-sm whitespace-pre-wrap">
              {message.result}
            </div>
          </div>
        </div>

        <div className="text-xs text-green-400">
          {message.timestamp.toLocaleTimeString()}
        </div>
      </div>
    </div>
  );
};

// Component for displaying text messages
export const TextComponent: React.FC<{
  message: TextMessage;
  isStreaming?: boolean;
}> = ({ message, isStreaming = false }) => {
  return (
    <div className="space-y-2">
      <div className="text-gray-200 leading-relaxed prose prose-invert prose-green max-w-none">
        {message.content === 'Typing...' ? (
          <div className="typing-indicator">
            <span className="text-sm text-gray-400">AI is thinking</span>
            <div className="typing-dot"></div>
            <div className="typing-dot"></div>
            <div className="typing-dot"></div>
          </div>
        ) : (
          <StreamingTextComponent
            content={message.content}
            isStreaming={isStreaming}
          />
        )}
      </div>

      {/* Streaming indicator */}
      {isStreaming && message.content !== 'Typing...' && (
        <div className="inline-flex items-center space-x-1 mt-2 text-green-400">
          <div className="streaming-dot"></div>
          <span className="text-sm">Streaming...</span>
        </div>
      )}

      {/* Progress bar for streaming messages */}
      {isStreaming && message.content !== 'Typing...' && (
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
      {isStreaming && message.content !== 'Typing...' && (
        <span className="streaming-cursor"></span>
      )}
    </div>
  );
};

// Component for displaying plot messages
export const PlotComponent: React.FC<{
  message: PlotMessage;
}> = ({ message }) => {
  const [imageUrl, setImageUrl] = React.useState<string | null>(null);
  const [isLoading, setIsLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    const loadImage = async () => {
      try {
        setIsLoading(true);
        setError(null);

        // Get presigned URL from MinIO
        const { MinioService } = await import('../services/minio');
        const url = await MinioService.getFileUrl(message.filename);
        setImageUrl(url);
      } catch (err) {
        console.error('Error loading plot image:', err);
        setError('Failed to load plot image');
      } finally {
        setIsLoading(false);
      }
    };

    loadImage();
  }, [message.filename]);

  return (
    <div className="bg-purple-900/20 border border-purple-700/50 rounded-lg p-4 mb-3">
      <div className="flex items-center space-x-2 mb-3">
        <div className="bg-purple-600 p-2 rounded-full">
          <Image className="h-4 w-4 text-white" />
        </div>
        <div>
          <span className="font-medium text-purple-300">Generated Plot</span>
          <span className="text-xs text-purple-400 ml-2">
            {message.filename}
          </span>
        </div>
      </div>

      <div className="space-y-2">
        {isLoading && (
          <div className="text-purple-200 text-sm">Loading plot...</div>
        )}

        {error && <div className="text-red-400 text-sm">Error: {error}</div>}

        {imageUrl && !isLoading && (
          <div className="mt-2">
            <img
              src={imageUrl}
              alt="Generated plot"
              className="max-w-full h-auto rounded border border-purple-600/50"
              onError={() => setError('Failed to display image')}
            />
          </div>
        )}

        <div className="text-xs text-purple-400">
          {message.timestamp.toLocaleTimeString()}
        </div>
      </div>
    </div>
  );
};

// Main message component that renders the appropriate component based on message type
export const StreamingMessageComponent: React.FC<MessageProps> = ({
  message,
  isStreaming,
}) => {
  switch (message.type) {
    case 'functionCall':
      return <FunctionCallComponent message={message} />;
    case 'functionResponse':
      return <FunctionResponseComponent message={message} />;
    case 'text':
      return <TextComponent message={message} isStreaming={isStreaming} />;
    case 'plot':
      return <PlotComponent message={message} />;
    default:
      return <div>Unknown message type</div>;
  }
};
