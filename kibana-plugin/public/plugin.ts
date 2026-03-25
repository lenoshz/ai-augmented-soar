/**
 * Kibana plugin registration for AI-Augmented SOAR.
 *
 * Implements the Plugin interface to register the SOAR dashboard
 * as a Kibana application in the navigation menu.
 */

import type { CoreSetup, CoreStart, Plugin } from '@kbn/core/public';

export class AiAugmentedSoarPlugin implements Plugin {
  /**
   * Called during Kibana setup phase. Registers the SOAR application
   * in the Kibana navigation and maps it to a mount function.
   */
  public setup(core: CoreSetup): void {
    core.application.register({
      id: 'aiAugmentedSoar',
      title: 'AI-Augmented SOAR',
      async mount(params) {
        const { renderApp } = await import('./application');
        return renderApp(params);
      },
    });
  }

  /** Called when Kibana is fully started. No-op for this plugin. */
  public start(_core: CoreStart): void {}

  /** Called when the plugin is stopped. No-op for this plugin. */
  public stop(): void {}
}
