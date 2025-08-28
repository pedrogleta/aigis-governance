// API Service for chat and session management (FastAPI + LangGraph)

// Simple backend SSE payload type
type BackendSSE =
  | { type: 'chunk'; content: string }
  | { type: 'tool_result'; content: unknown }
  | { type: 'end'; full_response: string }
  | { type: 'error'; error: string };

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

// New interfaces for different message types
export interface FunctionCallMessage {
  type: 'functionCall';
  id: string;
  name: string;
  args: Record<string, unknown>;
  timestamp: Date;
}

export interface FunctionResponseMessage {
  type: 'functionResponse';
  id: string;
  name: string;
  result: string;
  timestamp: Date;
}

export interface TextMessage {
  type: 'text';
  content: string;
  partial: boolean;
  timestamp: Date;
}

export interface PlotMessage {
  type: 'plot';
  filename: string;
  timestamp: Date;
}

export interface ToolStreamMessage {
  type: 'tool';
  content: unknown;
  timestamp: Date;
}

export type StreamingMessage =
  | FunctionCallMessage
  | FunctionResponseMessage
  | TextMessage
  | PlotMessage
  | ToolStreamMessage;

export class ApiService {
  private baseUrl: string;
  private threadId: string = '';
  private token: string | null = null;
  private currentUser: User | null = null;
  private selectedConnection: UserConnection | null = null;

  constructor(baseUrl: string = 'http://localhost:8000') {
    this.baseUrl = baseUrl;
    // Load auth state from localStorage
    try {
      const stored = localStorage.getItem('aigis_token');
      if (stored) this.token = stored;
      const userJson = localStorage.getItem('aigis_user');
      if (userJson) this.currentUser = JSON.parse(userJson);
      const connJson = localStorage.getItem('aigis_selected_connection');
      if (connJson) this.selectedConnection = JSON.parse(connJson);
    } catch (e) {
      console.warn('Failed to load auth from localStorage', e);
    }
  }

  // Simple user type for auth responses
  getToken() {
    return this.token;
  }

  getCurrentUser() {
    return this.currentUser;
  }

  private saveAuth(token: string, user: User | null) {
    this.token = token;
    this.currentUser = user;
    try {
      localStorage.setItem('aigis_token', token);
      if (user) localStorage.setItem('aigis_user', JSON.stringify(user));
    } catch (e) {
      console.warn('Failed to save auth to localStorage', e);
    }
  }

  clearAuth() {
    this.token = null;
    this.currentUser = null;
    this.selectedConnection = null;
    try {
      localStorage.removeItem('aigis_token');
      localStorage.removeItem('aigis_user');
      localStorage.removeItem('aigis_selected_connection');
    } catch (e) {
      console.warn('Failed to clear auth from localStorage', e);
    }
  }

  private getAuthHeaders(contentType = 'application/json') {
    const headers: Record<string, string> = { 'Content-Type': contentType };
    if (this.token) headers['Authorization'] = `Bearer ${this.token}`;
    return headers;
  }

  // Create a new chat thread if one does not exist
  async ensureThread(): Promise<string> {
    if (this.threadId) return this.threadId;
    const response = await fetch(`${this.baseUrl}/chat/thread`, {
      method: 'POST',
      headers: this.getAuthHeaders('application/json'),
    });
    if (!response.ok) throw new Error('Failed to create thread');
    const data = (await response.json()) as { thread_id?: string };
    if (!data.thread_id) throw new Error('Invalid thread response');
    this.threadId = data.thread_id;
    return this.threadId;
  }

  async updateThreadConnection(userConnectionId: number): Promise<void> {
    const threadId = await this.ensureThread();
    const resp = await fetch(`${this.baseUrl}/chat/${threadId}/connection`, {
      method: 'POST',
      headers: this.getAuthHeaders('application/json'),
      body: JSON.stringify({ user_connection_id: userConnectionId }),
    });
    if (!resp.ok) {
      const text = await resp.text();
      throw new Error(text || `Failed to update connection: ${resp.status}`);
    }
  }

  // Send a chat message to the agent with streaming support
  async sendMessageStreaming(
    message: string,
    onChunk: (chunk: StreamingMessage) => void,
    onComplete: (finalResponse: ChatResponse) => void,
    onError: (error: string) => void,
  ): Promise<void> {
    try {
      const threadId = await this.ensureThread();
      const payload = {
        text: message,
        user_connection_id: this.selectedConnection?.id,
      };

      // Add timeout to the fetch request
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 second timeout

      const response = await fetch(`${this.baseUrl}/chat/${threadId}/message`, {
        method: 'POST',
        headers: this.getAuthHeaders('application/json'),
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
      let finalTextContent = '';

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
                const data: BackendSSE = JSON.parse(line.slice(6));
                const timestamp = new Date();

                if (data.type === 'chunk' && typeof data.content === 'string') {
                  const textMessage: TextMessage = {
                    type: 'text',
                    content: data.content,
                    partial: true,
                    timestamp,
                  };
                  onChunk(textMessage);
                  finalTextContent += data.content;
                } else if (data.type === 'tool_result') {
                  const toolMessage: ToolStreamMessage = {
                    type: 'tool',
                    content: data.content,
                    timestamp,
                  };
                  onChunk(toolMessage);
                } else if (data.type === 'end') {
                  // Ignore here, handled after loop
                } else if (data.type === 'error') {
                  onError(data.error || 'Unknown streaming error');
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

      // Call onComplete when the stream is finished
      if (finalTextContent.trim()) {
        onComplete({
          content: finalTextContent,
          plots: [],
          sessionId: threadId,
        });
      }
    } catch (error: unknown) {
      console.error('SSE API Error:', error);
      if (error instanceof Error) {
        if (error.name === 'AbortError') {
          onError('Request timed out. Please try again.');
        } else {
          onError(error.message || 'Unknown error');
        }
      } else {
        onError('Unknown error occurred');
      }
    }
  }

  // Send a chat message to the agent (non-streaming by aggregating SSE)
  async sendMessage(message: string): Promise<ChatResponse> {
    try {
      const threadId = await this.ensureThread();
      // Use the streaming endpoint and aggregate
      let aggregated = '';
      await this.sendMessageStreaming(
        message,
        (chunk) => {
          if (chunk.type === 'text' && chunk.partial)
            aggregated += chunk.content;
        },
        () => {},
        (err) => {
          throw new Error(err);
        },
      );
      return { content: aggregated, plots: [], sessionId: threadId };
    } catch (error: unknown) {
      console.error('API Error:', error);
      return {
        content: '',
        plots: [],
        sessionId: this.threadId || '',
        error: error instanceof Error ? error.message : 'Unknown error',
      };
    }
  }

  async getHealth(): Promise<boolean> {
    try {
      // Check if endpoint is available
      const response = await fetch(`${this.baseUrl}/health`, {
        headers: this.getAuthHeaders(),
      });
      return response.ok;
    } catch {
      return false;
    }
  }

  // Method to check if BigQuery connection is available
  async checkBigQueryConnection(): Promise<boolean> {
    try {
      // For now, use the same health endpoint
      const response = await fetch(`${this.baseUrl}/health`, {
        headers: this.getAuthHeaders(),
      });

      return response.ok;
    } catch {
      return false;
    }
  }

  // -----------------
  // Authentication API
  // -----------------

  async register(payload: {
    email: string;
    username: string;
    password: string;
  }) {
    const response = await fetch(`${this.baseUrl}/auth/register`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify(payload),
    });
    if (!response.ok) {
      const text = await response.text();
      throw new Error(text || `Register failed: ${response.status}`);
    }
    const user = await response.json();
    return user as User;
  }

  async login(payload: { username_or_email: string; password: string }) {
    const response = await fetch(`${this.baseUrl}/auth/login`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify(payload),
    });
    if (!response.ok) {
      const text = await response.text();
      throw new Error(text || `Login failed: ${response.status}`);
    }
    const data = await response.json();
    const token = data?.access_token;
    if (!token) throw new Error('No token returned from login');

    // Fetch current user
    const meResp = await fetch(`${this.baseUrl}/auth/me`, {
      method: 'GET',
      headers: { Authorization: `Bearer ${token}` },
    });
    let user: User | null = null;
    if (meResp.ok) {
      try {
        user = await meResp.json();
      } catch (e) {
        console.warn('Failed to parse /auth/me response', e);
      }
    }

    this.saveAuth(token, user);
    return { token, user };
  }

  // -----------------
  // Connections API
  // -----------------
  async listConnections(): Promise<UserConnection[]> {
    const resp = await fetch(`${this.baseUrl}/connections/`, {
      method: 'GET',
      headers: this.getAuthHeaders(),
    });
    if (!resp.ok) throw new Error(`Failed to list connections: ${resp.status}`);
    return (await resp.json()) as UserConnection[];
  }

  async createConnection(
    payload: UserConnectionCreate,
  ): Promise<UserConnection> {
    const resp = await fetch(`${this.baseUrl}/connections/`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify(payload),
    });
    if (!resp.ok)
      throw new Error(`Failed to create connection: ${resp.status}`);
    return (await resp.json()) as UserConnection;
  }

  async updateConnection(
    id: number,
    payload: UserConnectionUpdate,
  ): Promise<UserConnection> {
    const resp = await fetch(`${this.baseUrl}/connections/${id}`, {
      method: 'PUT',
      headers: this.getAuthHeaders(),
      body: JSON.stringify(payload),
    });
    if (!resp.ok)
      throw new Error(`Failed to update connection: ${resp.status}`);
    return (await resp.json()) as UserConnection;
  }

  async deleteConnection(id: number): Promise<void> {
    const resp = await fetch(`${this.baseUrl}/connections/${id}`, {
      method: 'DELETE',
      headers: this.getAuthHeaders(),
    });
    if (!resp.ok)
      throw new Error(`Failed to delete connection: ${resp.status}`);
  }

  async testConnection(id: number): Promise<boolean> {
    const resp = await fetch(`${this.baseUrl}/connections/${id}/test`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
    });
    return resp.ok;
  }

  getSelectedConnection(): UserConnection | null {
    return this.selectedConnection;
  }

  setSelectedConnection(conn: UserConnection | null) {
    this.selectedConnection = conn;
    try {
      if (conn)
        localStorage.setItem('aigis_selected_connection', JSON.stringify(conn));
      else localStorage.removeItem('aigis_selected_connection');
    } catch (e) {
      console.warn('Failed to persist selected connection', e);
    }
  }

  // ---------------
  // CSV Import API
  // ---------------
  async uploadCsv(file: File): Promise<CsvUploadPreview> {
    const form = new FormData();
    form.append('file', file);
    const headers: Record<string, string> = {};
    if (this.token) headers['Authorization'] = `Bearer ${this.token}`;
    const resp = await fetch(`${this.baseUrl}/connections/import/csv/upload`, {
      method: 'POST',
      headers,
      body: form,
    });
    if (!resp.ok) {
      const text = await resp.text();
      throw new Error(text || `CSV upload failed: ${resp.status}`);
    }
    return (await resp.json()) as CsvUploadPreview;
  }

  async finishImportCsv(
    filename: string,
    raw: string,
    columnTypes: Record<string, string>,
  ): Promise<UserConnection> {
    const form = new FormData();
    form.append('filename', filename);
    form.append('raw', raw);
    form.append('column_types_json', JSON.stringify(columnTypes));
    const headers: Record<string, string> = {};
    if (this.token) headers['Authorization'] = `Bearer ${this.token}`;
    const resp = await fetch(`${this.baseUrl}/connections/import/csv/finish`, {
      method: 'POST',
      headers,
      body: form,
    });
    if (!resp.ok) {
      const text = await resp.text();
      throw new Error(text || `CSV import failed: ${resp.status}`);
    }
    return (await resp.json()) as UserConnection;
  }
}

export const apiService = new ApiService();

// Minimal user type returned by backend `/auth/me`
export interface User {
  id: string;
  email?: string;
  username?: string;
  is_active?: boolean;
  is_superuser?: boolean;
}

export interface UserConnection {
  id: number;
  user_id: number;
  name: string;
  db_type: 'sqlite' | 'postgres' | string;
  host?: string | null;
  port?: number | null;
  username?: string | null;
  database_name?: string | null;
  created_at: string;
  updated_at: string;
}

export interface UserConnectionCreate {
  name: string;
  db_type: 'sqlite' | 'postgres';
  host?: string | null;
  port?: number | null;
  username?: string | null;
  database_name?: string | null;
  password?: string | null;
}

export type UserConnectionUpdate = Partial<UserConnectionCreate>;

export interface CsvUploadPreview {
  filename: string;
  headers: string[];
  sample: string[][];
  raw: string;
}
