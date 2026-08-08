import { Inbox } from 'lucide-react';

export default function EmptyState({ title = 'No evaluations yet.', detail, action }) {
  return <div className="empty-state"><Inbox aria-hidden="true" /><h2>{title}</h2>{detail && <p>{detail}</p>}{action}</div>;
}
