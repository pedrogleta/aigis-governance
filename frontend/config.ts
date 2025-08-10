export const config = {
  // Backend API Configuration
  api: {
    baseUrl: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
    timeout: 30000, // 30 seconds
  },
  
  // Development Configuration
  dev: {
    mode: import.meta.env.VITE_DEV_MODE === 'true',
    enableMockResponses: import.meta.env.VITE_ENABLE_MOCK_RESPONSES === 'true',
  },
  
  // Feature Flags
  features: {
    enablePlots: import.meta.env.VITE_ENABLE_PLOTS !== 'false',
    enableCodeDisplay: import.meta.env.VITE_ENABLE_CODE_DISPLAY !== 'false',
    enableSessionPersistence: import.meta.env.VITE_ENABLE_SESSION_PERSISTENCE !== 'false',
  },
  
  // UI Configuration
  ui: {
    maxMessageLength: 1000,
    typingIndicatorDelay: 1000, // ms
    autoScrollDelay: 100, // ms
  }
}
