import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';
import Layout from '../../components/Layout';
import IdeaDialog from '../../components/ideas/IdeaDialog';
import { apiClient } from '../../lib/apiClient';
import { ContentIdea, ContentIdeaStatus } from '../../lib/types';

const COLUMNS: Array<{ key: ContentIdeaStatus; label: string }> = [
  { key: 'ideas', label: 'Ideas' },
  { key: 'research', label: 'Research' },
  { key: 'angle_review', label: 'Angle Review' },
  { key: 'script_draft', label: 'Script Draft' },
  { key: 'compliance_review', label: 'Compliance Review' },
  { key: 'ready', label: 'Ready' },
  { key: 'published', label: 'Published' },
  { key: 'analyzed', label: 'Analyzed' }
];

export default function IdeasBoard() {
  const [ideas, setIdeas] = useState<ContentIdea[]>([]);
  const [status, setStatus] = useState('');
  const [contentPillar, setContentPillar] = useState('');
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [createOpen, setCreateOpen] = useState(false);
  const [editIdea, setEditIdea] = useState<ContentIdea | null>(null);

  const load = () => {
    setLoading(true);
    setError('');
    apiClient.listIdeas({ status: status as ContentIdeaStatus || undefined, contentPillar: contentPillar || undefined, query: query || undefined })
      .then(setIdeas).catch((e) => setError(e.message)).finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, [status, contentPillar, query]);

  const grouped = useMemo(() => COLUMNS.map((c) => ({ ...c, items: ideas.filter((i) => i.status === c.key) })), [ideas]);

  const move = async (idea: ContentIdea, next: ContentIdeaStatus) => {
    setIdeas((prev) => prev.map((p) => p.id === idea.id ? { ...p, status: next } : p));
    try {
      await apiClient.updateIdeaStatus(idea.id, next);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to update status');
      load();
    }
  };

  return <Layout title="Content Ideas">
    <IdeaDialog mode="create" open={createOpen} onClose={() => setCreateOpen(false)} onSubmit={async (payload) => { await apiClient.createIdea(payload); setCreateOpen(false); load(); }} />
    <IdeaDialog mode="edit" open={Boolean(editIdea)} idea={editIdea} onClose={() => setEditIdea(null)} onSubmit={async (payload) => { if (!editIdea) return; await apiClient.updateIdea(editIdea.id, payload); setEditIdea(null); load(); }} />
    <div className="row" style={{ marginBottom: 12 }}>
      <select value={status} onChange={(e) => setStatus(e.target.value)}><option value="">All statuses</option>{COLUMNS.map((c) => <option key={c.key} value={c.key}>{c.label}</option>)}</select>
      <input className="input" placeholder="Content pillar" value={contentPillar} onChange={(e) => setContentPillar(e.target.value)} style={{ maxWidth: 240 }} />
      <input className="input" placeholder="Search ideas" value={query} onChange={(e) => setQuery(e.target.value)} style={{ maxWidth: 240 }} />
      <button className="btn primary" onClick={() => setCreateOpen(true)}>Create Idea</button>
    </div>
    {loading && <p>Loading ideas...</p>}
    {error && <p className="error">{error}</p>}
    {!loading && !error && ideas.length === 0 && <div className="card">No ideas found.</div>}
    {!loading && !error && ideas.length > 0 && <div className="grid" style={{ gridTemplateColumns: 'repeat(4, minmax(220px, 1fr))' }}>
      {grouped.map((column) => <div key={column.key} className="card"><h4>{column.label}</h4>{column.items.length === 0 && <p className="muted">Empty</p>}{column.items.map((idea) => <div key={idea.id} className="card" style={{ marginBottom: 8 }} draggable onDragStart={(e) => e.dataTransfer.setData('idea', JSON.stringify(idea))}><Link href={`/ideas/${idea.id}`}>{idea.title}</Link><p className="muted">{idea.contentPillar}</p><div className="row"><button className="btn" onClick={() => setEditIdea(idea)}>Edit</button><select value={idea.status} onChange={(e) => move(idea, e.target.value as ContentIdeaStatus)}>{COLUMNS.map((c) => <option key={c.key} value={c.key}>{c.label}</option>)}</select></div></div>)}</div>)}
    </div>}
  </Layout>;
}
