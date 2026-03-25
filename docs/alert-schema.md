# Alert Schema Reference

This document describes the alert data schema used by the AI-Augmented SOAR enrichment service. Alerts conform to the [Elastic Common Schema (ECS)](https://www.elastic.co/guide/en/ecs/current/index.html) where applicable.

## ECS Overview

The Elastic Common Schema provides a consistent structure for event data across Elasticsearch. AI-Augmented SOAR alert payloads map to ECS fields where possible to ensure compatibility with Kibana Security and detection rules.

## Alert Payload Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `alert_id` | `string` | ✅ | Unique identifier for the alert (UUID recommended) |
| `rule_name` | `string` | ✅ | Name of the detection rule that triggered the alert |
| `severity` | `string` | ✅ | Alert severity: `critical`, `high`, `medium`, or `low` |
| `timestamp` | `string` | ✅ | ISO 8601 UTC timestamp of the alert |
| `description` | `string` | ❌ | Human-readable description of what triggered the alert |
| `host_name` | `string` | ❌ | FQDN or short hostname of the affected system |
| `host_ip` | `string` | ❌ | IP address of the affected host |
| `user_name` | `string` | ❌ | Username associated with the alert activity |
| `process_name` | `string` | ❌ | Name of the process involved (ECS: `process.name`) |
| `process_command_line` | `string` | ❌ | Full command line string (ECS: `process.command_line`) |
| `network_destination_ip` | `string` | ❌ | Destination IP for network events (ECS: `destination.ip`) |
| `network_destination_port` | `integer` | ❌ | Destination port (ECS: `destination.port`) |
| `file_path` | `string` | ❌ | File path involved in the alert (ECS: `file.path`) |
| `tags` | `string[]` | ❌ | Detection rule tags, typically MITRE ATT&CK technique IDs |
| `raw_event` | `object` | ❌ | Raw source event data for additional context |

## Process Events

Process-based alerts (e.g., PowerShell execution, suspicious child processes) should include:

```json
{
  "alert_id": "a1b2c3d4-...",
  "rule_name": "Suspicious PowerShell Execution",
  "severity": "high",
  "timestamp": "2025-06-01T08:23:11Z",
  "host_name": "workstation-042",
  "user_name": "jsmith",
  "process_name": "powershell.exe",
  "process_command_line": "powershell.exe -ExecutionPolicy Bypass -enc JABjAG0AZAA...",
  "tags": ["T1059.001", "Windows", "Execution"]
}
```

## Network Events

Network-based alerts (e.g., C2 beaconing, DNS tunnelling) should include:

```json
{
  "alert_id": "b2c3d4e5-...",
  "rule_name": "Data Exfiltration via DNS",
  "severity": "high",
  "timestamp": "2025-06-01T13:17:52Z",
  "host_name": "fin-workstation-07",
  "network_destination_ip": "8.8.8.8",
  "network_destination_port": 53,
  "tags": ["T1048.003", "DNS", "Exfiltration"]
}
```

## Authentication Events

Authentication-based alerts (e.g., brute force, credential stuffing) should include:

```json
{
  "alert_id": "c3d4e5f6-...",
  "rule_name": "Brute Force Login Attempt",
  "severity": "medium",
  "timestamp": "2025-06-01T10:45:30Z",
  "host_name": "web-server-01",
  "user_name": "root",
  "network_destination_ip": "203.0.113.45",
  "network_destination_port": 22,
  "tags": ["T1110", "Authentication", "Credential Access"]
}
```

## Schema Checklist

- [ ] `alert_id` is a UUID v4
- [ ] `severity` is lowercase (`critical`, `high`, `medium`, `low`)
- [ ] `timestamp` is ISO 8601 UTC format (ending in `Z` or `+00:00`)
- [ ] Process alerts include `process_name` and `process_command_line`
- [ ] Network alerts include `network_destination_ip` and `network_destination_port`
- [ ] `tags` contains relevant MITRE ATT&CK technique IDs where known
