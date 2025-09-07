import { useQuery, useMutation } from "convex/react";
import { api } from "../convex/_generated/api";
import { useEffect, useState, useRef } from "react";
import { Button } from "./components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "./components/ui/dialog";
import { Textarea } from "./components/ui/textarea";
import { Input } from "./components/ui/input";
import { Comments } from "./components/Comments";
import { Settings } from "./components/Settings";
import { SettingsIcon } from "lucide-react";

export default function App() {
  const posts = useQuery(api.hackerNews.getPosts);
  const userSettings = useQuery(api.users.getUserSettings);
  const triggerExtractContent = useMutation(api.hackerNews.triggerExtractContent);
  const saveThought = useMutation(api.thoughts.saveThought);

  const [currentPostIndex, setCurrentPostIndex] = useState(0);
  const [scrollPercentage, setScrollPercentage] = useState(0);
  const [isThoughtDialogOpen, setIsThoughtDialogOpen] = useState(false);
  const [isCommentsOpen, setIsCommentsOpen] = useState(false);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [thought, setThought] = useState("");
  const contentRef = useRef<HTMLDivElement>(null);

  const currentPost = posts?.[currentPostIndex];

  useEffect(() => {
    if (userSettings) {
      document.documentElement.classList.toggle("dark", userSettings.theme === "dark");
      const style = document.createElement("style");
      style.innerHTML = `
        :root {
          --font-header: "${userSettings.headerFont ?? "PP Editorial"}";
          --font-body: "${userSettings.bodyFont ?? "Geist"}";
        }
      `;
      document.head.appendChild(style);
      return () => {
        document.head.removeChild(style);
      };
    }
  }, [userSettings]);

  useEffect(() => {
    if (currentPost && !currentPost.content) {
      triggerExtractContent({ postId: currentPost._id, url: currentPost.url });
    }
  }, [currentPost, triggerExtractContent]);

  useEffect(() => {
    const handleScroll = () => {
      const contentElement = contentRef.current;
      if (contentElement) {
        const { scrollTop, scrollHeight, clientHeight } = contentElement;
        const percentage = (scrollTop / (scrollHeight - clientHeight)) * 100;
        setScrollPercentage(percentage);
      }
    };

    const contentElement = contentRef.current;
    contentElement?.addEventListener("scroll", handleScroll);
    return () => {
      contentElement?.removeEventListener("scroll", handleScroll);
    };
  }, []);

  const handleNextPost = () => {
    setIsThoughtDialogOpen(true);
  };

  const handleSaveThought = async () => {
    if (currentPost) {
      await saveThought({ postId: currentPost._id, text: thought });
      setThought("");
      setIsThoughtDialogOpen(false);
      if (posts && currentPostIndex < posts.length - 1) {
        setCurrentPostIndex(currentPostIndex + 1);
        setScrollPercentage(0);
      }
    }
  };

  if (!posts) {
    return <div>Loading posts...</div>;
  }

  if (!currentPost) {
    return <div>No more posts!</div>;
  }

  return (
    <div className="flex flex-col h-screen font-body">
      <header className="fixed top-0 left-0 right-0 h-16 bg-background border-b flex items-center justify-between px-4 z-10 font-header">
        <div className="w-1/3">
          <div className="w-full bg-gray-200 rounded-full h-2.5">
            <div
              className="bg-primary h-2.5 rounded-full"
              style={{ width: `${scrollPercentage}%` }}
            ></div>
          </div>
        </div>
        <div className="w-1/3 text-center truncate">
          <h1 className="text-lg font-semibold">{currentPost.title}</h1>
        </div>
        <div className="w-1/3 flex justify-end gap-2">
          <Button variant="outline" onClick={() => setIsCommentsOpen(true)}>View Comments</Button>
          <Button onClick={handleNextPost}>Next Post</Button>
          <Button variant="ghost" size="icon" onClick={() => setIsSettingsOpen(true)}>
            <SettingsIcon className="h-4 w-4" />
          </Button>
        </div>
      </header>
      <main className="pt-16 flex-grow overflow-y-auto" ref={contentRef}>
        {currentPost.content ? (
          <div
            className="prose lg:prose-xl mx-auto p-8"
            dangerouslySetInnerHTML={{ __html: currentPost.content }}
          />
        ) : (
          <div className="flex justify-center items-center h-full">
            <div>Loading content...</div>
          </div>
        )}
      </main>
      <Dialog open={isThoughtDialogOpen} onOpenChange={setIsThoughtDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>What are your thoughts on this post?</DialogTitle>
            <DialogDescription>
              Write a private note to move on to the next post.
            </DialogDescription>
          </DialogHeader>
          <Textarea
            value={thought}
            onChange={(e) => setThought(e.target.value)}
            placeholder="Your thoughts..."
          />
          <DialogFooter>
            <Button onClick={handleSaveThought}>Save and Continue</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      <Dialog open={isCommentsOpen} onOpenChange={setIsCommentsOpen}>
        <DialogContent className="max-w-4xl h-4/5 overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Comments</DialogTitle>
          </DialogHeader>
          {currentPost && <Comments hnId={currentPost.hnId} />}
        </DialogContent>
      </Dialog>
      <Dialog open={isSettingsOpen} onOpenChange={setIsSettingsOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Settings</DialogTitle>
          </DialogHeader>
          <Settings />
        </DialogContent>
      </Dialog>
    </div>
  );
}
