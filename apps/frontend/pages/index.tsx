import { useEffect, useState } from 'react';
import Layout from '../components/Layout';
import { apiClient } from '../lib/apiClient';
import { VideoProject } from '../lib/types';

export default function Dashboard() {
  const [data, setData] = useState<VideoProject[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    apiClient.listProjects().then(setData).catch((e) => setError(e.message)).finally(() => setLoading(false));
  }, []);

  const awaiting = data.filter((p) => p.status === 'awaiting_review').length;
  const aiCost = data.reduce((a, p) => a + p.aiCostUsd, 0).toFixed(2);
  const quota = data.reduce((a, p) => a + p.youtubeQuotaUsed, 0);

  return <Layout title="AI Media Operations OS - Dashboard">
    {loading && <p>Loading dashboard...</p>}
    {error && <p className="error">{error}</p>}
    {!loading && !error && <div className="grid grid-5">
      <div className="card"><div className="muted">Projects</div><h2>{data.length}</h2></div>
      <div className="card"><div className="muted">Awaiting review</div><h2>{awaiting}</h2></div>
      <div className="card"><div className="muted">AI costs</div><h2>${aiCost}</h2></div>
      <div className="card"><div className="muted">YouTube quota</div><h2>{quota}</h2></div>
      <div className="card"><div className="muted">Statuses</div><h2>{new Set(data.map((p) => p.status)).size}</h2></div>
    </div>}
  </Layout>;
}
