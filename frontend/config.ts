import dotenv from 'dotenv';

// Load environment variables from .env file
dotenv.config();

// Helper function to get environment variables with proper typing
function getEnvVar(key: string, defaultValue?: string): string {
  const value = process.env[key];
  if (value === undefined && defaultValue === undefined) {
    throw new Error(`Environment variable ${key} is required but not set`);
  }
  return value || defaultValue!;
}

// Helper function to get boolean environment variables
function getBoolEnvVar(key: string, defaultValue: boolean = false): boolean {
  const value = getEnvVar(key, defaultValue.toString());
  return value === 'true';
}

export const config = {
  // Backend API Configuration
  api: {
    baseUrl: getEnvVar('VITE_API_BASE_URL', 'http://localhost:8000'),
    timeout: 30000, // 30 seconds
  },

  // Development Configuration
  dev: {
    mode: getBoolEnvVar('VITE_DEV_MODE', false),
    enableMockResponses: getBoolEnvVar('VITE_ENABLE_MOCK_RESPONSES', false),
  },

  // Feature Flags
  features: {
    enablePlots: getBoolEnvVar('VITE_ENABLE_PLOTS', true),
    enableCodeDisplay: getBoolEnvVar('VITE_ENABLE_CODE_DISPLAY', true),
    enableSessionPersistence: getBoolEnvVar(
      'VITE_ENABLE_SESSION_PERSISTENCE',
      true,
    ),
  },

  // UI Configuration
  ui: {
    maxMessageLength: 1000,
    typingIndicatorDelay: 1000, // ms
    autoScrollDelay: 100, // ms
  },
};
