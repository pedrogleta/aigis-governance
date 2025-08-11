// ADK API Service for chat and session management

export interface ChatRequest {
  message: string;
}

export interface ChatResponse {
  content: string;
  plots?: string[];
  code?: string;
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

  // Send a chat message to the ADK agent
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
      // Parse response (assuming a simple text reply in data, adapt as needed)
      let content = '';
      let plots: string[] = [];
      let code = '';
      if (data && data.reply) {
        // If ADK returns a reply object
        if (typeof data.reply === 'string') {
          content = data.reply;
        } else if (data.reply.parts && Array.isArray(data.reply.parts)) {
          // If reply is in parts
          content = data.reply.parts.map((p: any) => p.text).join('\n');
        }
        if (data.reply.plots) plots = data.reply.plots;
        if (data.reply.code) code = data.reply.code;
      } else if (data && data.parts && Array.isArray(data.parts)) {
        content = data.parts.map((p: any) => p.text).join('\n');
      } else if (typeof data === 'string') {
        content = data;
      } else {
        content = JSON.stringify(data);
      }
      return {
        content,
        plots,
        code,
        sessionId: sessionId,
      };
    } catch (error: any) {
      console.error('API Error:', error);
      return {
        content: '',
        plots: [],
        code: '',
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
