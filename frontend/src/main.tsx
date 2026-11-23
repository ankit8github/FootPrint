import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { App } from './App';
import { ImportLab } from './features/imports/ImportLab';
import { EvidenceLab } from './features/discovery/EvidenceLab';
import './style.css';

const view = window.location.pathname === '/phase3' ? <EvidenceLab /> : window.location.pathname === '/phase2' ? <ImportLab /> : <App />;
createRoot(document.getElementById('root')!).render(<StrictMode>{view}</StrictMode>);
