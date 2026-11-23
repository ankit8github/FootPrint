import { act, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { ImportLab } from './ImportLab';
import type { Batch } from './parsers';

function setup() {
  const worker = { postMessage: vi.fn(), terminate: vi.fn(),
    onmessage: null as ((event: { data: { batch: Batch } }) => void) | null,
    onerror: null as (() => void) | null };
  vi.stubGlobal('Worker', vi.fn(function () { return worker; }));
  const view = render(<ImportLab />);
  const input = screen.getByLabelText('Select synthetic .eml or Chrome JSON');
  expect(input).toBeDisabled();
  fireEvent.click(screen.getByRole('checkbox'));
  return { input, worker, unmount: view.unmount };
}
function select(input: HTMLElement) {
  fireEvent.change(input, { target: { files: [new File(['fictional'], 'SYNTHETIC_FILENAME_SECRET.eml')] } });
}
afterEach(() => vi.useRealTimers());
describe('transient import worker lifecycle', () => {
  it('unmounting terminates the current worker', () => {
    const { input, worker, unmount } = setup(); select(input);
    unmount();
    expect(worker.terminate).toHaveBeenCalledOnce();
  });
  it('requires consent, sends File objects only to the worker, and clears results', () => {
    const { input, worker } = setup();
    select(input);
    expect(worker.postMessage).toHaveBeenCalledOnce();
    act(() => worker.onmessage?.({ data: { batch: { schema_version: 'phase2-normalized-v1',
      synthetic_only: true, sources: [] } } }));
    expect(worker.terminate).toHaveBeenCalledOnce();
    expect(screen.getByRole('status')).toHaveTextContent('Nothing was uploaded or saved');
    expect(document.body.textContent).not.toContain('SYNTHETIC_FILENAME_SECRET');
    fireEvent.click(screen.getByText('Clear transient results'));
    expect(screen.getByText('No transient records.')).toBeVisible();
  });
  it('terminates a stalled worker at five seconds without displaying exception content', () => {
    vi.useFakeTimers();
    const { input, worker } = setup();
    select(input);
    act(() => { vi.advanceTimersByTime(5001); });
    expect(worker.terminate).toHaveBeenCalledOnce();
    expect(screen.getByRole('status')).toHaveTextContent('PARSER_TIMEOUT');
  });
  it('revoking consent terminates parsing and drops transient results', () => {
    const { input, worker } = setup(); select(input);
    fireEvent.click(screen.getByRole('checkbox'));
    expect(worker.terminate).toHaveBeenCalledOnce();
    expect(input).toBeDisabled();
    expect(screen.getByText('No transient records.')).toBeVisible();
  });
});
