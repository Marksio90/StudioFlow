import { useRouter } from 'next/router';
import { useEffect, useMemo, useState } from 'react';
import Layout from '../../components/Layout';
import { apiClient } from '../../lib/apiClient';
import { Channel, ChannelMemoryInput } from '../../lib/types';

type TabKey = 'overview' | 'audience' | 'tone' | 'pillars' | 'title' | 'thumbnail' | 'compliance' | 'memory';

const TABS: { key: TabKey; label: string }[] = [
  { key: 'overview', label: 'Overview' }, { key: 'audience', label: 'Audience' }, { key: 'tone', label: 'Tone of Voice' }, { key: 'pillars', label: 'Content Pillars' },
  { key: 'title', label: 'Title Rules' }, { key: 'thumbnail', label: 'Thumbnail Rules' }, { key: 'compliance', label: 'Compliance Rules' }, { key: 'memory', label: 'Memory Notes' }
];

const defaults: ChannelMemoryInput = {
  approvedTitlePatterns: [], rejectedTitlePatterns: [], thumbnailRules: {}, bannedPhrases: [], preferredPhrases: [], compliancePreferences: {}, narratorStyle: {}, visualStyle: {}, audienceObjections: [], bestPerformingPatterns: [], worstPerformingPatterns: [], freeformMemoryNotes: []
};

const parseLines = (value: string) => value.split('\n').map((line) => line.trim()).filter(Boolean);
const formatLines = (rows: string[]) => rows.join('\n');

export default function ChannelProfilePage() {
  const { query } = useRouter();
  const channelId = useMemo(() => (query.id && !Array.isArray(query.id) ? query.id : ''), [query.id]);
  const [channel, setChannel] = useState<Channel | null>(null);
  const [form, setForm] = useState<ChannelMemoryInput>(defaults);
  const [tab, setTab] = useState<TabKey>('overview');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [validationError, setValidationError] = useState('');

  useEffect(() => {
    if (!channelId) return;
    setLoading(true); setError('');
    Promise.all([apiClient.getChannel(channelId), apiClient.getChannelMemory(channelId)])
      .then(([loadedChannel, loadedMemory]) => { setChannel(loadedChannel); const { channelId: _channelId, ...memoryInput } = loadedMemory; setForm(memoryInput); })
      .catch((e) => setError(e.message)).finally(() => setLoading(false));
  }, [channelId]);

  const setField = <K extends keyof ChannelMemoryInput>(field: K, value: ChannelMemoryInput[K]) => setForm((curr) => ({ ...curr, [field]: value }));

  const onSave = async () => {
    setValidationError(''); setSuccess(''); setError('');
    if (!form.approvedTitlePatterns.length && !form.rejectedTitlePatterns.length && !form.freeformMemoryNotes.length) {
      setValidationError('Please provide at least one title pattern or memory note before saving.');
      return;
    }
    setSaving(true);
    try { await apiClient.updateChannelMemory(channelId, form); setSuccess('Saved channel memory successfully.'); }
    catch (e) { setError(e instanceof Error ? e.message : 'Failed to save changes.'); }
    finally { setSaving(false); }
  };

  if (loading) return <Layout title="Channel Profile"><p>Loading channel profile...</p></Layout>;
  if (error && !channel) return <Layout title="Channel Profile"><p className="error">{error}</p></Layout>;
  if (!channel) return <Layout title="Channel Profile"><p className="muted">Channel not found.</p></Layout>;

  return <Layout title={`Channel: ${channel.name}`}>
    <div className="card"><p className="muted">YouTube ID: {channel.youtubeChannelId}</p>
      <div className="row" style={{ marginBottom: 12 }}>{TABS.map((item) => <button className={`btn ${tab === item.key ? 'primary' : ''}`} key={item.key} onClick={() => setTab(item.key)}>{item.label}</button>)}</div>

      {tab === 'overview' && <><label>Name</label><input className="input" value={channel.name} disabled /><label style={{ marginTop: 8, display: 'block' }}>Best Performing Patterns</label><textarea className="input" rows={5} value={formatLines(form.bestPerformingPatterns)} onChange={(e) => setField('bestPerformingPatterns', parseLines(e.target.value))} /></>}
      {tab === 'audience' && <><label>Audience Objections</label><textarea className="input" rows={8} value={formatLines(form.audienceObjections)} onChange={(e) => setField('audienceObjections', parseLines(e.target.value))} /></>}
      {tab === 'tone' && <><label>Narrator Style (JSON)</label><textarea className="input" rows={8} value={JSON.stringify(form.narratorStyle, null, 2)} onChange={(e) => { try { setField('narratorStyle', JSON.parse(e.target.value)); setValidationError(''); } catch { setValidationError('Narrator style must be valid JSON.'); } }} /></>}
      {tab === 'pillars' && <><label>Visual Style (JSON)</label><textarea className="input" rows={8} value={JSON.stringify(form.visualStyle, null, 2)} onChange={(e) => { try { setField('visualStyle', JSON.parse(e.target.value)); setValidationError(''); } catch { setValidationError('Visual style must be valid JSON.'); } }} /></>}
      {tab === 'title' && <><label>Approved Title Patterns</label><textarea className="input" rows={6} value={formatLines(form.approvedTitlePatterns)} onChange={(e) => setField('approvedTitlePatterns', parseLines(e.target.value))} /><label>Rejected Title Patterns</label><textarea className="input" rows={6} value={formatLines(form.rejectedTitlePatterns)} onChange={(e) => setField('rejectedTitlePatterns', parseLines(e.target.value))} /></>}
      {tab === 'thumbnail' && <><label>Thumbnail Rules (JSON)</label><textarea className="input" rows={10} value={JSON.stringify(form.thumbnailRules, null, 2)} onChange={(e) => { try { setField('thumbnailRules', JSON.parse(e.target.value)); setValidationError(''); } catch { setValidationError('Thumbnail rules must be valid JSON.'); } }} /></>}
      {tab === 'compliance' && <><label>Banned Phrases</label><textarea className="input" rows={5} value={formatLines(form.bannedPhrases)} onChange={(e) => setField('bannedPhrases', parseLines(e.target.value))} /><label>Preferred Phrases</label><textarea className="input" rows={5} value={formatLines(form.preferredPhrases)} onChange={(e) => setField('preferredPhrases', parseLines(e.target.value))} /><label>Compliance Preferences (JSON)</label><textarea className="input" rows={8} value={JSON.stringify(form.compliancePreferences, null, 2)} onChange={(e) => { try { setField('compliancePreferences', JSON.parse(e.target.value)); setValidationError(''); } catch { setValidationError('Compliance preferences must be valid JSON.'); } }} /></>}
      {tab === 'memory' && <><label>Memory Notes</label><textarea className="input" rows={8} value={formatLines(form.freeformMemoryNotes)} onChange={(e) => setField('freeformMemoryNotes', parseLines(e.target.value))} /><label>Worst Performing Patterns</label><textarea className="input" rows={5} value={formatLines(form.worstPerformingPatterns)} onChange={(e) => setField('worstPerformingPatterns', parseLines(e.target.value))} /></>}
      {validationError && <p className="error">{validationError}</p>}
      {success && <p style={{ color: '#166534' }}>{success}</p>}
      {error && channel && <p className="error">{error}</p>}
      <div className="row" style={{ marginTop: 12 }}><button className="btn primary" onClick={onSave} disabled={saving}>{saving ? 'Saving...' : 'Save Channel Memory'}</button></div>
    </div>
  </Layout>;
}
