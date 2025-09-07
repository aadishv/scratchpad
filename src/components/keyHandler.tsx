import { useEffect, useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogTrigger,
} from "@/components/ui/dialog";
import { getApiKey } from "@/logic/getApiKey";
import { Button } from "./ui/button";
import { Key } from "lucide-react";
import { Input } from "./ui/input";

const useKeyHandler = () => {
  // API key dialog state
  const [apiKey, setApiKey] = useState<string | null>(null);
  const [showDialog, setShowDialog] = useState(false);
  const [editValue, setEditValue] = useState("");

  // Check for API key on mount
  useEffect(() => {
    const key = getApiKey();
    setApiKey(key);
    if (!key) setShowDialog(true);
  }, []);

  // Save API key to localStorage
  function saveApiKey(newKey: string) {
    window.localStorage.setItem("apiKey", newKey);
    setApiKey(newKey);
    setShowDialog(false);
  }

  // Open dialog from key icon
  function openDialog() {
    setEditValue(apiKey ?? "");
    setShowDialog(true);
  }
  return {
    dialog: (
      <Dialog open={showDialog} onOpenChange={setShowDialog}>
        <DialogTrigger asChild>
          <Button
            variant="ghost"
            className="ml-2 px-2 py-1 my-auto"
            aria-label="Edit API key"
            onClick={openDialog}
            type="button"
          >
            <Key />
          </Button>
        </DialogTrigger>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>API Key</DialogTitle>
          </DialogHeader>
          <div className="flex flex-col gap-2 mt-2">
            <Input
              type="password"
              placeholder="Enter your API key"
              value={editValue}
              onChange={(e) => setEditValue(e.target.value)}
              className="w-full"
              autoFocus
            />
            <span className="text-xs text-gray-500">
              Your API key is stored locally and never sent to our servers.
            </span>
          </div>
          <DialogFooter>
            <Button
              variant="fancy"
              onClick={() => {
                saveApiKey(editValue.trim());
              }}
              disabled={!editValue.trim()}
            >
              Save
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    ),
    prompt: (
      !apiKey && (
        <div className="flex flex-col items-center justify-center h-[30vh]">
          <div className="bg-white border border-gray-200 rounded-xl shadow-md p-6 flex flex-col gap-3 items-center">
            <Key className="w-8 h-8 mb-2 text-primary" />
            <div className="font-semibold text-lg">API Key Required</div>
            <div className="text-gray-600 text-sm mb-2 text-center">
              Please enter your API key to use the app.
            </div>
            <Button variant="fancy" onClick={openDialog}>
              Enter API Key
            </Button>
          </div>
        </div>
      )
    )
  } as const;
};

export default useKeyHandler;
