# OpenEmotion MVP-1

An always-on emotional core daemon ("emotiond") that experiences time (continuous drift/decay), maintains object-specific attachment (bond) and grudge, and returns a Response Plan JSON for an LLM to speak.

## Architecture

- **emotiond**: Long-lived daemon process written in Python
- **FastAPI**: Web API for interaction
- **SQLite**: Persistent storage for emotional state
- **OpenClaw Skill**: Integration with OpenClaw agent framework

## Runbook

### Quick Start

1. **Setup environment:**
   ```bash
   cd /home/moonlight/Project/Github/MyProject/Emotion/OpenEmotion
   make venv
   ```

2. **Run daemon:**
   ```bash
   make run
   ```

3. **Test health:**
   ```bash
   curl -s http://127.0.0.1:18080/health
   ```

4. **Run tests:**
   ```bash
   make test
   ```

5. **Run demo:**
   ```bash
   make demo
   ```

### Systemd User Service (Optional)

To run emotiond as a systemd user service:

1. Copy the service file:
   ```bash
   cp deploy/systemd/user/emotiond.service ~/.config/systemd/user/
   ```

2. Reload systemd:
   ```bash
   systemctl --user daemon-reload
   ```

3. Enable and start the service:
   ```bash
   systemctl --user enable emotiond.service
   systemctl --user start emotiond.service
   ```

4. Check status:
   ```bash
   systemctl --user status emotiond.service
   ```

## API Endpoints

- `GET /health` - Health check
- `POST /event` - Ingest events and update emotional state
- `POST /plan` - Generate response plan based on current emotional state

## Development

- Tests: `make test`
- Type checking: `mypy emotiond/` (if mypy is configured)
- Code formatting: `black emotiond/ tests/` (if black is configured)