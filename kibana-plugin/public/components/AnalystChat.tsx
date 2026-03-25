/**
 * Multi-turn analyst chat component for investigating enriched alerts.
 *
 * Allows analysts to ask questions about a specific alert and receive
 * AI-powered responses from the enrichment service.
 */

import React, { useState } from 'react';
import {
  EuiButton,
  EuiButtonEmpty,
  EuiFieldText,
  EuiFlexGroup,
  EuiFlexItem,
  EuiPanel,
  EuiSpacer,
  EuiText,
  EuiTitle,
  EuiToast,
} from '@elastic/eui';
import type { EnrichedAlert } from './AiAugmentedSoarApp';

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

interface AnalystChatProps {
  alert: EnrichedAlert;
}

const ENRICHMENT_SERVICE_URL = 'http://localhost:8000';

/** Multi-turn chat interface for analyst alert investigation. */
export const AnalystChat: React.FC<AnalystChatProps> = ({ alert }) => {
  const [open, setOpen] = useState<boolean>(false);
  const [history, setHistory] = useState<ChatMessage[]>([]);
  const [inputText, setInputText] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [errorToast, setErrorToast] = useState<string | null>(null);

  const handleSend = async () => {
    if (!inputText.trim()) return;

    const userMessage = inputText.trim();
    setInputText('');
    const updatedHistory: ChatMessage[] = [...history, { role: 'user', content: userMessage }];
    setHistory(updatedHistory);
    setLoading(true);

    try {
      const response = await fetch(`${ENRICHMENT_SERVICE_URL}/api/v1/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          alert_id: alert.alert_id,
          alert,
          history: updatedHistory.slice(0, -1).map(({ role, content }) => ({ role, content })),
          message: userMessage,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data: { response: string } = await response.json();
      setHistory([...updatedHistory, { role: 'assistant', content: data.response }]);
    } catch (err) {
      setErrorToast(`Chat request failed: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setLoading(false);
    }
  };

  if (!open) {
    return (
      <EuiButtonEmpty iconType="discuss" onClick={() => setOpen(true)}>
        Analyst Chat
      </EuiButtonEmpty>
    );
  }

  return (
    <EuiPanel paddingSize="m" style={{ width: 480 }}>
      <EuiFlexGroup justifyContent="spaceBetween" alignItems="center">
        <EuiFlexItem>
          <EuiTitle size="xs">
            <h3>Analyst Chat</h3>
          </EuiTitle>
        </EuiFlexItem>
        <EuiFlexItem grow={false}>
          <EuiButtonEmpty size="xs" onClick={() => setOpen(false)}>
            Close
          </EuiButtonEmpty>
        </EuiFlexItem>
      </EuiFlexGroup>

      <EuiSpacer size="s" />

      {/* Conversation history */}
      <div style={{ maxHeight: 300, overflowY: 'auto', marginBottom: 8 }}>
        {history.map((msg, i) => (
          <EuiPanel
            key={i}
            paddingSize="s"
            color={msg.role === 'user' ? 'plain' : 'subdued'}
            style={{ marginBottom: 4 }}
          >
            <EuiText size="xs">
              <strong>{msg.role === 'user' ? 'You' : 'AI'}:</strong> {msg.content}
            </EuiText>
          </EuiPanel>
        ))}
      </div>

      {/* Input area */}
      <EuiFlexGroup gutterSize="s">
        <EuiFlexItem>
          <EuiFieldText
            placeholder="Ask about this alert..."
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') void handleSend();
            }}
            disabled={loading}
          />
        </EuiFlexItem>
        <EuiFlexItem grow={false}>
          <EuiButton onClick={() => void handleSend()} isLoading={loading} size="s">
            Send
          </EuiButton>
        </EuiFlexItem>
      </EuiFlexGroup>

      {errorToast && (
        <>
          <EuiSpacer size="s" />
          <EuiToast
            title="Error"
            color="danger"
            onClose={() => setErrorToast(null)}
          >
            <p>{errorToast}</p>
          </EuiToast>
        </>
      )}
    </EuiPanel>
  );
};
