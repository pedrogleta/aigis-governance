export interface ChatRequest {
  message: string
  sessionId?: string
}

export interface ChatResponse {
  content: string
  plots?: string[]
  code?: string
  sessionId: string
  error?: string
}

export class ApiService {
  private baseUrl: string
  private sessionId: string | null = null

  constructor(baseUrl: string = 'http://localhost:8000') {
    this.baseUrl = baseUrl
  }

  async sendMessage(message: string): Promise<ChatResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message,
          sessionId: this.sessionId,
        } as ChatRequest),
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data: ChatResponse = await response.json()
      
      // Store session ID for future requests
      if (data.sessionId) {
        this.sessionId = data.sessionId
      }

      return data
    } catch (error) {
      console.error('API Error:', error)
      throw error
    }
  }

  async getHealth(): Promise<boolean> {
    try {
      const response = await fetch(`${this.baseUrl}/health`)
      return response.ok
    } catch {
      return false
    }
  }

  // Method to check if BigQuery connection is available
  async checkBigQueryConnection(): Promise<boolean> {
    try {
      const response = await fetch(`${this.baseUrl}/api/health/bigquery`)
      return response.ok
    } catch {
      return false
    }
  }
}

export const apiService = new ApiService()
