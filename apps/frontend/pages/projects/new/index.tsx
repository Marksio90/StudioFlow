import { useState } from 'react';
import { useRouter } from 'next/router';
import Layout from '../../../components/Layout';
import { apiClient } from '../../../lib/apiClient';

const fields = ['title', 'topic', 'description', 'channel', 'language', 'targetAudience'] as const;

export default function NewProject() {
  const router = useRouter();
  const [form, setForm] = useState({ title: '', topic: '', description: '', channel: '', language: 'English', targetAudience: '' });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true); setError('');
    try {
      const created = await apiClient.createProject(form);
      router.push(`/projects/${created.id}`);
    } catch (err) { setError((err as Error).message); } finally { setSaving(false); }
  }

  return <Layout title="Create Video Project">
    <form className="card" onSubmit={submit} style={{ display: 'grid', gap: 12 }}>
      {fields.map((field) => <div key={field}><label>{field}</label><input className="input" required value={form[field]} onChange={(e) => setForm({ ...form, [field]: e.target.value })} /></div>)}
      {error && <p className="error">{error}</p>}
      <button className="btn primary" disabled={saving}>{saving ? 'Creating...' : 'Create project'}</button>
    </form>
  </Layout>;
}
