// App configuration
export const config = {
  // Convex configuration
  convexUrl: process.env.EXPO_PUBLIC_CONVEX_URL || 'https://your-convex-deployment.convex.cloud',
  
  // App metadata
  appName: 'Dotlist Lite Mobile',
  version: '1.0.0',
  
  // Feature flags
  features: {
    debugMode: __DEV__,
    analytics: false, // Enable when you want to add analytics
  },
  
  // UI configuration
  ui: {
    colors: {
      primary: '#007AFF',
      secondary: '#5856D6',
      success: '#4caf50',
      warning: '#ff9800',
      error: '#f44336',
      text: '#333',
      textSecondary: '#666',
      textPlaceholder: '#999',
      background: '#fff',
      surface: '#f8f9fa',
      border: '#e0e0e0',
    },
    spacing: {
      xs: 4,
      sm: 8,
      md: 12,
      lg: 16,
      xl: 24,
      xxl: 32,
    },
    borderRadius: {
      sm: 8,
      md: 12,
      lg: 16,
    },
  },
};