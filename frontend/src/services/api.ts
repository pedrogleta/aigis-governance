// ADK API Service for chat and session management
import { z } from 'zod';
import { MinioService } from './minio';

// Zod schemas for streaming responses
const FunctionCallSchema = z.object({
  id: z.string(),
  args: z.record(z.string(), z.unknown()),
  name: z.string(),
});

const FunctionResponseSchema = z.object({
  id: z.string(),
  name: z.string(),
  response: z.object({
    result: z.string(),
  }),
});

const PartSchema = z.union([
  z.object({ text: z.string() }),
  z.object({ functionCall: FunctionCallSchema }),
  z.object({ functionResponse: FunctionResponseSchema }),
]);

const ContentSchema = z.object({
  parts: z.array(PartSchema),
  role: z.string(),
});

const UsageMetadataSchema = z.object({
  candidatesTokenCount: z.number().optional(),
  candidatesTokensDetails: z
    .array(
      z.object({
        modality: z.string(),
        tokenCount: z.number(),
      }),
    )
    .optional(),
  promptTokenCount: z.number().optional(),
  promptTokensDetails: z
    .array(
      z.object({
        modality: z.string(),
        tokenCount: z.number(),
      }),
    )
    .optional(),
  thoughtsTokenCount: z.number().optional(),
  totalTokenCount: z.number().optional(),
  trafficType: z.string().optional(),
});

const ActionsSchema = z.object({
  stateDelta: z.record(z.string(), z.unknown()).optional(),
  artifactDelta: z.record(z.string(), z.unknown()).optional(),
  requestedAuthConfigs: z.record(z.string(), z.unknown()).optional(),
});

// Schema for content messages (with content.parts)
const ContentMessageSchema = z.object({
  content: ContentSchema,
  usageMetadata: UsageMetadataSchema.optional(),
  invocationId: z.string().optional(),
  author: z.string().optional(),
  actions: ActionsSchema.optional(),
  longRunningToolIds: z.array(z.string()).optional(),
  id: z.string(),
  timestamp: z.number(),
  partial: z.boolean().optional(),
});

// Union schema for all possible SSE message types
const SSEMessageSchema = ContentMessageSchema;

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

export type StreamingMessage =
  | FunctionCallMessage
  | FunctionResponseMessage
  | TextMessage
  | PlotMessage;

const CreateSessionResponseSchema = z.object({
  id: z.uuid(),
  appName: z.string(),
  userId: z.string(),
  state: z.record(z.string(), z.unknown()),
  events: z.array(z.unknown()),
  lastUpdateTime: z.number(),
});

// type CreateSessionResponse = z.infer<typeof CreateSessionResponseSchema>;

export class ApiService {
  private baseUrl: string;
  private appName: string;
  private userId: string;
  private sessionId: string = '';
  private token: string | null = null;
  private currentUser: User | null = null;
  private initialFileCount: number = 0;

  constructor(
    baseUrl: string = 'http://localhost:8000',
    appName = 'data_science',
    userId = 'u_123',
  ) {
    this.baseUrl = baseUrl;
    this.appName = appName;
    this.userId = userId;
    this.initializeFileCount();
    // Load auth state from localStorage
    try {
      const stored = localStorage.getItem('aigis_token');
      if (stored) this.token = stored;
      const userJson = localStorage.getItem('aigis_user');
      if (userJson) this.currentUser = JSON.parse(userJson);
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
    try {
      localStorage.removeItem('aigis_token');
      localStorage.removeItem('aigis_user');
    } catch (e) {
      console.warn('Failed to clear auth from localStorage', e);
    }
  }

  private getAuthHeaders(contentType = 'application/json') {
    const headers: Record<string, string> = { 'Content-Type': contentType };
    if (this.token) headers['Authorization'] = `Bearer ${this.token}`;
    return headers;
  }

  // Initialize the file count from MinIO
  private async initializeFileCount(): Promise<void> {
    try {
      await MinioService.ensureBucket();
      this.initialFileCount = await MinioService.getFileCount();
      console.log('Initial MinIO file count:', this.initialFileCount);
    } catch (error) {
      console.error('Error initializing file count:', error);
      this.initialFileCount = 0;
    }
  }

  // Get the current file count from MinIO
  async getCurrentFileCount(): Promise<number> {
    try {
      return await MinioService.getFileCount();
    } catch (error) {
      console.error('Error getting current file count:', error);
      return this.initialFileCount;
    }
  }

  // Check if new files were added and get the latest one
  async checkForNewFiles(): Promise<string | null> {
    try {
      const currentCount = await this.getCurrentFileCount();
      if (currentCount > this.initialFileCount) {
        // New files were added, get the latest one
        const latestFile = await MinioService.getLatestFile();
        if (latestFile) {
          // Update the initial count to the current count
          this.initialFileCount = currentCount;
          return latestFile;
        }
      }
      return null;
    } catch (error) {
      console.error('Error checking for new files:', error);
      return null;
    }
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

    try {
      const createSessionResponse = CreateSessionResponseSchema.parse(data);
      return createSessionResponse.id;
    } catch (error) {
      console.error('API response did not match expected schema:', error);
      throw new Error('Invalid data received from server');
    }
  }

  // Send a chat message to the ADK agent with streaming support
  async sendMessageStreaming(
    message: string,
    onChunk: (chunk: StreamingMessage) => void,
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
      const plots: string[] = [];
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
                const data = JSON.parse(line.slice(6));

                // Validate the data with Zod schema
                const validatedData = SSEMessageSchema.parse(data);

                // Only process messages that have actual content to display
                if (
                  'content' in validatedData &&
                  validatedData.content &&
                  validatedData.content.parts
                ) {
                  console.log('Processing content message:', validatedData);
                  // This is a content message with parts - we know these fields exist due to schema validation
                  const contentData = validatedData as z.infer<
                    typeof ContentMessageSchema
                  >;
                  const timestamp = new Date(contentData.timestamp * 1000);
                  const isPartial = contentData.partial === true;

                  // Process each part
                  for (const part of validatedData.content.parts) {
                    if ('text' in part && part.text) {
                      // Only display text chunks when they're partial (streaming)
                      // When partial: false, the backend sends the complete message again,
                      // so we don't want to display it as a duplicate chunk
                      if (isPartial) {
                        console.log(
                          'Processing text part:',
                          part.text,
                          'partial:',
                          isPartial,
                        );
                        const textMessage: TextMessage = {
                          type: 'text',
                          content: part.text,
                          partial: true,
                          timestamp,
                        };
                        onChunk(textMessage);

                        finalTextContent += part.text;
                        console.log(
                          'Accumulated final text:',
                          finalTextContent,
                        );
                      }
                    } else if ('functionCall' in part) {
                      console.log(
                        'Processing function call:',
                        part.functionCall,
                      );
                      const functionCallMessage: FunctionCallMessage = {
                        type: 'functionCall',
                        id: part.functionCall.id,
                        name: part.functionCall.name,
                        args: part.functionCall.args,
                        timestamp,
                      };
                      onChunk(functionCallMessage);
                    } else if ('functionResponse' in part) {
                      console.log(
                        'Processing function response:',
                        part.functionResponse,
                      );
                      const functionResponseMessage: FunctionResponseMessage = {
                        type: 'functionResponse',
                        id: part.functionResponse.id,
                        name: part.functionResponse.name,
                        result: part.functionResponse.response.result,
                        timestamp,
                      };
                      onChunk(functionResponseMessage);

                      // Check if new plots were generated
                      try {
                        const newFile = await this.checkForNewFiles();
                        if (newFile) {
                          console.log('New plot file detected:', newFile);
                          // Create a plot message to display the image
                          const plotMessage: PlotMessage = {
                            type: 'plot',
                            filename: newFile,
                            timestamp,
                          };
                          onChunk(plotMessage);
                        }
                      } catch (error) {
                        console.error('Error checking for new plots:', error);
                      }
                    }
                  }
                }

                // Handle artifacts if they exist
                // if (
                //   validatedData.actions &&
                //   validatedData.actions.artifactDelta
                // ) {
                //   console.log(
                //     'Artifacts found:',
                //     validatedData.actions.artifactDelta,
                //   );
                // }
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
          plots,
          sessionId: sessionId,
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
        headers: this.getAuthHeaders('application/json'),
        body: JSON.stringify(payload),
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();

      // Parse ADK API response - it returns an array of objects
      let content = '';
      const plots: string[] = [];

      if (Array.isArray(data) && data.length > 0) {
        // Look for the content object (usually the second one with role: "model")
        const contentObject = data.find((item: Record<string, unknown>) => {
          const content = item.content;
          return (
            content &&
            typeof content === 'object' &&
            content !== null &&
            'parts' in content &&
            Array.isArray((content as Record<string, unknown>).parts)
          );
        });

        if (
          contentObject &&
          typeof contentObject.content === 'object' &&
          contentObject.content &&
          'parts' in contentObject.content &&
          Array.isArray(
            (contentObject.content as Record<string, unknown>).parts,
          )
        ) {
          // Extract text from all parts
          const parts = (contentObject.content as Record<string, unknown>)
            .parts as Array<Record<string, unknown>>;
          content = parts
            .map((part: Record<string, unknown>) =>
              typeof part === 'object' && part && 'text' in part
                ? String(part.text || '')
                : '',
            )
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
    } catch (error: unknown) {
      console.error('API Error:', error);
      return {
        content: '',
        plots: [],
        sessionId: this.sessionId || '',
        error: error instanceof Error ? error.message : 'Unknown error',
      };
    }
  }

  async getHealth(): Promise<boolean> {
    try {
      // Check if endpoint is available
      const response = await fetch(`${this.baseUrl}/list-apps`, {
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
      // Check if we can reach the ADK server by trying to list apps
      const response = await fetch(`${this.baseUrl}/list-apps`, {
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
