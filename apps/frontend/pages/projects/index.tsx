import Link from 'next/link';
import { useEffect, useState } from 'react';
import Layout from '../../components/Layout';
import { apiClient } from '../../lib/apiClient';
import { ProjectStatus, VideoProject } from '../../lib/types';

export default function ProjectList() {
  const [status, setStatus] = useState('');
  const [channel, setChannel] = useState('');
  const [rows, setRows] = useState<VideoProject[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const load = () => {
    setLoading(true);
    apiClient.listProjects({ status: status as ProjectStatus || undefined, channel: channel || undefined })
      .then(setRows).catch((e) => setError(e.message)).finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, [status, channel]);

  return <Layout title="Video Projects">
    <div className="row" style={{ marginBottom: 12 }}>
      <select value={status} onChange={(e) => setStatus(e.target.value)}><option value="">All statuses</option><option value="draft">Draft</option><option value="awaiting_review">Awaiting review</option><option value="approved">Approved</option><option value="rejected">Rejected</option></select>
      <input className="input" placeholder="Filter by channel" value={channel} onChange={(e) => setChannel(e.target.value)} style={{ maxWidth: 280 }} />
      <Link href="/projects/new" className="btn primary">New Project</Link>
    </div>
    {loading && <p>Loading projects...</p>}
    {error && <p className="error">{error}</p>}
    {!loading && !error && rows.length === 0 && <div className="card">No projects found.</div>}
    {!loading && !error && rows.length > 0 && <div className="card"><table><thead><tr><th>Title</th><th>Status</th><th>Channel</th><th>AI Cost</th></tr></thead><tbody>{rows.map((p) => <tr key={p.id}><td><Link href={`/projects/${p.id}`}>{p.title}</Link></td><td><span className="badge">{p.status}</span></td><td>{p.channel}</td><td>${p.aiCostUsd.toFixed(2)}</td></tr>)}</tbody></table></div>}
  </Layout>;
}
