/**
 * Feedback widget for analyst thumbs-up/thumbs-down rating of enriched alerts.
 *
 * Posts feedback to the enrichment service feedback endpoint.
 */

import React, { useState } from 'react';
import {
  EuiButtonIcon,
  EuiFlexGroup,
  EuiFlexItem,
  EuiText,
  EuiToolTip,
} from '@elastic/eui';

interface FeedbackWidgetProps {
  alertId: string;
}

const ENRICHMENT_SERVICE_URL = 'http://localhost:8000';

/** Thumbs up/down feedback widget for analyst rating of enrichments. */
export const FeedbackWidget: React.FC<FeedbackWidgetProps> = ({ alertId }) => {
  const [submitted, setSubmitted] = useState<'positive' | 'negative' | null>(null);
  const [loading, setLoading] = useState<boolean>(false);

  const handleFeedback = async (rating: 'positive' | 'negative') => {
    if (loading || submitted !== null) return;
    setLoading(true);

    try {
      await fetch(`${ENRICHMENT_SERVICE_URL}/api/v1/feedback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ alert_id: alertId, rating }),
      });
      setSubmitted(rating);
    } catch (err) {
      console.error('[ai-augmented-soar] Failed to submit feedback:', err);
    } finally {
      setLoading(false);
    }
  };

  if (submitted) {
    return (
      <EuiText size="xs" color="subdued">
        <p>Feedback submitted: {submitted === 'positive' ? '👍' : '👎'}</p>
      </EuiText>
    );
  }

  return (
    <EuiFlexGroup gutterSize="xs" alignItems="center">
      <EuiFlexItem grow={false}>
        <EuiText size="xs" color="subdued">
          <span>Rate enrichment:</span>
        </EuiText>
      </EuiFlexItem>
      <EuiFlexItem grow={false}>
        <EuiToolTip content="Helpful enrichment">
          <EuiButtonIcon
            iconType="thumbsUp"
            aria-label="Positive feedback"
            color="success"
            onClick={() => void handleFeedback('positive')}
            isDisabled={loading}
          />
        </EuiToolTip>
      </EuiFlexItem>
      <EuiFlexItem grow={false}>
        <EuiToolTip content="Unhelpful enrichment">
          <EuiButtonIcon
            iconType="thumbsDown"
            aria-label="Negative feedback"
            color="danger"
            onClick={() => void handleFeedback('negative')}
            isDisabled={loading}
          />
        </EuiToolTip>
      </EuiFlexItem>
    </EuiFlexGroup>
  );
};
