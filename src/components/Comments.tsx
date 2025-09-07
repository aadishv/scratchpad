import { useAction } from "convex/react";
import { api } from "../../convex/_generated/api";
import { Id } from "../../convex/_generated/dataModel";
import { useEffect, useState } from "react";
import { Skeleton } from "./ui/skeleton";

interface Comment {
  id: number;
  created_at: string;
  author: string;
  text: string;
  children: Comment[];
}

const CommentView = ({ comment, depth }: { comment: Comment; depth: number }) => {
  const [isDelayed, setIsDelayed] = useState(true);

  useEffect(() => {
    const timer = setTimeout(() => {
      setIsDelayed(false);
    }, depth * 300); // 300ms lag per depth level
    return () => clearTimeout(timer);
  }, [depth]);

  if (isDelayed) {
    return <Skeleton className="h-12 w-full my-2" />;
  }

  return (
    <div className="my-2 p-2 border-l-2" style={{ marginLeft: `${depth * 20}px` }}>
      <div className="text-sm text-muted-foreground">
        {comment.author}
      </div>
      <div dangerouslySetInnerHTML={{ __html: comment.text }} />
      {comment.children && comment.children.map((child) => (
        <CommentView key={child.id} comment={child} depth={depth + 1} />
      ))}
    </div>
  );
};

export const Comments = ({ hnId }: { hnId: number }) => {
  const getComments = useAction(api.comments.getComments);
  const [comments, setComments] = useState<Comment[] | null>(null);

  useEffect(() => {
    const fetchComments = async () => {
      const result = await getComments({ hnId });
      setComments(result);
    };
    fetchComments();
  }, [getComments, hnId]);

  if (!comments) {
    return (
      <div>
        <Skeleton className="h-12 w-full my-2" />
        <Skeleton className="h-12 w-full my-2" />
        <Skeleton className="h-12 w-full my-2" />
      </div>
    );
  }

  return (
    <div>
      {comments.map((comment) => (
        <CommentView key={comment.id} comment={comment} depth={0} />
      ))}
    </div>
  );
};
