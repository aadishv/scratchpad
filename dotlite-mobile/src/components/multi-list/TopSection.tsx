import React, { useState, useEffect } from 'react';
import { 
  View, 
  Text, 
  TextInput, 
  TouchableOpacity, 
  StyleSheet, 
  Alert,
  Modal,
  ScrollView,
  Pressable
} from 'react-native';
import { useMutation } from 'convex/react';
import { api } from '../../../convex/_generated/api';
import { Id } from '../../../convex/_generated/dataModel';

type List = {
  _id: Id<'lists'>;
  _creationTime: number;
  name: string;
  userId: Id<'users'>;
  order: number;
};

interface TopSectionProps {
  lists: List[];
  selectedList: List;
  setSelectedListId: (id: Id<'lists'>) => void;
}

export default function TopSection({
  lists,
  selectedList,
  setSelectedListId,
}: TopSectionProps) {
  const updateListName = useMutation(api.lists.updateListName);
  const createList = useMutation(api.lists.createList);
  const deleteList = useMutation(api.lists.deleteList);

  const [listName, setListName] = useState(selectedList.name);
  const [showListSelector, setShowListSelector] = useState(false);

  // Update local state when selected list changes
  useEffect(() => {
    setListName(selectedList.name);
  }, [selectedList.name]);

  const handleListNameChange = async (newName: string) => {
    setListName(newName);
    try {
      await updateListName({
        listId: selectedList._id,
        name: newName,
      });
    } catch (error) {
      console.error('Failed to update list name:', error);
    }
  };

  const handleCreateList = async () => {
    try {
      const newListId = await createList({ name: 'New List' });
      setSelectedListId(newListId);
      setShowListSelector(false);
    } catch (error) {
      console.error('Failed to create list:', error);
      Alert.alert('Error', 'Failed to create list');
    }
  };

  const handleDeleteList = () => {
    if (lists.length === 1) {
      Alert.alert('Cannot Delete', 'You must have at least one list.');
      return;
    }

    Alert.alert(
      'Delete List',
      `Are you sure you want to delete "${selectedList.name}"? This cannot be undone.`,
      [
        { text: 'Cancel', style: 'cancel' },
        { 
          text: 'Delete', 
          style: 'destructive',
          onPress: async () => {
            try {
              await deleteList({ listId: selectedList._id });
              const remainingLists = lists.filter((l) => l._id !== selectedList._id);
              if (remainingLists.length > 0) {
                setSelectedListId(remainingLists[0]._id);
              }
            } catch (error) {
              console.error('Failed to delete list:', error);
              Alert.alert('Error', 'Failed to delete list');
            }
          }
        }
      ]
    );
  };

  return (
    <View style={styles.container}>
      <View style={styles.headerRow}>
        <TextInput
          style={styles.titleInput}
          value={listName}
          onChangeText={setListName}
          onBlur={() => handleListNameChange(listName)}
          placeholder="List name goes here"
          placeholderTextColor="#999"
          multiline={false}
          numberOfLines={1}
        />
        <TouchableOpacity 
          style={styles.menuButton}
          onPress={() => setShowListSelector(true)}
        >
          <Text style={styles.menuButtonText}>⋮</Text>
        </TouchableOpacity>
      </View>

      <Modal
        visible={showListSelector}
        transparent={true}
        animationType="slide"
        onRequestClose={() => setShowListSelector(false)}
      >
        <Pressable 
          style={styles.modalOverlay} 
          onPress={() => setShowListSelector(false)}
        >
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Lists</Text>
              <TouchableOpacity 
                onPress={() => setShowListSelector(false)}
                style={styles.closeButton}
              >
                <Text style={styles.closeButtonText}>✕</Text>
              </TouchableOpacity>
            </View>
            
            <ScrollView style={styles.listContainer}>
              {lists.map((list) => (
                <TouchableOpacity
                  key={list._id}
                  style={[
                    styles.listItem,
                    selectedList._id === list._id && styles.selectedListItem
                  ]}
                  onPress={() => {
                    setSelectedListId(list._id);
                    setShowListSelector(false);
                  }}
                >
                  <Text style={[
                    styles.listItemText,
                    selectedList._id === list._id && styles.selectedListItemText
                  ]}>
                    {list.name || 'Untitled'}
                  </Text>
                </TouchableOpacity>
              ))}
            </ScrollView>

            <View style={styles.modalActions}>
              <TouchableOpacity
                style={styles.actionButton}
                onPress={handleCreateList}
              >
                <Text style={styles.actionButtonText}>+ Create New List</Text>
              </TouchableOpacity>
              
              <TouchableOpacity
                style={[styles.actionButton, styles.deleteButton]}
                onPress={handleDeleteList}
              >
                <Text style={[styles.actionButtonText, styles.deleteButtonText]}>
                  🗑 Delete Current List
                </Text>
              </TouchableOpacity>
            </View>
          </View>
        </Pressable>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    marginBottom: 24,
  },
  headerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  titleInput: {
    flex: 1,
    fontSize: 28,
    fontWeight: 'bold',
    padding: 8,
    marginRight: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  menuButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#f0f0f0',
    justifyContent: 'center',
    alignItems: 'center',
  },
  menuButtonText: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#666',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  modalContent: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    margin: 32,
    maxHeight: '80%',
    minWidth: '80%',
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
    paddingBottom: 12,
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: 'bold',
  },
  closeButton: {
    width: 30,
    height: 30,
    borderRadius: 15,
    backgroundColor: '#f0f0f0',
    justifyContent: 'center',
    alignItems: 'center',
  },
  closeButtonText: {
    fontSize: 16,
    color: '#666',
  },
  listContainer: {
    maxHeight: 300,
  },
  listItem: {
    padding: 12,
    borderRadius: 8,
    marginVertical: 2,
  },
  selectedListItem: {
    backgroundColor: '#e3f2fd',
  },
  listItemText: {
    fontSize: 16,
    color: '#333',
  },
  selectedListItemText: {
    fontWeight: '600',
    color: '#1976d2',
  },
  modalActions: {
    marginTop: 16,
    paddingTop: 16,
    borderTopWidth: 1,
    borderTopColor: '#e0e0e0',
  },
  actionButton: {
    padding: 12,
    borderRadius: 8,
    marginVertical: 4,
    backgroundColor: '#f0f0f0',
  },
  deleteButton: {
    backgroundColor: '#ffebee',
  },
  actionButtonText: {
    fontSize: 16,
    fontWeight: '600',
    textAlign: 'center',
    color: '#333',
  },
  deleteButtonText: {
    color: '#d32f2f',
  },
});