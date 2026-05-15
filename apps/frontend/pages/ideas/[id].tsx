import { useRouter } from 'next/router';
import { useEffect, useState } from 'react';
import Layout from '../../components/Layout';
import { apiClient } from '../../lib/apiClient';
import { ContentIdea } from '../../lib/types';

export default function IdeaDetailPage() {
  const { query } = useRouter();
  const [idea, setIdea] = useState<ContentIdea | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!query.id || Array.isArray(query.id)) return;
    apiClient.getIdea(query.id).then(setIdea).catch((e) => setError(e.message)).finally(() => setLoading(false));
  }, [query.id]);

  return <Layout title="Idea Detail">
    {loading && <p>Loading idea...</p>}
    {error && <p className="error">{error}</p>}
    {!loading && !error && !idea && <div className="card">Idea not found.</div>}
    {idea && <div className="card"><h3>{idea.title}</h3><p className="muted">{idea.contentPillar} • {idea.status}</p><p>{idea.summary || 'No summary provided.'}</p></div>}
  </Layout>;
}
