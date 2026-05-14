import { useRouter } from 'next/router';
import { useEffect, useState } from 'react';
import Layout from '../../components/Layout';
import { apiClient } from '../../lib/apiClient';
import { VideoProject } from '../../lib/types';

export default function ComplianceView() {
  const { query } = useRouter();
  const [project, setProject] = useState<VideoProject | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!query.id || Array.isArray(query.id)) return;
    apiClient.getProject(query.id).then(setProject).catch((e) => setError(e.message)).finally(() => setLoading(false));
  }, [query.id]);

  return <Layout title="Compliance Report">
    {loading && <p>Loading compliance report...</p>}
    {error && <p className="error">{error}</p>}
    {project && <div className="card"><h3>{project.title}</h3><p>Score: <strong>{project.compliance.score}</strong></p><p>Risk level: <span className="badge">{project.compliance.riskLevel}</span></p><h4>Blocking issues</h4>{project.compliance.blockingIssues.length ? <ul>{project.compliance.blockingIssues.map((x) => <li key={x}>{x}</li>)}</ul> : <p className="muted">No blocking issues.</p>}<h4>Recommendations</h4>{project.compliance.recommendations.length ? <ul>{project.compliance.recommendations.map((x) => <li key={x}>{x}</li>)}</ul> : <p className="muted">No recommendations.</p>}</div>}
  </Layout>;
}
