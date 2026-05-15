import { describe, it, expect, vi, beforeEach } from 'vitest';
import { apiClient } from './apiClient';

describe('apiClient contract', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('uses backend v1 video-projects endpoints with expected request/response shapes', async () => {
    const project = {
      id: 'p1', organization_id: 'o1', workspace_id: 'w1', channel_id: 'c1', title: 'Title', status: 'draft', created_at: '2026-01-01T00:00:00Z', updated_at: '2026-01-01T00:00:00Z'
    };
    const analytics = [{
      id: 'a1', video_project_id: 'p1', channel_id: 'c1', youtube_video_id: 'y1', views: 10, watch_time_minutes: 11, average_view_duration: 12, ctr: 1.2, likes: 2, comments: 3, subscribers_gained: 4, estimated_revenue: 5, snapshot_at: '2026-01-01T00:00:00Z'
    }];

    const fetchMock = vi.spyOn(global, 'fetch').mockImplementation(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.includes('/api/v1/video-projects?')) {
        return new Response(JSON.stringify({ items: [project], total: 1, limit: 50, offset: 0 }), { status: 200 });
      }
      if (url.endsWith('/api/v1/video-projects/p1')) {
        return new Response(JSON.stringify(project), { status: 200 });
      }
      if (url.endsWith('/api/v1/video-projects') && init?.method === 'POST') {
        const body = JSON.parse(String(init.body));
        expect(body).toMatchObject({ title: 'new title', organization_id: expect.any(String), workspace_id: expect.any(String), channel_id: expect.any(String) });
        expect(body.topic).toBeUndefined();
        return new Response(JSON.stringify(project), { status: 200 });
      }
      if (url.endsWith('/api/v1/video-projects/p1/approve')) {
        return new Response(JSON.stringify(project), { status: 200 });
      }
      if (url.endsWith('/api/v1/video-projects/p1/reject')) {
        return new Response(JSON.stringify(project), { status: 200 });
      }
      if (url.endsWith('/api/v1/video-projects/p1/analytics')) {
        return new Response(JSON.stringify(analytics), { status: 200 });
      }
      throw new Error(`Unhandled URL: ${url}`);
    });

    await apiClient.listProjects({ status: 'draft', channel: 'c1' });
    await apiClient.getProject('p1');
    await apiClient.createProject({ title: 'new title', topic: 't', description: 'd', channel: 'c', language: 'pl', targetAudience: 'ta' });
    await apiClient.setApproval('p1', true, 'ok');
    await apiClient.setApproval('p1', false, 'no');
    await apiClient.listAnalytics('p1');

    const calledUrls = fetchMock.mock.calls.map(([u]) => String(u));
    expect(calledUrls.some((u) => u.includes('/api/v1/video-projects'))).toBe(true);
    expect(calledUrls.every((u) => !u.includes('/projects'))).toBe(true);
  });


  

  it('maps channel endpoint payloads and memory payload contract correctly', async () => {
    const channel = { id: 'c1', organization_id: 'o1', workspace_id: 'w1', name: 'Main', youtube_channel_id: 'yt-1', created_at: '2026-01-01T00:00:00Z', updated_at: '2026-01-01T00:00:00Z' };
    const memory = { channel_id: 'c1', memory: { approved_title_patterns: ['A'], rejected_title_patterns: [], thumbnail_rules: { face: true }, banned_phrases: ['No hype'], preferred_phrases: [], compliance_preferences: {}, narrator_style: {}, visual_style: {}, audience_objections: [], best_performing_patterns: [], worst_performing_patterns: [], freeform_memory_notes: ['note'] } };

    vi.spyOn(global, 'fetch').mockImplementation(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.includes('/api/v1/channels') && !url.includes('/memory') && !url.endsWith('/c1') && (!init?.method || init.method === 'GET')) return new Response(JSON.stringify({ items: [channel], total: 1, limit: 20, offset: 0 }), { status: 200 });
      if (url.endsWith('/api/v1/channels/c1') && (!init?.method || init.method === 'GET')) return new Response(JSON.stringify(channel), { status: 200 });
      if (url.endsWith('/api/v1/channels') && init?.method === 'POST') {
        const body = JSON.parse(String(init.body));
        expect(body).toMatchObject({ name: 'Main', youtube_channel_id: 'yt-1', organization_id: expect.any(String), workspace_id: expect.any(String) });
        return new Response(JSON.stringify(channel), { status: 201 });
      }
      if (url.endsWith('/api/v1/channels/c1') && init?.method === 'PATCH') {
        const body = JSON.parse(String(init.body));
        expect(body).toEqual({ youtube_channel_id: 'yt-2' });
        return new Response(JSON.stringify({ ...channel, youtube_channel_id: 'yt-2' }), { status: 200 });
      }
      if (url.endsWith('/api/v1/channels/c1') && init?.method === 'DELETE') return new Response(JSON.stringify({}), { status: 200 });
      if (url.endsWith('/api/v1/channels/c1/memory') && (!init?.method || init.method === 'GET')) return new Response(JSON.stringify(memory), { status: 200 });
      if (url.endsWith('/api/v1/channels/c1/memory') && init?.method === 'PATCH') {
        const body = JSON.parse(String(init.body));
        expect(body.banned_phrases).toEqual(['No hype']);
        return new Response(JSON.stringify(memory), { status: 200 });
      }
      throw new Error(`Unhandled URL: ${url}`);
    });

    const listed = await apiClient.listChannels();
    const fetched = await apiClient.getChannel('c1');
    const created = await apiClient.createChannel({ name: 'Main', youtubeChannelId: 'yt-1' });
    const patched = await apiClient.updateChannel('c1', { youtubeChannelId: 'yt-2' });
    await apiClient.deleteChannel('c1');
    const channelMemory = await apiClient.getChannelMemory('c1');
    await apiClient.updateChannelMemory('c1', channelMemory);

    expect(listed[0].youtubeChannelId).toBe('yt-1');
    expect(fetched.id).toBe('c1');
    expect(created.name).toBe('Main');
    expect(patched.youtubeChannelId).toBe('yt-2');
    expect(channelMemory.bannedPhrases).toEqual(['No hype']);
  });


  it('covers ideas board smoke interactions via ideas API calls (list/create/edit/filter/status)', async () => {
    const idea = {
      id: 'i1', organization_id: 'o1', workspace_id: 'w1', channel_id: 'c1', title: 'Idea 1', summary: 'Summary 1', content_pillar: 'education', status: 'ideas', created_at: '2026-01-01T00:00:00Z', updated_at: '2026-01-01T00:00:00Z'
    };

    const fetchMock = vi.spyOn(global, 'fetch').mockImplementation(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.includes('/api/v1/content-ideas?')) {
        expect(url).toContain('status=ideas');
        expect(url).toContain('content_pillar=education');
        expect(url).toContain('q=hook');
        return new Response(JSON.stringify({ items: [idea] }), { status: 200 });
      }
      if (url.endsWith('/api/v1/content-ideas') && init?.method === 'POST') {
        const body = JSON.parse(String(init.body));
        expect(body).toMatchObject({ title: 'Created', content_pillar: 'education', organization_id: expect.any(String), workspace_id: expect.any(String), channel_id: expect.any(String) });
        return new Response(JSON.stringify({ ...idea, title: 'Created' }), { status: 200 });
      }
      if (url.endsWith('/api/v1/content-ideas/i1') && init?.method === 'PATCH') {
        const body = JSON.parse(String(init.body));
        expect(body).toEqual({ title: 'Edited', content_pillar: 'news', summary: 'Updated summary' });
        return new Response(JSON.stringify({ ...idea, title: 'Edited', content_pillar: 'news', summary: 'Updated summary' }), { status: 200 });
      }
      if (url.endsWith('/api/v1/content-ideas/i1/status') && init?.method === 'PATCH') {
        const body = JSON.parse(String(init.body));
        expect(body).toEqual({ status: 'ready' });
        return new Response(JSON.stringify({ ...idea, status: 'ready' }), { status: 200 });
      }
      throw new Error(`Unhandled URL: ${url}`);
    });

    const listed = await apiClient.listIdeas({ status: 'ideas', contentPillar: 'education', query: 'hook' });
    const created = await apiClient.createIdea({ title: 'Created', contentPillar: 'education', summary: 'New summary' });
    const edited = await apiClient.updateIdea('i1', { title: 'Edited', contentPillar: 'news', summary: 'Updated summary' });
    const moved = await apiClient.updateIdeaStatus('i1', 'ready');

    expect(listed[0].title).toBe('Idea 1');
    expect(created.title).toBe('Created');
    expect(edited.contentPillar).toBe('news');
    expect(moved.status).toBe('ready');
    expect(fetchMock).toHaveBeenCalledTimes(4);
  });

it('fails fast on backend 500 errors', async () => {
    vi.spyOn(global, 'fetch').mockResolvedValue(new Response(JSON.stringify({ detail: 'Internal Server Error' }), { status: 500, statusText: 'Internal Server Error' }));

    await expect(apiClient.getProject('p500')).rejects.toThrow(/HTTP 500/);
  });
});

it('maps angle API payloads including blocked approve and override reason submission path', async () => {
  const angleDto = {
    id: 'a1', content_idea_id: 'i1', channel_id: 'c1', video_project_id: 'p1',
    angle: { headline: 'H', hook: 'K', summary: 'S' }, status: 'proposed', approved: false,
    evaluation: { hook_clarity: 0.2, novelty: 0.7, audience_fit: 0.8, risk: 0.3, overall_score: 0.4, gate_passed: false, blocked_reasons: ['HOOK_TOO_WEAK'] },
    override: null, created_at: '2026-01-01T00:00:00Z', updated_at: '2026-01-01T00:00:00Z'
  };

  vi.spyOn(global, 'fetch').mockImplementation(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input);
    if (url.endsWith('/api/v1/ideas/i1/angles') && (!init?.method || init.method === 'GET')) {
      return new Response(JSON.stringify([angleDto]), { status: 200 });
    }
    if (url.endsWith('/api/v1/ideas/i1/angles/approve') && init?.method === 'POST') {
      return new Response(JSON.stringify({ detail: { code: 'ANGLE_APPROVAL_BLOCKED' } }), { status: 409 });
    }
    if (url.endsWith('/api/v1/ideas/i1/angles/override') && init?.method === 'POST') {
      const body = JSON.parse(String(init.body));
      expect(body.reason).toBe('Editorial exception');
      expect(body.angle_id).toBe('a1');
      return new Response(JSON.stringify({ ...angleDto, approved: true, status: 'approved_override', override: { reason: 'Editorial exception', overridden_by: body.overridden_by, metadata: {}, at: '2026-01-01T00:00:00Z', rejection_reasons: ['OVERALL_SCORE_TOO_LOW'] } }), { status: 200 });
    }
    throw new Error(`Unhandled URL: ${url}`);
  });

  const list = await apiClient.listIdeaAngles('i1');
  expect(list[0].evaluation?.gatePassed).toBe(false);

  await expect(apiClient.approveIdeaAngle('i1', 'a1')).rejects.toThrow(/HTTP 409/);

  const overridden = await apiClient.overrideIdeaAngle('i1', 'a1', 'Editorial exception');
  expect(overridden.override?.reason).toBe('Editorial exception');
});
