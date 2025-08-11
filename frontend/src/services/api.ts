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

      // Parse ADK API response - it returns an array of objects
      let content = '';
      let plots: string[] = [];
      let code = '';

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
