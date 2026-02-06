import { useState, useRef, useEffect, useCallback } from "react";
import { useMutation } from "convex/react";
import { api } from "../../../convex/_generated/api";
import { Id } from "../../../convex/_generated/dataModel";
import { Textarea } from "../ui/textarea";
import { Button } from "../ui/button";
import { motion, AnimatePresence } from "framer-motion";
import { Trash2, Plus, Calendar } from "lucide-react";
import MiddleSection from "./MiddleSection";

type Node = {
  _id: Id<"nodes">;
  _creationTime: number;
  text: string;
  state: "red" | "yellow" | "green";
  listId: Id<"lists">;
  order: number;
  dueDate?: string | null;
};

interface BottomSectionProps {
  listId: Id<"lists">;
  nodes: Node[];
}

export default function BottomSection({ listId, nodes }: BottomSectionProps) {
  const createNode = useMutation(api.lists.createNode);
  const updateNodeText = useMutation(api.lists.updateNodeText);
  const updateNodeState = useMutation(api.lists.updateNodeState);
  const deleteNode = useMutation(api.lists.deleteNode);

  const textareaRefs = useRef<Map<Id<"nodes">, HTMLTextAreaElement>>(new Map());
  const [localTexts, setLocalTexts] = useState<Record<string, string>>({});
  const [lastCreatedNodeId, setLastCreatedNodeId] =
    useState<Id<"nodes"> | null>(null);
  const [localDueDates, setLocalDueDates] = useState<Record<string, string>>(
    {},
  );
  const [datePickerOpen, setDatePickerOpen] = useState<Record<string, boolean>>(
    {},
  );

  // Initialize local texts from nodes, preserving existing local changes
  useEffect(() => {
    setLocalTexts((prev) => {
      const newLocalTexts = { ...prev };
      nodes.forEach((node) => {
        if (!(node._id in newLocalTexts)) {
          newLocalTexts[node._id] = node.text;
        }
      });
      const nodeIds = new Set(nodes.map((n) => n._id));
      Object.keys(newLocalTexts).forEach((nodeId) => {
        if (!nodeIds.has(nodeId as Id<"nodes">)) {
          delete newLocalTexts[nodeId];
        }
      });
      return newLocalTexts;
    });

    setLocalDueDates((prev) => {
      const newLocalDueDates = { ...prev };
      nodes.forEach((node) => {
        if (!(node._id in newLocalDueDates)) {
          newLocalDueDates[node._id] = node.dueDate ?? "";
        }
      });
      const nodeIds = new Set(nodes.map((n) => n._id));
      Object.keys(newLocalDueDates).forEach((nodeId) => {
        if (!nodeIds.has(nodeId as Id<"nodes">)) {
          delete newLocalDueDates[nodeId];
        }
      });
      return newLocalDueDates;
    });
  }, [nodes]);

  // Add item
  const addItem = useCallback(async () => {
    try {
      const newNodeId = await createNode({
        listId,
        text: "",
        state: "red",
      });
      setLastCreatedNodeId(newNodeId);
    } catch (error) {
      console.error("Failed to create node:", error);
    }
  }, [listId, createNode]);

  // Cmd+Enter to add item
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
        // Don't create a new item if we're currently focused on a textarea
        const activeElement = document.activeElement;
        if (activeElement && activeElement.tagName === "TEXTAREA") {
          return;
        }
        e.preventDefault();
        void addItem();
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [addItem]);

  // Autosize textareas
  useEffect(() => {
    textareaRefs.current.forEach((textarea) => {
      if (textarea) {
        textarea.style.height = "auto";
        textarea.style.height = `${Math.max(32, textarea.scrollHeight)}px`;
      }
    });
  }, [nodes, localTexts]);

  const handleTextChange = (nodeId: Id<"nodes">, newText: string) => {
    setLocalTexts((prev) => ({
      ...prev,
      [nodeId]: newText,
    }));
  };

  const handleDueDateChange = (nodeId: Id<"nodes">, newDueDate: string) => {
    setLocalDueDates((prev) => ({
      ...prev,
      [nodeId]: newDueDate,
    }));
  };

  const handleTextBlur = async (
    node: Node,
    newText: string,
    dueDate?: string,
  ) => {
    const trimmed = newText.trim();
    const dueDateVal = dueDate === "" ? undefined : dueDate;
    if (trimmed !== node.text || dueDateVal !== node.dueDate) {
      try {
        await updateNodeText({
          nodeId: node._id,
          text: trimmed,
          dueDate: dueDateVal,
        });
      } catch (error) {
        console.error("Failed to update node text or due date:", error);
      }
    }
  };

  const handleStateChange = async (
    nodeId: Id<"nodes">,
    currentState: "red" | "yellow" | "green",
    pushForward: number,
  ) => {
    let nextState =
      currentState === "red"
        ? "yellow"
        : currentState === "yellow"
          ? "green"
          : "red";
    if (pushForward > 1) {
      nextState =
        nextState === "red"
          ? "yellow"
          : nextState === "yellow"
            ? "green"
            : "red";
    }
    try {
      await updateNodeState({
        nodeId,
        state: nextState as "red" | "yellow" | "green",
      });
    } catch (error) {
      console.error("Failed to update node state:", error);
    }
  };
  //
  const handleDeleteNode = async (nodeId: Id<"nodes">) => {
    try {
      await deleteNode({ nodeId });
    } catch (error) {
      console.error("Failed to delete node:", error);
    }
  };

  // Animation order
  const getOrder = (state: "red" | "yellow" | "green") =>
    state === "red" ? 0 : state === "yellow" ? 1 : 2;

  // Sort by color, then due date (closest first, null last), then alphabetical
  const sortedNodes = [...nodes].sort((a, b) => {
    const colorDiff = getOrder(a.state) - getOrder(b.state);
    if (colorDiff !== 0) return colorDiff;

    // Due date: null/undefined goes last
    if (a.dueDate && b.dueDate) {
      const dateDiff =
        new Date(a.dueDate).getTime() - new Date(b.dueDate).getTime();
      if (dateDiff !== 0) return dateDiff;
    } else if (a.dueDate && !b.dueDate) {
      return -1;
    } else if (!a.dueDate && b.dueDate) {
      return 1;
    }

    // Alphabetical by text
    return a.text.localeCompare(b.text);
  });

  return (
    <div className="space-y-3">
      <div className="flex gap-3">
        <MiddleSection nodes={nodes} />
        <Button
          variant="fancy"
          className="flex-col"
          onClick={() => void addItem()}
        >
          <Plus className="w-5 h-5 -mb-3" />
          <span className="text-xs">⌘+enter</span>
        </Button>
      </div>

      <motion.div layout className="space-y-2">
        <AnimatePresence>
          {sortedNodes.map((node) => {
            const localText = localTexts[node._id] ?? node.text;
            const colorClass =
              node.state === "red"
                ? "bg-red-500"
                : node.state === "yellow"
                  ? "bg-yellow-500"
                  : "bg-green-500";
            const localDueDate = localDueDates[node._id] ?? "";
            const isDatePickerOpen = datePickerOpen[node._id] ?? false;

            return (
              <motion.div
                key={node._id}
                layout
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                transition={{ duration: 0.1, ease: "easeOut" }}
                className="flex"
              >
                <div
                  onClick={() =>
                    void handleStateChange(node._id, node.state, 1)
                  }
                  onContextMenu={(e) => {
                    e.preventDefault();
                    void handleStateChange(node._id, node.state, 2);
                  }}
                  className={`!w-6 rounded-full transition-all duration-100 cursor-pointer  mb-1 hover:blur-xs ${colorClass}`}
                ></div>
                <div className="flex w-full">
                  <Textarea
                    value={localText}
                    onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) =>
                      handleTextChange(node._id, e.target.value)
                    }
                    className="my-auto pt-0.5 border-0 text-base bg-transparent placeholder:text-gray"
                    rows={1}
                    placeholder="Add a task..."
                    style={{
                      minHeight: "32px",
                      height: "32px",
                      resize: "none",
                      overflowY: "hidden",
                    }}
                    ref={(el: HTMLTextAreaElement | null) => {
                      if (el) {
                        textareaRefs.current.set(node._id, el);
                        if (lastCreatedNodeId === node._id) {
                          el.focus();
                          setLastCreatedNodeId(null);
                        }
                      } else {
                        textareaRefs.current.delete(node._id);
                      }
                    }}
                    onInput={(e: React.FormEvent<HTMLTextAreaElement>) => {
                      const textarea = e.currentTarget;
                      textarea.style.height = "auto";
                      textarea.style.height = `${Math.max(32, textarea.scrollHeight)}px`;
                    }}
                    onBlur={(e: React.FocusEvent<HTMLTextAreaElement>) => {
                      void handleTextBlur(
                        node,
                        e.currentTarget.value,
                        localDueDate,
                      );
                    }}
                    onKeyDown={(
                      e: React.KeyboardEvent<HTMLTextAreaElement>,
                    ) => {
                      const textarea = e.currentTarget;

                      // Handle cmd+enter to create new item from within textarea
                      if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
                        e.preventDefault();
                        void addItem();
                        return;
                      }

                      if (e.key === "Backspace" && textarea.value === "") {
                        e.preventDefault();
                        void handleDeleteNode(node._id);
                        return;
                      }

                      // Arrow key navigation
                      const currentIndex = sortedNodes.findIndex(
                        (n) => n._id === node._id,
                      );

                      if (
                        e.key === "ArrowUp" &&
                        textarea.selectionStart === 0 &&
                        textarea.selectionEnd === 0 &&
                        currentIndex > 0
                      ) {
                        e.preventDefault();
                        const prevNode = sortedNodes[currentIndex - 1];
                        textareaRefs.current.get(prevNode._id)?.focus();
                      }

                      if (
                        e.key === "ArrowDown" &&
                        textarea.selectionStart === textarea.value.length &&
                        textarea.selectionEnd === textarea.value.length &&
                        currentIndex < sortedNodes.length - 1
                      ) {
                        const value = textarea.value;
                        const beforeCaret = value.slice(
                          0,
                          textarea.selectionStart,
                        );
                        if (
                          beforeCaret.split("\n").length ===
                          value.split("\n").length
                        ) {
                          e.preventDefault();
                          const nextNode = sortedNodes[currentIndex + 1];
                          textareaRefs.current.get(nextNode._id)?.focus();
                        }
                      }
                    }}
                  />

                  {localDueDate ? (
                    <input
                      type="date"
                      className="ml-2 px-2 py-1 rounded border border-gray-300 bg-white text-sm"
                      value={localDueDate}
                      onChange={(e) => {
                        handleDueDateChange(node._id, e.target.value);
                        void handleTextBlur(node, localText, e.target.value);
                      }}
                      onBlur={(e) => {
                        void handleTextBlur(node, localText, e.target.value);
                      }}
                      placeholder="Due date"
                    />
                  ) : (
                    <button
                      className="ml-2 p-1 rounded hover:bg-gray-100"
                      type="button"
                      aria-label="Set due date"
                      onClick={() =>
                        setDatePickerOpen((prev) => ({
                          ...prev,
                          [node._id]: true,
                        }))
                      }
                    >
                      <Calendar className="w-4 h-4 text-primary" />
                    </button>
                  )}

                  {isDatePickerOpen && !localDueDate && (
                    <input
                      type="date"
                      className="ml-2 px-2 py-1 rounded border border-gray-300 bg-white text-sm"
                      value={localDueDate}
                      autoFocus
                      onChange={(e) => {
                        handleDueDateChange(node._id, e.target.value);
                        void handleTextBlur(node, localText, e.target.value);
                        setDatePickerOpen((prev) => ({
                          ...prev,
                          [node._id]: false,
                        }));
                      }}
                      onBlur={(_) => {
                        setDatePickerOpen((prev) => ({
                          ...prev,
                          [node._id]: false,
                        }));
                      }}
                      placeholder="Due date"
                    />
                  )}

                  <Button
                    size="icon"
                    variant="ghost"
                    className="w-6 h-6 my-auto opacity-70 hover:opacity-100 text-destructive hover:text-destructive"
                    onClick={() => void handleDeleteNode(node._id)}
                  >
                    <Trash2 className="w-3 h-3" />
                  </Button>
                </div>
              </motion.div>
            );
          })}
        </AnimatePresence>
      </motion.div>
    </div>
  );
}
