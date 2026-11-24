import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { App } from './App';
import { ImportLab } from './features/imports/ImportLab';
import { EvidenceLab } from './features/discovery/EvidenceLab';
import { AssessmentLab } from './features/assessments/AssessmentLab';
import { IntegratedMvp } from './features/findings/IntegratedMvp';
import './style.css';

const view = window.location.pathname === '/phase5' ? <IntegratedMvp /> : window.location.pathname === '/phase4' ? <AssessmentLab /> : window.location.pathname === '/phase3' ? <EvidenceLab /> : window.location.pathname === '/phase2' ? <ImportLab /> : <App />;
createRoot(document.getElementById('root')!).render(<StrictMode>{view}</StrictMode>);
