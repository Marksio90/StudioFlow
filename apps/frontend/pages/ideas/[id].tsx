import { useRouter } from 'next/router';
import { useEffect, useState } from 'react';
import Layout from '../../components/Layout';
import { apiClient } from '../../lib/apiClient';
import { ContentIdea, IdeaResearchReport } from '../../lib/types';

type TabKey = 'overview' | 'research';

const TABS: { key: TabKey; label: string }[] = [
  { key: 'overview', label: 'Overview' },
  { key: 'research', label: 'Research' }
];

const recommendationTone: Record<string, 'low' | 'medium' | 'high'> = {
  proceed: 'low',
  proceed_with_caution: 'medium',
  do_not_proceed: 'high',
  needs_more_research: 'medium'
};

export default function IdeaDetailPage() {
  const { query } = useRouter();
  const [tab, setTab] = useState<TabKey>('overview');
  const [idea, setIdea] = useState<ContentIdea | null>(null);
  const [research, setResearch] = useState<IdeaResearchReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [researchLoading, setResearchLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!query.id || Array.isArray(query.id)) return;

    const ideaId = query.id;
    setLoading(true);
    setError('');
    Promise.all([
      apiClient.getIdea(ideaId),
      apiClient.getLatestIdeaResearch(ideaId).catch(() => null)
    ])
      .then(([ideaValue, researchValue]) => {
        setIdea(ideaValue);
        setResearch(researchValue);
      })
      .catch((e) => setError(e instanceof Error ? e.message : 'Failed to load idea.'))
      .finally(() => setLoading(false));
  }, [query.id]);

  const runResearch = async () => {
    if (!idea) return;
    setResearchLoading(true);
    setError('');
    try {
      const report = await apiClient.analyzeIdeaResearch(idea.id);
      setResearch(report);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to run research.');
    } finally {
      setResearchLoading(false);
    }
  };

  const renderResearch = () => {
    if (!idea) return null;

    if (researchLoading) return <p>Analyzing research...</p>;

    if (!research) {
      return <div className="card">
        <p className="muted">No research report available yet.</p>
        <button className="btn primary" onClick={runResearch}>Run Research Analysis</button>
      </div>;
    }

    const recommendationClass = recommendationTone[research.recommendation] ?? 'medium';

    return <>
      <div className="card">
        <div className="row" style={{ justifyContent: 'space-between', alignItems: 'center' }}>
          <h4 style={{ margin: 0 }}>Latest Research Report</h4>
          <span className="badge" style={{
            backgroundColor: recommendationClass === 'high' ? '#7f1d1d' : recommendationClass === 'medium' ? '#78350f' : '#14532d',
            color: '#fff',
            textTransform: 'capitalize'
          }}>{research.recommendation.replace(/_/g, ' ')}</span>
        </div>
        <p className="muted">Generated {new Date(research.createdAt).toLocaleString()}</p>
        <div className="grid" style={{ gridTemplateColumns: 'repeat(3, minmax(180px, 1fr))' }}>
          <div className="card"><div className="muted">Demand score</div><h3>{research.scores.demandScore}</h3></div>
          <div className="card"><div className="muted">Competition score</div><h3>{research.scores.competitionScore}</h3></div>
          <div className="card"><div className="muted">Evidence score</div><h3>{research.scores.evidenceScore}</h3></div>
        </div>
        <h4>Missing Evidence</h4>
        {research.missingEvidence.length ? <ul>{research.missingEvidence.map((item) => <li key={item}>{item}</li>)}</ul> : <p className="muted">No major evidence gaps.</p>}
        <h4>Generic Risks</h4>
        {research.genericRisks.length ? <ul>{research.genericRisks.map((risk) => <li key={risk}>{risk}</li>)}</ul> : <p className="muted">No generic risks identified.</p>}
        <h4>Recommended Next Action</h4>
        <p>{research.recommendedNextAction || 'No next action provided.'}</p>
        <button className="btn" onClick={runResearch} disabled={researchLoading}>{researchLoading ? 'Analyzing...' : 'Re-run Analysis'}</button>
      </div>
    </>;
  };

  return <Layout title="Idea Detail">
    {loading && <p>Loading idea...</p>}
    {error && <p className="error">{error}</p>}
    {!loading && !error && !idea && <div className="card">Idea not found.</div>}
    {idea && <div className="card">
      <div className="row" style={{ marginBottom: 12 }}>{TABS.map((item) => <button className={`btn ${tab === item.key ? 'primary' : ''}`} key={item.key} onClick={() => setTab(item.key)}>{item.label}</button>)}</div>
      {tab === 'overview' && <><h3>{idea.title}</h3><p className="muted">{idea.contentPillar} • {idea.status}</p><p>{idea.summary || 'No summary provided.'}</p></>}
      {tab === 'research' && renderResearch()}
    </div>}
  </Layout>;
}
