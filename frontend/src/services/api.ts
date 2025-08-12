// ADK API Service for chat and session management

export interface ChatRequest {
  message: string;
  streaming?: boolean;
}

export interface ChatResponse {
  content: string;
  plots?: string[];
  sessionId: string;
  error?: string;
}

export interface StreamingChatResponse {
  content: string;
  partial: boolean;
  sessionId: string;
  error?: string;
}

export class ApiService {
  private baseUrl: string;
  private appName: string;
  private userId: string;
  private sessionId: string = '';

  constructor(
    baseUrl: string = 'http://localhost:8000',
    appName = 'data_science',
    userId = 'u_123',
  ) {
    this.baseUrl = baseUrl;
    this.appName = appName;
    this.userId = userId;
  }

  // Create a new session if one does not exist
  async ensureSession(): Promise<string> {
    if (this.sessionId) return this.sessionId;
    // Create session
    const response = await fetch(
      `${this.baseUrl}/apps/${this.appName}/users/${this.userId}/sessions`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({}),
      },
    );
    if (!response.ok) throw new Error('Failed to create session');
    const data = await response.json();
    this.sessionId = data.session_id || data.sessionId || data.id;
    return this.sessionId;
  }

  // Send a chat message to the ADK agent with streaming support
  async sendMessageStreaming(
    message: string,
    onChunk: (chunk: StreamingChatResponse) => void,
    onComplete: (finalResponse: ChatResponse) => void,
    onError: (error: string) => void,
  ): Promise<void> {
    try {
      const sessionId = await this.ensureSession();
      const payload = {
        app_name: this.appName,
        user_id: this.userId,
        session_id: sessionId,
        new_message: {
          role: 'user',
          parts: [{ text: message }],
        },
        streaming: true,
      };

      // Add timeout to the fetch request
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 second timeout

      const response = await fetch(`${this.baseUrl}/run_sse`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      if (!response.body) {
        throw new Error('Response body is null');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let plots: string[] = [];

      try {
        while (true) {
          const { done, value } = await reader.read();

          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');

          // Keep the last incomplete line in the buffer
          buffer = lines.pop() || '';

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const data = JSON.parse(line.slice(6));

                if (data.content && data.content.parts) {
                  const textContent = data.content.parts
                    .map((part: any) => part.text || '')
                    .filter((text: string) => text.trim())
                    .join('');

                  // Check if this is a partial response
                  const isPartial = data.partial === true;

                  if (isPartial) {
                    // Only call onChunk for partial responses to avoid duplication
                    onChunk({
                      content: textContent,
                      partial: true,
                      sessionId: sessionId,
                    });
                  } else {
                    // This is the final response without "partial", so call onComplete
                    onComplete({
                      content: textContent,
                      plots,
                      sessionId: sessionId,
                    });
                    return; // Exit early since we got the final response
                  }
                }

                // Handle artifacts if they exist
                if (data.actions && data.actions.artifactDelta) {
                  console.log('Artifacts found:', data.actions.artifactDelta);
                }
              } catch (parseError) {
                console.warn('Failed to parse SSE data:', line, parseError);
              }
            }
          }
        }
      } finally {
        reader.releaseLock();
      }

      // onComplete is now called when we receive the final response without "partial"
    } catch (error: any) {
      console.error('SSE API Error:', error);
      if (error.name === 'AbortError') {
        onError('Request timed out. Please try again.');
      } else {
        onError(error.message || 'Unknown error');
      }
    }
  }

  // Send a chat message to the ADK agent (non-streaming)
  async sendMessage(message: string): Promise<ChatResponse> {
    try {
      const sessionId = await this.ensureSession();
      const payload = {
        app_name: this.appName,
        user_id: this.userId,
        session_id: sessionId,
        new_message: {
          role: 'user',
          parts: [{ text: message }],
        },
      };
      const response = await fetch(`${this.baseUrl}/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();

      // Parse ADK API response - it returns an array of objects
      let content = '';
      let plots: string[] = [];

      if (Array.isArray(data) && data.length > 0) {
        // Look for the content object (usually the second one with role: "model")
        const contentObject = data.find(
          (item: any) =>
            item.content &&
            item.content.parts &&
            Array.isArray(item.content.parts),
        );

        if (contentObject && contentObject.content.parts) {
          // Extract text from all parts
          content = contentObject.content.parts
            .map((part: any) => part.text || '')
            .filter((text: string) => text.trim())
            .join('\n');
        }

        // Look for any artifacts or additional data in the response
        // This might need to be adjusted based on actual response structure
        if (
          contentObject &&
          contentObject.actions &&
          contentObject.actions.artifactDelta
        ) {
          // Handle artifacts if they exist
          console.log('Artifacts found:', contentObject.actions.artifactDelta);
        }
      } else if (typeof data === 'string') {
        content = data;
      } else {
        content = 'No response content found';
        console.warn('Unexpected response format:', data);
      }
      return {
        content,
        plots,
        sessionId: sessionId,
      };
    } catch (error: any) {
      console.error('API Error:', error);
      return {
        content: '',
        plots: [],
        sessionId: this.sessionId || '',
        error: error.message || 'Unknown error',
      };
    }
  }

  async getHealth(): Promise<boolean> {
    try {
      // Check if endpoint is available
      const response = await fetch(`${this.baseUrl}/list-apps`);
      return response.ok;
    } catch {
      return false;
    }
  }

  // Method to check if BigQuery connection is available
  async checkBigQueryConnection(): Promise<boolean> {
    try {
      // Check if we can reach the ADK server by trying to list apps
      const response = await fetch(`${this.baseUrl}/list-apps`);

      return response.ok;
    } catch {
      return false;
    }
  }
}

export const apiService = new ApiService();
