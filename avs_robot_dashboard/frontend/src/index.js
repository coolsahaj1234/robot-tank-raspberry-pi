import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';

const root = ReactDOM.createRoot(document.getElementById('root'));
// Note: StrictMode removed because streetscape.gl v1.0.13 is incompatible with
// React 18's double-invocation of lifecycle methods
root.render(<App />);
