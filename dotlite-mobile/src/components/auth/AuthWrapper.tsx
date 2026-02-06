import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity, Alert } from 'react-native';
import { useAuthActions } from '@convex-dev/auth/react';
import { useConvexAuth } from 'convex/react';
import MultiListApp from '../multi-list/MultiListApp';
import LoadingSpinner from '../ui/LoadingSpinner';

export default function AuthWrapper() {
  const { isLoading, isAuthenticated } = useConvexAuth();
  const { signIn } = useAuthActions();

  const handleSignIn = async () => {
    try {
      await signIn('anonymous');
    } catch (error) {
      Alert.alert('Error', 'Failed to sign in');
      console.error('Sign in error:', error);
    }
  };

  if (isLoading) {
    return (
      <View style={styles.container}>
        <LoadingSpinner />
        <Text style={styles.loadingText}>Loading...</Text>
      </View>
    );
  }

  if (!isAuthenticated) {
    return (
      <View style={styles.container}>
        <View style={styles.authContainer}>
          <Text style={styles.title}>Dotlist Lite Mobile</Text>
          <Text style={styles.subtitle}>Simple, elegant task management</Text>
          <TouchableOpacity style={styles.signInButton} onPress={handleSignIn}>
            <Text style={styles.signInButtonText}>Get Started</Text>
          </TouchableOpacity>
        </View>
      </View>
    );
  }

  return <MultiListApp />;
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    fontSize: 16,
    color: '#666',
    marginTop: 16,
  },
  authContainer: {
    alignItems: 'center',
    paddingHorizontal: 32,
  },
  title: {
    fontSize: 32,
    fontWeight: 'bold',
    marginBottom: 8,
    textAlign: 'center',
  },
  subtitle: {
    fontSize: 18,
    color: '#666',
    marginBottom: 32,
    textAlign: 'center',
  },
  signInButton: {
    backgroundColor: '#007AFF',
    paddingHorizontal: 32,
    paddingVertical: 16,
    borderRadius: 8,
    minWidth: 200,
  },
  signInButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
    textAlign: 'center',
  },
});