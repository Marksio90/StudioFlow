import { FormEvent, useEffect, useState } from 'react';
import { ContentIdea } from '../../lib/types';

export default function IdeaDialog({
  mode,
  open,
  idea,
  onClose,
  onSubmit
}: {
  mode: 'create' | 'edit';
  open: boolean;
  idea?: ContentIdea | null;
  onClose: () => void;
  onSubmit: (payload: { title: string; summary: string; contentPillar: string }) => Promise<void>;
}) {
  const [title, setTitle] = useState('');
  const [summary, setSummary] = useState('');
  const [contentPillar, setContentPillar] = useState('');

  useEffect(() => {
    setTitle(idea?.title ?? '');
    setSummary(idea?.summary ?? '');
    setContentPillar(idea?.contentPillar ?? '');
  }, [idea, open]);

  if (!open) return null;

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    await onSubmit({ title, summary, contentPillar });
  };

  return <div className="card" style={{ marginBottom: 12 }}>
    <h3>{mode === 'create' ? 'Create Idea' : 'Edit Idea'}</h3>
    <form className="grid" onSubmit={submit}>
      <input className="input" value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Idea title" required />
      <input className="input" value={contentPillar} onChange={(e) => setContentPillar(e.target.value)} placeholder="Content pillar" required />
      <textarea rows={4} value={summary} onChange={(e) => setSummary(e.target.value)} placeholder="Summary" />
      <div className="row"><button className="btn primary" type="submit">Save</button><button className="btn" type="button" onClick={onClose}>Cancel</button></div>
    </form>
  </div>;
}
