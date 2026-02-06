import React from 'react';
import { StatusBar } from 'expo-status-bar';
import { ConvexAuthProvider } from '@convex-dev/auth/react';
import { ConvexReactClient } from 'convex/react';
import { NavigationContainer } from '@react-navigation/native';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import AuthWrapper from './src/components/auth/AuthWrapper';
import ErrorBoundary from './src/components/ui/ErrorBoundary';
import { config } from './src/config/app';

const convex = new ConvexReactClient(config.convexUrl);

export default function App() {
  return (
    <ErrorBoundary>
      <SafeAreaProvider>
        <ConvexAuthProvider client={convex}>
          <NavigationContainer>
            <AuthWrapper />
            <StatusBar style="auto" />
          </NavigationContainer>
        </ConvexAuthProvider>
      </SafeAreaProvider>
    </ErrorBoundary>
  );
}
