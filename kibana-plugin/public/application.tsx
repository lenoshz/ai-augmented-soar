/**
 * Application mount function for the AI-Augmented SOAR Kibana plugin.
 *
 * Renders the main React application into the Kibana DOM element
 * provided by the platform.
 */

import React from 'react';
import { createRoot } from 'react-dom/client';
import { AiAugmentedSoarApp } from './components/AiAugmentedSoarApp';

interface AppMountParams {
  element: HTMLElement;
}

/**
 * Mount the AI-Augmented SOAR React app into the given DOM element.
 * Returns an unmount function for Kibana to call on navigation away.
 */
export function renderApp(params: AppMountParams): () => void {
  const root = createRoot(params.element);
  root.render(<AiAugmentedSoarApp />);
  return () => root.unmount();
}
