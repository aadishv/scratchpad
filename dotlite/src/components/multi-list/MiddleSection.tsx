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

interface MiddleSectionProps {
  nodes: Node[];
}

export default function MiddleSection({ nodes }: MiddleSectionProps) {
  const total = nodes.length || 1;
  const redCount = nodes.filter(n => n.state === 'red').length;
  const yellowCount = nodes.filter(n => n.state === 'yellow').length;
  const greenCount = nodes.filter(n => n.state === 'green').length;
  const redPct = (redCount / total) * 100;
  const yellowPct = (yellowCount / total) * 100;
  const greenPct = (greenCount / total) * 100;

  return (
    <div className="w-full">
      <div className="flex h-10 w-full rounded-xl overflow-hidden bg-secondary">
        {redCount > 0 && (
          <div
            className="bg-destructive transition-all duration-75"
            style={{ width: `${redPct}%` }}
          />
        )}
        {yellowCount > 0 && (
          <div
            className="bg-yellow-500 transition-all duration-75"
            style={{ width: `${yellowPct}%` }}
          />
        )}
        {greenCount > 0 && (
          <div
            className="bg-green-500 transition-all duration-75"
            style={{ width: `${greenPct}%` }}
          />
        )}
      </div>
    </div>
  );
}
