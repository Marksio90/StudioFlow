import Link from 'next/link';
import { useRouter } from 'next/router';
import { useEffect, useState } from 'react';
import Layout from '../../components/Layout';
import { apiClient } from '../../lib/apiClient';
import { VideoProject } from '../../lib/types';

export default function ProjectDetail() {
  const { query } = useRouter();
  const [project, setProject] = useState<VideoProject | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!query.id || Array.isArray(query.id)) return;
    apiClient.getProject(query.id).then(setProject).catch((e) => setError(e.message)).finally(() => setLoading(false));
  }, [query.id]);

  const handleApproval = async (approve: boolean) => {
    if (!project) return;
    const updated = await apiClient.setApproval(project.id, approve);
    setProject(updated);
  };

  return <Layout title="Video Project Detail">
    {loading && <p>Loading project...</p>}
    {error && <p className="error">{error}</p>}
    {project && <div className="grid" style={{ gridTemplateColumns: '1fr', gap: 12 }}>
      <div className="card"><h3>{project.title}</h3><p className="muted">Status: <span className="badge">{project.status}</span></p><p>{project.description}</p></div>
      <div className="card"><h4>Overview</h4><p>{project.overview}</p><h4>Research</h4><p>{project.research}</p><h4>Script</h4><p>{project.script}</p><h4>SEO</h4><p>{project.seo}</p></div>
      <div className="card"><h4>Compliance</h4><p>Score: {project.compliance.score} | Risk: {project.compliance.riskLevel}</p><Link href={`/compliance/${project.id}`}>Open compliance report</Link></div>
      <div className="card"><h4>Approval</h4><div className="row"><button className="btn primary" onClick={() => handleApproval(true)}>Approve</button><button className="btn" onClick={() => handleApproval(false)}>Reject</button></div></div>
      <div className="card"><h4>Workflow events</h4>{project.workflowEvents.map((e) => <p key={e.id}>{new Date(e.timestamp).toLocaleString()} - {e.actor}: {e.event}</p>)}</div>
      <div className="card"><h4>Costs</h4><p>AI cost: ${project.aiCostUsd.toFixed(2)}</p><p>YouTube quota used: {project.youtubeQuotaUsed}</p></div>
      <div className="card"><h4>Analytics</h4><p>Estimated CTR: {project.analytics.estimatedCtr}%</p><p>Projected views: {project.analytics.projectedViews}</p></div>
    </div>}
  </Layout>;
}
