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


  it('fails fast on backend 500 errors', async () => {
    vi.spyOn(global, 'fetch').mockResolvedValue(new Response(JSON.stringify({ detail: 'Internal Server Error' }), { status: 500, statusText: 'Internal Server Error' }));

    await expect(apiClient.getProject('p500')).rejects.toThrow(/HTTP 500/);
  });
});
