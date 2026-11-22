import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import empty from '../../tests/fixtures/phase0-empty.json';
import { App } from './App';

describe('Phase 0 shell', () => {
  it('displays all planned pillars, an empty state, and the connected empty contract', async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: async () => empty });
    vi.stubGlobal('fetch', fetchMock);
    const { container } = render(<App />);
    expect(await screen.findByText('Local API connected · empty demo contract')).toBeVisible();
    expect(screen.getByRole('heading', { name: 'Synthetic demo only' })).toBeVisible();
    for (const name of ['Discover', 'Analyze', 'Classify', 'Visualize', 'Control']) {
      expect(screen.getByRole('heading', { name })).toBeVisible();
    }
    expect(screen.getByRole('heading', { name: 'No findings' })).toBeVisible();
    expect(container.querySelector('input[type="file"]')).toBeNull();
    expect(fetchMock.mock.calls[0][0]).toBe('/api/v1/demo');
  });

  it('offers safe startup guidance if the API is unavailable', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('Offline')));
    render(<App />);
    expect(await screen.findByText('Local API unavailable. Start it using the README.')).toBeVisible();
  });

  it('does not display unexpected populated records', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true, json: async () => ({ ...empty, observations: [{}] }),
    }));
    render(<App />);
    expect(await screen.findByText('Local API unavailable. Start it using the README.')).toBeVisible();
  });
});
