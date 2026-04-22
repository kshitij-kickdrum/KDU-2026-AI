# API Contract

## POST `/chat/stream`
Request:
```json
{
  "message": "What's the weather in Paris?",
  "session_id": "sess_abc123",
  "stream": true
}
```

Response: `text/event-stream` with events:
- `content`
- `tool_status`
- `tool_result`
- `usage_update`
- `done`

## GET `/usage/stats`
Query params:
- `session_id` (required)
- `detailed` (optional, bool)

## GET `/health`
Returns service status and timestamp.

