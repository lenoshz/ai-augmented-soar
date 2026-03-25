/**
 * MITRE ATT&CK tactic heatmap component.
 *
 * Displays a count of enriched alerts grouped by MITRE tactic
 * using EuiStat cards. Shows an empty state message when no alerts exist.
 */

import React from 'react';
import {
  EuiFlexGroup,
  EuiFlexItem,
  EuiPanel,
  EuiSpacer,
  EuiStat,
  EuiText,
  EuiTitle,
} from '@elastic/eui';
import type { EnrichedAlert } from './AiAugmentedSoarApp';

interface MitreHeatmapProps {
  alerts: EnrichedAlert[];
}

/** Compute tactic counts from an array of enriched alerts. */
function computeTacticCounts(alerts: EnrichedAlert[]): Record<string, number> {
  return alerts.reduce<Record<string, number>>((acc, alert) => {
    const tactic = alert.context.mitre_tactic || 'Unknown';
    acc[tactic] = (acc[tactic] ?? 0) + 1;
    return acc;
  }, {});
}

/** Heatmap of MITRE ATT&CK tactic alert counts. */
export const MitreHeatmap: React.FC<MitreHeatmapProps> = ({ alerts }) => {
  const tacticCounts = computeTacticCounts(alerts);
  const entries = Object.entries(tacticCounts).sort((a, b) => b[1] - a[1]);

  return (
    <EuiPanel paddingSize="l" hasBorder>
      <EuiTitle size="s">
        <h2>MITRE ATT&amp;CK Tactic Distribution</h2>
      </EuiTitle>
      <EuiText size="xs" color="subdued">
        <p>Alert counts grouped by MITRE ATT&amp;CK tactic across enriched alerts.</p>
      </EuiText>
      <EuiSpacer size="m" />

      {entries.length === 0 ? (
        <EuiText color="subdued">
          <p>No enriched alerts available. Enrich some alerts to see the tactic distribution.</p>
        </EuiText>
      ) : (
        <EuiFlexGroup wrap responsive gutterSize="m">
          {entries.map(([tactic, count]) => (
            <EuiFlexItem key={tactic} grow={false} style={{ minWidth: 160 }}>
              <EuiStat
                title={String(count)}
                description={tactic}
                titleColor={count >= 5 ? 'danger' : count >= 2 ? 'warning' : 'primary'}
                textAlign="center"
              />
            </EuiFlexItem>
          ))}
        </EuiFlexGroup>
      )}
    </EuiPanel>
  );
};
