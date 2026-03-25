/**
 * Entry point for the AI-Augmented SOAR Kibana plugin.
 *
 * Exports the plugin factory function used by the Kibana platform
 * to instantiate and register the plugin.
 */

import { AiAugmentedSoarPlugin } from './plugin';

/** Plugin factory called by the Kibana platform. */
export function plugin(): AiAugmentedSoarPlugin {
  return new AiAugmentedSoarPlugin();
}
