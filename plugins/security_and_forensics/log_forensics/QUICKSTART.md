# Quick Start Guide: `domain.log_forensics` (v1.0.0)

> High-throughput SIEM log stream parser, anomaly detection, and incident timeline reconstructor

## 🎯 When to Use
Use this plugin when you need capabilities related to `general`.

Common trigger intents:
- **`parse_log_stream`**: Parse raw text log stream (Syslog, JSONL, Apache/Nginx, or standard key-value) into structured records
- **`detect_log_anomalies`**: Detect attack patterns (brute force, 4xx/5xx spikes, privilege escalation, suspicious IPs) in parsed logs
- **`build_incident_timeline`**: Sort and synthesize a chronological incident timeline with severity tagging

## 🛠️ How to Use (Agent & User)
### Python / Runtime Tool Call:
```python
result = await runtime.tools.invoke('domain.log_forensics.parse_log_stream', {'log_content': '<log_content>', 'format_hint': '<format_hint>'})
```

### CLI Quick Action:
```powershell
harness tool list --provider domain.log_forensics
harness plugin enable domain.log_forensics
```

## ⚡ Available Entrypoints & Skills
- **`parse_log_stream(log_content: string, format_hint: string)`**
  Parse raw text log stream (Syslog, JSONL, Apache/Nginx, or standard key-value) into structured records
- **`detect_log_anomalies(log_events: array)`**
  Detect attack patterns (brute force, 4xx/5xx spikes, privilege escalation, suspicious IPs) in parsed logs
- **`build_incident_timeline(log_events: array)`**
  Sort and synthesize a chronological incident timeline with severity tagging