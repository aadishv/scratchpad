import { useState, useEffect, useMemo } from "react";
import { useMutation, useQuery } from "convex/react";
import { api } from "../../../convex/_generated/api";
import { Id } from "../../../convex/_generated/dataModel";
import { Button } from "../ui/button";
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
} from "../ui/dropdown-menu";
import { ChevronDown, Plus, Trash2, GripVertical, Settings } from "lucide-react";
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "../ui/dialog";
import { ShareLinkComponent } from "./ShareLink";
// webcal://brainy-emu-524.convex.site/calendar?k570tr8q5evckdvh24ydj6sczn7mefkz
type List = {
  _id: Id<"lists">;
  _creationTime: number;
  name: string;
  userId: Id<"users">;
  order: number;
};

interface TopSectionProps {
  lists: List[];
  selectedList: List;
  setSelectedListId: (id: Id<"lists">) => void;
}

export default function TopSection({
  lists,
  selectedList,
  setSelectedListId,
}: TopSectionProps) {
  const updateListName = useMutation(api.lists.updateListName);
  const createList = useMutation(api.lists.createList);
  const deleteList = useMutation(api.lists.deleteList);
  const reorderLists = useMutation(api.lists.reorderLists);

  const user = useQuery(api.myFunctions.getUser) ?? null;

  const [listName, setListName] = useState(selectedList.name);
  const [draggedIdx, setDraggedIdx] = useState<number | null>(null);
  const [dragOverIdx, setDragOverIdx] = useState<number | null>(null);

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
      console.error("Failed to update list name:", error);
    }
  };

  const handleCreateList = async () => {
    try {
      const newListId = await createList({ name: "New List" });
      setSelectedListId(newListId);
      setTimeout(() => {
        const input = document.getElementById("list-name-input");
        if (input) {
          (input as HTMLInputElement).focus();
          (input as HTMLInputElement).select();
        }
      }, 100);
    } catch (error) {
      console.error("Failed to create list:", error);
    }
  };

  const handleReorderLists = async (fromIdx: number, toIdx: number) => {
    const reorderedLists = [...lists];
    const [removed] = reorderedLists.splice(fromIdx, 1);
    reorderedLists.splice(toIdx, 0, removed);

    try {
      await reorderLists({
        listIds: reorderedLists.map((list) => list._id),
      });
    } catch (error) {
      console.error("Failed to reorder lists:", error);
    }
  };

  const handleDeleteList = async () => {
    try {
      await deleteList({ listId: selectedList._id });
      // After deletion, set selected list to the first available list
      const remainingLists = lists.filter((l) => l._id !== selectedList._id);
      if (remainingLists.length > 0) {
        setSelectedListId(remainingLists[0]._id);
      }
    } catch (error) {
      console.error("Failed to delete list:", error);
    }
  };

  const calendarUrl = useMemo(() => {
    if (user == null || user.id == null) {
      return;
    }
    let convex_url = (import.meta.env as any).VITE_CONVEX_URL;
    convex_url = convex_url.replace('https://', 'webcal://');
    convex_url = convex_url.replace('.convex.cloud', '.convex.site');
    convex_url += `/calendar?${user.id}`;
    console.log(convex_url);
    return convex_url;
  }, [user]);

  return (
    <div className="relative flex items-center gap-2">
      <input
        id="list-name-input"
        className="!text-3xl border-none outline-none w-full bg-transparent p-2 font-serif placeholder:text-gray-500"
        value={listName}
        onChange={(e) => setListName(e.target.value)}
        onBlur={(e) => void handleListNameChange(e.target.value)}
        placeholder="list name goes here"
      />

      <Dialog>
        <DialogTrigger className="">
          <Button variant="ghost">
            <Settings className="w-4 h-4" />
          </Button>
        </DialogTrigger>

        <DialogContent>
          <DialogHeader>
            <DialogTitle className="text-2xl">Settings</DialogTitle>
            <DialogDescription>
             <h2 className="font-serif text-lg">Calendar integration</h2>
             <p><b>For Google Calendar: </b>
               Go to Settings &gt; Add Calendar &gt; From URL and enter the below link.</p>
             <p><b>For other calendars: </b>
               Similarly, look for the option to import an iCal calendar and use the link below.</p>
             <p><b>Don't share this link with other users; they can use this link to access your todos.</b></p>
             <ShareLinkComponent link={calendarUrl} />
            </DialogDescription>
          </DialogHeader>
        </DialogContent>
      </Dialog>

      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="ghost" size="icon" className="shrink-0">
            <ChevronDown className="w-4 h-4" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent
          align="end"
          className="flex-col space-y-1 w-56 border-[0.1px]"
        >
          {lists.map((list, idx) => (
            <DropdownMenuItem
              key={list._id}
              onClick={() => setSelectedListId(list._id)}
              className={`
                flex items-center justify-between cursor-pointer
                ${selectedList._id === list._id ? "bg-accent font-medium" : ""}
                ${dragOverIdx === idx && draggedIdx !== null && draggedIdx !== idx ? "bg-accent/50" : ""}
              `}
              draggable
              onDragStart={(e: React.DragEvent) => {
                setDraggedIdx(idx);
                e.dataTransfer.effectAllowed = "move";
              }}
              onDragOver={(e: React.DragEvent) => {
                e.preventDefault();
                setDragOverIdx(idx);
              }}
              onDrop={(e: React.DragEvent) => {
                e.preventDefault();
                if (draggedIdx !== null && draggedIdx !== idx) {
                  void handleReorderLists(draggedIdx, idx);
                }
                setDraggedIdx(null);
                setDragOverIdx(null);
              }}
              onDragEnd={() => {
                setDraggedIdx(null);
                setDragOverIdx(null);
              }}
              style={{
                opacity: draggedIdx === idx ? 0.5 : 1,
                userSelect: "none",
              }}
            >
              <span className="flex-1 truncate">
                {list.name || (
                  <span className="italic text-muted-foreground">Untitled</span>
                )}
              </span>
              <GripVertical className="w-4 h-4 text-muted-foreground/50" />
            </DropdownMenuItem>
          ))}

          <DropdownMenuItem
            onClick={() => void handleCreateList()}
            className="text-sm"
          >
            <Plus className="w-4 h-4 mr-2" />
            Create New List
          </DropdownMenuItem>

          {/*<DropdownMenuItem
            onClick={() => void handleDeleteList()}
            className="text-sm text-destructive focus:text-destructive"
          >
            <Trash2 className="w-4 h-4 mr-2" />
            Delete Current List
          </DropdownMenuItem>*/}
          <Dialog>
            <DialogTrigger className="w-full -mt-1">
              <button className="flex cursor-pointer text-destructive w-full select-none items-center rounded-sm px-2 py-1.5 text-sm outline-none transition-colors hover:bg-accent">
                <Trash2 className="w-4 h-4 mr-2" />
                Delete Current List
              </button>
            </DialogTrigger>
            {lists.length === 1 ? (
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>You need at least one list</DialogTitle>
                  <DialogDescription>
                    You cannot delete your last remaining list. Please create
                    another list before deleting this one.
                  </DialogDescription>
                </DialogHeader>
              </DialogContent>
            ) : (
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Are you absolutely sure?</DialogTitle>
                  <DialogDescription>
                    This action cannot be undone. This will permanently delete
                    your list and remove its data from our servers.
                  </DialogDescription>
                </DialogHeader>
                <DialogClose>
                  <Button
                    variant="destructive"
                    onClick={() => void handleDeleteList()}
                  >
                    Delete this list
                  </Button>
                </DialogClose>
              </DialogContent>
            )}
          </Dialog>
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  );
}
/*
const handleDeleteList = async () => {
  if (lists.length === 1) {
    window.alert("You must have at least one list.");
    return;
  }
  setConfirmDialog(true);
  const confirmed = window.confirm(
    `Are you sure you want to delete "${selectedList.name}"? This cannot be undone.`
  );
  if (confirmed) {

  }
};*/
