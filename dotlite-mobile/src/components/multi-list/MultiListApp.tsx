import React, { useState, useEffect, useMemo } from 'react';
import { View, Text, StyleSheet, ScrollView } from 'react-native';
import { useQuery, useMutation } from 'convex/react';
import { SafeAreaView } from 'react-native-safe-area-context';
import { api } from '../../../convex/_generated/api';
import { Id } from '../../../convex/_generated/dataModel';
import TopSection from './TopSection';
import BottomSection from './BottomSection';

type List = {
  _id: Id<'lists'>;
  _creationTime: number;
  name: string;
  userId: Id<'users'>;
  order: number;
};

export default function MultiListApp() {
  const listsQuery = useQuery(api.lists.getLists, {});
  const lists = useMemo(() => listsQuery ?? [], [listsQuery]);
  const initializeUserLists = useMutation(api.lists.initializeUserLists);

  const [selectedListId, setSelectedListId] = useState<Id<'lists'> | null>(null);

  // Initialize user lists if none exist
  useEffect(() => {
    if (lists.length === 0 && selectedListId === null) {
      initializeUserLists().then((listId) => {
        setSelectedListId(listId);
      }).catch((error) => {
        console.error('Failed to initialize lists:', error);
      });
    } else if (lists.length > 0 && selectedListId === null) {
      setSelectedListId(lists[0]._id);
    }
  }, [lists, selectedListId, initializeUserLists]);

  // Update selected list if it gets deleted
  useEffect(() => {
    if (selectedListId && !lists.find(l => l._id === selectedListId)) {
      setSelectedListId(lists.length > 0 ? lists[0]._id : null);
    }
  }, [lists, selectedListId]);

  const selectedList = lists.find(l => l._id === selectedListId);
  const nodes = useQuery(
    api.lists.getNodes,
    selectedListId ? { listId: selectedListId } : 'skip'
  ) ?? [];

  if (!selectedList || !selectedListId) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.loadingContainer}>
          <Text style={styles.loadingText}>Loading...</Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView style={styles.scrollView} contentContainerStyle={styles.contentContainer}>
        <TopSection
          lists={lists}
          selectedList={selectedList}
          setSelectedListId={setSelectedListId}
        />
        <BottomSection listId={selectedListId} nodes={nodes} />
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
  },
  scrollView: {
    flex: 1,
  },
  contentContainer: {
    padding: 16,
    paddingTop: 32,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    fontSize: 16,
    color: '#666',
  },
});