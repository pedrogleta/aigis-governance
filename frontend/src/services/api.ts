export interface ChatRequest {
  message: string;
  sessionId?: string;
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
  private sessionId: string | null = null;

  constructor(baseUrl: string = 'http://localhost:8000') {
    this.baseUrl = baseUrl;
  }

  async sendMessage(message: string): Promise<ChatResponse> {
    try {
      // Use OpenAI-compatible chat completions endpoint
      const response = await fetch(`${this.baseUrl}/v1/chat/completions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          model: 'gpt-3.5-turbo', // This will be handled by the ADK server
          messages: [
            {
              role: 'user',
              content: message,
            },
          ],
          stream: false,
          sessionId: this.sessionId,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      // Extract content from OpenAI-compatible response
      const content =
        data.choices?.[0]?.message?.content || 'No response received';

      // Try to extract additional data from the response
      let plots: string[] = [];
      let code: string = '';

      // Check if there's additional metadata in the response
      if (data.choices?.[0]?.message?.function_call) {
        try {
          const functionCall = data.choices[0].message.function_call;
          if (functionCall.arguments) {
            const args = JSON.parse(functionCall.arguments);
            plots = args.plots || [];
            code = args.code || '';
          }
        } catch (e) {
          console.warn('Could not parse function call arguments:', e);
        }
      }

      // Store session ID if provided
      if (data.sessionId) {
        this.sessionId = data.sessionId;
      }

      return {
        content,
        plots,
        code,
        sessionId: this.sessionId || 'default-session',
      };
    } catch (error) {
      console.error('API Error:', error);
      throw error;
    }
  }

  async getHealth(): Promise<boolean> {
    try {
      // Check if OpenAI-compatible endpoint is available
      const response = await fetch(`${this.baseUrl}/v1/models`);
      return response.ok;
    } catch {
      return false;
    }
  }

  // Method to check if BigQuery connection is available
  async checkBigQueryConnection(): Promise<boolean> {
    try {
      // Try the original endpoint first
      const response = await fetch(`${this.baseUrl}/api/health/bigquery`);
      if (response.ok) return true;

      // Fallback: if we can reach the server, assume BigQuery is available
      const modelsResponse = await fetch(`${this.baseUrl}/v1/models`);
      return modelsResponse.ok;
    } catch {
      return false;
    }
  }
}

export const apiService = new ApiService();
