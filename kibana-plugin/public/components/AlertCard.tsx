/**
 * Alert card component displaying enriched alert details including
 * AI summary, MITRE context, response steps, and analyst tools.
 */

import React, { useState } from 'react';
import {
  EuiAccordion,
  EuiBadge,
  EuiCallOut,
  EuiCodeBlock,
  EuiFlexGroup,
  EuiFlexItem,
  EuiPanel,
  EuiSpacer,
  EuiText,
  EuiTitle,
} from '@elastic/eui';
import type { EnrichedAlert } from './AiAugmentedSoarApp';
import { AnalystChat } from './AnalystChat';
import { FeedbackWidget } from './FeedbackWidget';

const SEVERITY_COLORS: Record<string, string> = {
  critical: 'danger',
  high: 'warning',
  medium: 'primary',
  low: 'default',
};

interface AlertCardProps {
  alert: EnrichedAlert;
}

/** Card component rendering all enrichment data for a single alert. */
export const AlertCard: React.FC<AlertCardProps> = ({ alert }) => {
  const [chatOpen, setChatOpen] = useState<boolean>(false);
  const severityColor = SEVERITY_COLORS[alert.severity] ?? 'default';

  return (
    <EuiPanel paddingSize="l" hasBorder>
      {/* Header: rule name + severity + MITRE badges */}
      <EuiFlexGroup alignItems="center" gutterSize="s">
        <EuiFlexItem grow>
          <EuiTitle size="s">
            <h2>{alert.rule_name}</h2>
          </EuiTitle>
        </EuiFlexItem>
        <EuiFlexItem grow={false}>
          <EuiBadge color={severityColor as any}>{alert.severity.toUpperCase()}</EuiBadge>
        </EuiFlexItem>
        <EuiFlexItem grow={false}>
          <EuiBadge color="hollow">{alert.context.mitre_tactic}</EuiBadge>
        </EuiFlexItem>
        <EuiFlexItem grow={false}>
          <EuiBadge color="hollow">{alert.context.mitre_technique}</EuiBadge>
        </EuiFlexItem>
      </EuiFlexGroup>

      <EuiSpacer size="m" />

      {/* AI Summary */}
      <EuiCallOut title="AI Summary" iconType="compute" color="primary">
        <p>{alert.summary}</p>
      </EuiCallOut>

      <EuiSpacer size="m" />

      {/* Response steps accordion */}
      <EuiAccordion
        id={`response-${alert.alert_id}`}
        buttonContent="Response Steps"
        paddingSize="m"
      >
        <EuiText size="s">
          <strong>Immediate Actions</strong>
          <ul>
            {alert.response.immediate_actions.map((action, i) => (
              <li key={i}>{action}</li>
            ))}
          </ul>
          <strong>Investigation Steps</strong>
          <ul>
            {alert.response.investigation_steps.map((step, i) => (
              <li key={i}>{step}</li>
            ))}
          </ul>
        </EuiText>

        {alert.response.eql_hunt_query && (
          <>
            <EuiSpacer size="s" />
            <EuiText size="s">
              <strong>EQL Hunt Query</strong>
            </EuiText>
            <EuiCodeBlock language="sql" isCopyable paddingSize="s">
              {alert.response.eql_hunt_query}
            </EuiCodeBlock>
          </>
        )}
      </EuiAccordion>

      {/* Escalation callout */}
      {alert.response.escalation_criteria && (
        <>
          <EuiSpacer size="m" />
          <EuiCallOut title="Escalation Criteria" iconType="alert" color="warning">
            <p>{alert.response.escalation_criteria}</p>
          </EuiCallOut>
        </>
      )}

      <EuiSpacer size="m" />

      {/* Analyst chat and feedback */}
      <EuiFlexGroup gutterSize="m">
        <EuiFlexItem grow={false}>
          <AnalystChat alert={alert} />
        </EuiFlexItem>
        <EuiFlexItem grow={false}>
          <FeedbackWidget alertId={alert.alert_id} />
        </EuiFlexItem>
      </EuiFlexGroup>
    </EuiPanel>
  );
};
