/**
 * Main application component for the AI-Augmented SOAR Kibana plugin.
 *
 * Fetches enriched alerts on mount and refreshes every 15 seconds.
 * Renders the dashboard layout with alert cards and MITRE heatmap.
 */

import React, { useCallback, useEffect, useState } from 'react';
import {
  EuiFlexGroup,
  EuiFlexItem,
  EuiLoadingSpinner,
  EuiPage,
  EuiPageBody,
  EuiPageHeader,
  EuiPageHeaderSection,
  EuiText,
  EuiTitle,
} from '@elastic/eui';
import { AlertCard } from './AlertCard';
import { MitreHeatmap } from './MitreHeatmap';

/** Inline interface matching the EnrichedAlert model from the enrichment service. */
export interface EnrichedAlert {
  alert_id: string;
  rule_name: string;
  severity: string;
  timestamp: string;
  summary: string;
  context: {
    mitre_tactic: string;
    mitre_tactic_id: string;
    mitre_technique: string;
    mitre_technique_id: string;
    asset_owner: string | null;
    asset_criticality: string | null;
    ioc_hits: string[];
    similar_alert_count: number;
  };
  response: {
    immediate_actions: string[];
    investigation_steps: string[];
    escalation_criteria: string;
    eql_hunt_query: string;
  };
  enriched_at: string;
  ai_enriched: boolean;
}

const ENRICHMENT_SERVICE_URL = 'http://localhost:8000';
const REFRESH_INTERVAL_MS = 15_000;

/** Main dashboard component for the AI-Augmented SOAR plugin. */
export const AiAugmentedSoarApp: React.FC = () => {
  const [alerts, setAlerts] = useState<EnrichedAlert[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  const fetchAlerts = useCallback(async () => {
    try {
      const response = await fetch(`${ENRICHMENT_SERVICE_URL}/api/v1/alerts/enriched`);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      const data: EnrichedAlert[] = await response.json();
      setAlerts(data);
    } catch (err) {
      console.error('[ai-augmented-soar] Failed to fetch enriched alerts:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAlerts();
    const interval = setInterval(fetchAlerts, REFRESH_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [fetchAlerts]);

  return (
    <EuiPage paddingSize="l">
      <EuiPageBody>
        <EuiPageHeader>
          <EuiPageHeaderSection>
            <EuiTitle size="l">
              <h1>AI-Augmented SOAR</h1>
            </EuiTitle>
            <EuiText color="subdued">
              <p>AI-enriched security alerts with MITRE ATT&amp;CK context and response guidance</p>
            </EuiText>
          </EuiPageHeaderSection>
        </EuiPageHeader>

        {loading ? (
          <EuiFlexGroup justifyContent="center" alignItems="center" style={{ minHeight: 200 }}>
            <EuiFlexItem grow={false}>
              <EuiLoadingSpinner size="xl" />
            </EuiFlexItem>
          </EuiFlexGroup>
        ) : (
          <EuiFlexGroup direction="column" gutterSize="l">
            <EuiFlexItem>
              <MitreHeatmap alerts={alerts} />
            </EuiFlexItem>
            {alerts.map((alert) => (
              <EuiFlexItem key={alert.alert_id}>
                <AlertCard alert={alert} />
              </EuiFlexItem>
            ))}
          </EuiFlexGroup>
        )}
      </EuiPageBody>
    </EuiPage>
  );
};
