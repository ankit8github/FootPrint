import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { App } from './App';
import { ImportLab } from './features/imports/ImportLab';
import './style.css';

createRoot(document.getElementById('root')!).render(<StrictMode>{window.location.pathname === '/phase2' ? <ImportLab /> : <App />}</StrictMode>);
