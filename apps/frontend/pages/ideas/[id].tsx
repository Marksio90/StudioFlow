import { useRouter } from 'next/router';
import { useEffect, useState } from 'react';
import Layout from '../../components/Layout';
import { apiClient } from '../../lib/apiClient';
import { ContentIdea, IdeaAngle, IdeaResearchReport } from '../../lib/types';

type TabKey = 'overview' | 'research' | 'angle';

const TABS: { key: TabKey; label: string }[] = [
  { key: 'overview', label: 'Overview' },
  { key: 'research', label: 'Research' },
  { key: 'angle', label: 'Angle' }
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
  const [anglesLoading, setAnglesLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState<string>('');
  const [researchLoading, setResearchLoading] = useState(false);
  const [error, setError] = useState('');
  const [angles, setAngles] = useState<IdeaAngle[]>([]);
  const [overrideTarget, setOverrideTarget] = useState<IdeaAngle | null>(null);
  const [overrideReason, setOverrideReason] = useState('');

  useEffect(() => {
    if (!query.id || Array.isArray(query.id)) return;

    const ideaId = query.id;
    setLoading(true);
    setError('');
    Promise.all([
      apiClient.getIdea(ideaId),
      apiClient.getLatestIdeaResearch(ideaId).catch(() => null),
      apiClient.listIdeaAngles(ideaId).catch(() => [])
    ])
      .then(([ideaValue, researchValue, angleValues]) => {
        setIdea(ideaValue);
        setResearch(researchValue);
        setAngles(angleValues);
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
  const refreshAngles = async () => {
    if (!idea) return;
    setAnglesLoading(true);
    try { setAngles(await apiClient.listIdeaAngles(idea.id)); } finally { setAnglesLoading(false); }
  };
  const generateVariants = async () => {
    if (!idea) return;
    setActionLoading('generate');
    setError('');
    try {
      const generated = await apiClient.generateIdeaAngles(idea.id, 3, idea.summary || idea.title);
      setAngles((prev) => [...prev, ...generated]);
    } catch (e) { setError(e instanceof Error ? e.message : 'Failed to generate variants.'); } finally { setActionLoading(''); }
  };
  const evaluateAngle = async (angleId: string) => {
    if (!idea) return;
    setActionLoading(`eval-${angleId}`);
    try { const updated = await apiClient.evaluateIdeaAngle(idea.id, angleId); setAngles((prev) => prev.map((a) => a.id === updated.id ? updated : a)); } finally { setActionLoading(''); }
  };
  const approveAngle = async (angleId: string) => {
    if (!idea) return;
    setActionLoading(`approve-${angleId}`);
    setError('');
    try { const updated = await apiClient.approveIdeaAngle(idea.id, angleId); setAngles((prev) => prev.map((a) => a.id === updated.id ? updated : a)); } catch (e) { setError(e instanceof Error ? e.message : 'Approval failed.'); } finally { setActionLoading(''); }
  };
  const submitOverride = async () => {
    if (!idea || !overrideTarget || !overrideReason.trim()) return;
    setActionLoading(`override-${overrideTarget.id}`);
    try {
      const updated = await apiClient.overrideIdeaAngle(idea.id, overrideTarget.id, overrideReason.trim());
      setAngles((prev) => prev.map((a) => a.id === updated.id ? updated : a));
      setOverrideTarget(null);
      setOverrideReason('');
    } catch (e) { setError(e instanceof Error ? e.message : 'Override failed.'); } finally { setActionLoading(''); }
  };

  const renderAngles = () => {
    if (!idea) return null;
    if (anglesLoading) return <p>Loading angle variants...</p>;
    return <div className="card">
      <div className="row" style={{ justifyContent: 'space-between', marginBottom: 12 }}>
        <h4 style={{ margin: 0 }}>Angle Variants</h4>
        <div className="row">
          <button className="btn" onClick={refreshAngles}>Refresh</button>
          <button className="btn primary" onClick={generateVariants} disabled={actionLoading === 'generate'}>{actionLoading === 'generate' ? 'Generating...' : 'Generate Variants'}</button>
        </div>
      </div>
      {!angles.length && <p className="muted">No angle variants yet. Generate variants to get started.</p>}
      {!!angles.length && <div className="grid" style={{ gap: 12 }}>
        {angles.map((entry) => {
          const angle = entry.angle || {};
          const evaln = entry.evaluation;
          const gatePassed = Boolean(evaln?.gatePassed);
          return <div key={entry.id} className="card">
            <h4>{String(angle.headline || 'Untitled angle')}</h4>
            <p><strong>Hook:</strong> {String(angle.hook || '—')}</p>
            <p><strong>Summary:</strong> {String(angle.summary || '—')}</p>
            <p><strong>Differentiator:</strong> {String(angle.differentiator || '—')}</p>
            <p><strong>Human judgment required:</strong> {String(angle.human_judgment_required || '—')}</p>
            {!evaln && <p className="muted">No scorecard yet. Evaluate to run deterministic gate.</p>}
            {evaln && <>
              <div className="grid" style={{ gridTemplateColumns: 'repeat(5, minmax(120px, 1fr))' }}>
                <div className="card"><div className="muted">Hook</div><h4>{evaln.hookClarity.toFixed(2)}</h4></div>
                <div className="card"><div className="muted">Novelty</div><h4>{evaln.novelty.toFixed(2)}</h4></div>
                <div className="card"><div className="muted">Audience fit</div><h4>{evaln.audienceFit.toFixed(2)}</h4></div>
                <div className="card"><div className="muted">Risk</div><h4>{evaln.risk.toFixed(2)}</h4></div>
                <div className="card"><div className="muted">Overall</div><h4>{evaln.overallScore.toFixed(2)}</h4></div>
              </div>
              {!gatePassed && <><p className="error">Generic-content warning: deterministic gate failed.</p><h5>Failed-gate reasons</h5><ul>{evaln.blockedReasons.map((reason) => <li key={reason}>{reason}</li>)}</ul></>}
            </>}
            {entry.override && <p className="muted">Overridden: {entry.override.reason}</p>}
            <div className="row">
              <button className="btn" onClick={() => evaluateAngle(entry.id)} disabled={actionLoading === `eval-${entry.id}`}>{actionLoading === `eval-${entry.id}` ? 'Evaluating...' : 'Evaluate'}</button>
              <button className="btn primary" onClick={() => approveAngle(entry.id)} disabled={!gatePassed || actionLoading === `approve-${entry.id}`}>{actionLoading === `approve-${entry.id}` ? 'Approving...' : 'Approve'}</button>
              {!gatePassed && <button className="btn" onClick={() => setOverrideTarget(entry)}>Override</button>}
            </div>
          </div>;
        })}
      </div>}
      {overrideTarget && <div className="card" style={{ marginTop: 12 }}>
        <h4>Override Approval Gate</h4>
        <p className="muted">Provide required reason for manual override.</p>
        <textarea value={overrideReason} onChange={(e) => setOverrideReason(e.target.value)} rows={4} style={{ width: '100%' }} placeholder="Explain why this angle should be approved despite gate failure." />
        <div className="row" style={{ marginTop: 8 }}>
          <button className="btn" onClick={() => { setOverrideTarget(null); setOverrideReason(''); }}>Cancel</button>
          <button className="btn primary" disabled={!overrideReason.trim() || actionLoading === `override-${overrideTarget.id}`} onClick={submitOverride}>Submit Override</button>
        </div>
      </div>}
    </div>;
  };

  return <Layout title="Idea Detail">
    {loading && <p>Loading idea...</p>}
    {error && <p className="error">{error}</p>}
    {!loading && !error && !idea && <div className="card">Idea not found.</div>}
    {idea && <div className="card">
      <div className="row" style={{ marginBottom: 12 }}>{TABS.map((item) => <button className={`btn ${tab === item.key ? 'primary' : ''}`} key={item.key} onClick={() => setTab(item.key)}>{item.label}</button>)}</div>
      {tab === 'overview' && <><h3>{idea.title}</h3><p className="muted">{idea.contentPillar} • {idea.status}</p><p>{idea.summary || 'No summary provided.'}</p></>}
      {tab === 'research' && renderResearch()}
      {tab === 'angle' && renderAngles()}
    </div>}
  </Layout>;
}
