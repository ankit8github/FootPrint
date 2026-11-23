import { act, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { EvidenceLab } from './EvidenceLab';
import { linkEvidence } from './discovery';
import type { DiscoveryGraph } from './types';

type Reply = { data: { graph?: DiscoveryGraph; code?: string } };
function setup() {
  const worker = { postMessage: vi.fn(), terminate: vi.fn(), onmessage: null as ((e: Reply) => void) | null,
    onerror: null as (() => void) | null };
  vi.stubGlobal('Worker', vi.fn(function () { return worker; }));
  const view = render(<EvidenceLab />);
  const input = screen.getByLabelText('Select synthetic evidence files');
  expect(input).toBeDisabled(); fireEvent.click(screen.getByRole('checkbox'));
  const select = () => fireEvent.change(input, { target: { files: [new File(['SYNTHETIC_BODY_SECRET'], 'SYNTHETIC_FILENAME_SECRET.eml')] } });
  return { worker, input, select, unmount: view.unmount };
}
afterEach(() => vi.useRealTimers());
describe('transient discovery inspector lifecycle', () => {
  it('requires consent, posts files only to the worker and terminates on completion', () => {
    const { worker, select } = setup(); select();
    expect(worker.postMessage).toHaveBeenCalledOnce();
    act(() => worker.onmessage?.({ data: { graph: linkEvidence([], [], []) } }));
    expect(worker.terminate).toHaveBeenCalledOnce();
    expect(screen.getByRole('status')).toHaveTextContent('Nothing was uploaded or saved');
    expect(screen.getByLabelText('Minimized evidence graph')).toBeVisible();
    expect(document.body.textContent).not.toMatch(/SYNTHETIC_BODY_SECRET|SYNTHETIC_FILENAME_SECRET/);
    fireEvent.click(screen.getByText('Clear transient evidence'));
    expect(screen.getByText('No transient evidence.')).toBeVisible();
  });
  it('terminates on timeout and ignores late replies', () => {
    vi.useFakeTimers(); const { worker, select } = setup(); select();
    act(() => { vi.advanceTimersByTime(5001); });
    act(() => worker.onmessage?.({ data: { graph: linkEvidence([], [], []) } }));
    expect(worker.terminate).toHaveBeenCalledOnce();
    expect(screen.getByRole('status')).toHaveTextContent('PARSER_TIMEOUT');
    expect(screen.getByText('No transient evidence.')).toBeVisible();
  });
  it('drops transient state and terminates when consent is revoked or the page unmounts', () => {
    const { worker, select, input, unmount } = setup(); select();
    fireEvent.click(screen.getByRole('checkbox'));
    expect(input).toBeDisabled(); expect(worker.terminate).toHaveBeenCalledOnce();
    fireEvent.click(screen.getByRole('checkbox')); select(); unmount();
    expect(worker.terminate).toHaveBeenCalledTimes(2);
  });
  it('shows only allowlisted failure codes and never exception content', () => {
    const { worker, select } = setup(); select();
    act(() => worker.onmessage?.({ data: { code: 'SYNTHETIC_ERROR_SECRET' } }));
    expect(screen.getByRole('status')).toHaveTextContent('PARSER_FAILED');
    expect(document.body.textContent).not.toContain('SYNTHETIC_ERROR_SECRET');
  });
});
