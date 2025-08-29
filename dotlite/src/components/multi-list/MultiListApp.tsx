import { useState, useEffect, useMemo } from 'react';
import { useQuery, useMutation } from 'convex/react';
import { api } from '../../../convex/_generated/api';
import { Id } from '../../../convex/_generated/dataModel';
import { Card, CardContent } from '../ui/card';
import TopSection from './TopSection';
// import MiddleSection from './MiddleSection';
import BottomSection from './BottomSection';

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
      <div className="container mx-auto max-w-4xl py-8 px-4">
        <Card>
          <CardContent className="flex items-center justify-center py-12">
            <div className="text-center text-muted-foreground">Loading...</div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <main className="container mx-auto max-w-4xl py-8 mt-10 px-4 space-y-2">
      <TopSection
        lists={lists}
        selectedList={selectedList}
        setSelectedListId={setSelectedListId}
      />
      {/*<MiddleSection nodes={nodes} />*/}
      <BottomSection listId={selectedListId} nodes={nodes} />
    </main>
  );
}
