import React, { useState, useRef, useEffect } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  Alert,
  ScrollView,
  Animated,
} from 'react-native';
import { useMutation } from 'convex/react';
import { api } from '../../../convex/_generated/api';
import { Id } from '../../../convex/_generated/dataModel';

type Node = {
  _id: Id<'nodes'>;
  _creationTime: number;
  text: string;
  state: 'red' | 'yellow' | 'green';
  listId: Id<'lists'>;
  order: number;
  dueDate?: string | null;
};

interface BottomSectionProps {
  listId: Id<'lists'>;
  nodes: Node[];
}

const StateColors = {
  red: '#f44336',
  yellow: '#ff9800',
  green: '#4caf50',
};

export default function BottomSection({ listId, nodes }: BottomSectionProps) {
  const createNode = useMutation(api.lists.createNode);
  const updateNodeText = useMutation(api.lists.updateNodeText);
  const updateNodeState = useMutation(api.lists.updateNodeState);
  const deleteNode = useMutation(api.lists.deleteNode);

  const [localTexts, setLocalTexts] = useState<Record<string, string>>({});
  const [newItemText, setNewItemText] = useState('');
  const newItemInputRef = useRef<TextInput>(null);

  // Initialize local texts from nodes
  useEffect(() => {
    setLocalTexts((prev) => {
      const newLocalTexts = { ...prev };
      nodes.forEach((node) => {
        if (!(node._id in newLocalTexts)) {
          newLocalTexts[node._id] = node.text;
        }
      });
      return newLocalTexts;
    });
  }, [nodes]);

  const handleTextChange = (nodeId: Id<'nodes'>, text: string) => {
    setLocalTexts((prev) => ({ ...prev, [nodeId]: text }));
  };

  const handleTextBlur = async (nodeId: Id<'nodes'>, text: string) => {
    try {
      await updateNodeText({ nodeId, text });
    } catch (error) {
      console.error('Failed to update node text:', error);
    }
  };

  const handleStateChange = async (nodeId: Id<'nodes'>, currentState: Node['state']) => {
    const states: Node['state'][] = ['red', 'yellow', 'green'];
    const currentIndex = states.indexOf(currentState);
    const nextState = states[(currentIndex + 1) % states.length];
    
    try {
      await updateNodeState({ nodeId, state: nextState });
    } catch (error) {
      console.error('Failed to update node state:', error);
    }
  };

  const handleDeleteNode = (nodeId: Id<'nodes'>) => {
    Alert.alert(
      'Delete Item',
      'Are you sure you want to delete this item?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: async () => {
            try {
              await deleteNode({ nodeId });
              setLocalTexts((prev) => {
                const newLocalTexts = { ...prev };
                delete newLocalTexts[nodeId];
                return newLocalTexts;
              });
            } catch (error) {
              console.error('Failed to delete node:', error);
            }
          },
        },
      ]
    );
  };

  const handleCreateNode = async () => {
    if (!newItemText.trim()) return;

    try {
      const nodeId = await createNode({
        listId,
        text: newItemText.trim(),
        state: 'red' as const,
      });
      setNewItemText('');
      setLocalTexts((prev) => ({ ...prev, [nodeId]: newItemText.trim() }));
    } catch (error) {
      console.error('Failed to create node:', error);
      Alert.alert('Error', 'Failed to create item');
    }
  };

  const sortedNodes = [...nodes].sort((a, b) => a.order - b.order);

  return (
    <View style={styles.container}>
      {/* Add new item input */}
      <View style={styles.newItemContainer}>
        <TextInput
          ref={newItemInputRef}
          style={styles.newItemInput}
          value={newItemText}
          onChangeText={setNewItemText}
          placeholder="Add a new item..."
          placeholderTextColor="#999"
          multiline
          textAlignVertical="top"
          onSubmitEditing={handleCreateNode}
          blurOnSubmit={false}
        />
        <TouchableOpacity
          style={[styles.addButton, !newItemText.trim() && styles.addButtonDisabled]}
          onPress={handleCreateNode}
          disabled={!newItemText.trim()}
        >
          <Text style={styles.addButtonText}>+</Text>
        </TouchableOpacity>
      </View>

      {/* List of items */}
      <ScrollView style={styles.itemsContainer}>
        {sortedNodes.map((node) => (
          <Animated.View key={node._id} style={styles.itemRow}>
            <TouchableOpacity
              style={[styles.stateButton, { backgroundColor: StateColors[node.state] }]}
              onPress={() => handleStateChange(node._id, node.state)}
            >
              <View style={styles.stateButtonInner} />
            </TouchableOpacity>

            <TextInput
              style={styles.itemInput}
              value={localTexts[node._id] ?? node.text}
              onChangeText={(text) => handleTextChange(node._id, text)}
              onBlur={() => handleTextBlur(node._id, localTexts[node._id] ?? node.text)}
              multiline
              textAlignVertical="top"
              placeholder="Enter item text..."
              placeholderTextColor="#999"
            />

            <TouchableOpacity
              style={styles.deleteButton}
              onPress={() => handleDeleteNode(node._id)}
            >
              <Text style={styles.deleteButtonText}>🗑</Text>
            </TouchableOpacity>
          </Animated.View>
        ))}
      </ScrollView>

      {sortedNodes.length === 0 && (
        <View style={styles.emptyState}>
          <Text style={styles.emptyStateText}>No items yet.</Text>
          <Text style={styles.emptyStateSubtext}>Add your first item above!</Text>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  newItemContainer: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 16,
    backgroundColor: '#f8f9fa',
    borderRadius: 12,
    padding: 12,
    borderWidth: 1,
    borderColor: '#e0e0e0',
  },
  newItemInput: {
    flex: 1,
    fontSize: 16,
    paddingRight: 12,
    minHeight: 40,
    maxHeight: 120,
  },
  addButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#007AFF',
    justifyContent: 'center',
    alignItems: 'center',
  },
  addButtonDisabled: {
    backgroundColor: '#ccc',
  },
  addButtonText: {
    color: '#fff',
    fontSize: 20,
    fontWeight: 'bold',
  },
  itemsContainer: {
    flex: 1,
  },
  itemRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 12,
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 12,
    borderWidth: 1,
    borderColor: '#e0e0e0',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  stateButton: {
    width: 24,
    height: 24,
    borderRadius: 12,
    marginRight: 12,
    marginTop: 8,
    justifyContent: 'center',
    alignItems: 'center',
  },
  stateButtonInner: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: 'rgba(255, 255, 255, 0.8)',
  },
  itemInput: {
    flex: 1,
    fontSize: 16,
    paddingRight: 12,
    minHeight: 40,
    maxHeight: 120,
    paddingTop: 8,
  },
  deleteButton: {
    width: 40,
    height: 40,
    justifyContent: 'center',
    alignItems: 'center',
    marginTop: 4,
  },
  deleteButtonText: {
    fontSize: 16,
  },
  emptyState: {
    alignItems: 'center',
    marginTop: 40,
    paddingHorizontal: 32,
  },
  emptyStateText: {
    fontSize: 18,
    fontWeight: '600',
    color: '#666',
    marginBottom: 8,
  },
  emptyStateSubtext: {
    fontSize: 14,
    color: '#999',
    textAlign: 'center',
  },
});