# OpenEmotion MVP-1

An always-on emotional core daemon ("emotiond") that experiences time (continuous drift/decay), maintains object-specific attachment (bond) and grudge, and returns a Response Plan JSON for an LLM to speak.

## Architecture

- **emotiond**: Long-lived daemon process written in Python
- **FastAPI**: Web API for interaction
- **SQLite**: Persistent storage for emotional state
- **OpenClaw Skill**: Integration with OpenClaw agent framework

## Quick Start

### Prerequisites

- Python 3.10+ 
- Ubuntu (recommended) or other Linux distribution

### Installation and Setup

1. **Clone and navigate to the repository:**
   ```bash
   cd /home/moonlight/Project/Github/MyProject/Emotion/OpenEmotion
   ```

2. **Create virtual environment and install dependencies:**
   ```bash
   make venv
   ```

3. **Run the daemon:**
   ```bash
   make run
   ```

4. **Verify the daemon is running:**
   ```bash
   curl -s http://127.0.0.1:18080/health
   ```
   Expected response: `{"ok": true, "ts": "..."}`

## Complete Runbook

### Virtual Environment Setup

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -e .
```

### Daemon Startup Procedures

#### Manual Startup

```bash
# Activate virtual environment
source venv/bin/activate

# Start the daemon
python -m emotiond.main
```

#### Using Make Commands

```bash
# Quick start with virtual environment
make venv  # Creates venv and installs dependencies
make run   # Starts the daemon
```

#### Using Convenience Runner

```bash
# Use the runner script (handles virtual environment automatically)
python scripts/run_daemon.py
```

### Systemd User Service (Production Deployment)

Systemd deployment allows emotiond to run persistently as a user service:

To run emotiond as a systemd user service for persistent operation:

1. **Copy service file:**
   ```bash
   mkdir -p ~/.config/systemd/user/
   cp deploy/systemd/user/emotiond.service ~/.config/systemd/user/
   ```

2. **Reload and enable service:**
   ```bash
   systemctl --user daemon-reload
   systemctl --user enable emotiond.service
   systemctl --user start emotiond.service
   ```

3. **Check service status:**
   ```bash
   systemctl --user status emotiond.service
   ```

4. **View logs:**
   ```bash
   journalctl --user -u emotiond.service -f
   ```

### Testing

#### Running Tests

```bash
# Run all tests
make test

# Run specific test file
python -m pytest tests/test_fastapi_service.py -v

# Run tests with coverage
python -m pytest --cov=emotiond tests/
```

#### Type Checking

```bash
# Run mypy type checking
mypy emotiond/
```

### Demo and Evaluation

#### Demo Usage

#### Demo CLI

```bash
# Run the demo CLI with deterministic scenarios
make demo

# Or run directly
python scripts/demo_cli.py
```

The demo showcases:
- Acceptance/rejection scenarios
- Betrayal/repair dynamics
- Separation gap demonstrating time-based affect dynamics
- Sadness persistence
- Object-specific grudge behavior
- Attachment separation pain

#### Evaluation Suite

```bash
# Run the evaluation suite comparing core enabled vs disabled
python scripts/eval_suite.py
```

This generates an evaluation report at `artifacts/eval_report.md` comparing:
- Core emotion dynamics enabled (E)
- Core emotion dynamics disabled (S)

### OpenClaw Skill Usage

After starting the daemon, you can use the OpenClaw skill:

```bash
# Navigate to the skill directory
cd openclaw_skill/emotion_core

# Use the skill to interact with emotiond
python skill.py --help
```

## API Reference

### Endpoints

#### `GET /health`
Health check endpoint.

**Response:**
```json
{
  "ok": true,
  "ts": "2026-02-26T12:11:00.123456"
}
```

#### `POST /event`
Ingest events to update emotional state.

**Request:**
```json
{
  "type": "user_message",
  "actor": "user",
  "target": "assistant", 
  "text": "Hello, how are you?",
  "meta": {}
}
```

**Event Types:**
- `user_message`: User sends a message
- `assistant_reply`: Assistant responds
- `world_event`: External world event

#### `POST /plan`
Generate response plan based on current emotional state.

**Request:**
```json
{
  "user_id": "user",
  "user_text": "Hello, how are you?"
}
```

**Response:**
```json
{
  "tone": "friendly",
  "intent": "engage",
  "focus_target": "user",
  "key_points": ["acknowledge greeting", "express current state"],
  "constraints": ["be concise", "maintain appropriate emotional tone"],
  "emotion": {
    "valence": 0.2,
    "arousal": 0.4
  },
  "relationship": {
    "bond": 0.7,
    "grudge": 0.1
  }
}
```

## Configuration

### Environment Variables

- `EMOTIOND_DB_PATH`: Database file path (default: `./data/emotiond.db`)
- `EMOTIOND_PORT`: API port (default: `18080`)
- `EMOTIOND_HOST`: Bind address (default: `127.0.0.1`)
- `EMOTIOND_K_AROUSAL`: Arousal constant for subjective time (default: `1.0`)
- `EMOTIOND_DISABLE_CORE`: Disable core emotion dynamics (default: `0`)

### Database

The SQLite database is stored at `./data/emotiond.db` by default. Key tables:
- `state`: Current emotional state (single row)
- `relationships`: Bond/grudge values per target
- `events`: Event history (append-only)

## Development

### Project Structure

```
├── emotiond/           # Core daemon package
├── tests/              # Test suite
├── scripts/            # Utility scripts
├── deploy/             # Deployment configurations
├── openclaw_skill/     # OpenClaw integration
├── artifacts/          # Generated reports
└── data/               # Database and runtime data
```

### Key Components

- **Core Emotion Processing**: `emotiond/core.py`
- **Database Operations**: `emotiond/db.py`
- **API Endpoints**: `emotiond/api.py`
- **Main Daemon**: `emotiond/daemon.py`

### Testing Strategy

The test suite includes:
- Unit tests for individual components
- Integration tests for API endpoints
- Comprehensive tests for emotion dynamics
- Documentation validation tests

## Troubleshooting

### Common Issues

1. **Database errors**: Ensure the `data/` directory exists and is writable
2. **Port conflicts**: Check if port 18080 is already in use
3. **Virtual environment issues**: Make sure `venv/bin/activate` is sourced
4. **Systemd service failures**: Check logs with `journalctl --user -u emotiond.service`

### Debug Mode

For debugging, you can run the daemon with verbose logging:

```bash
EMOTIOND_DEBUG=1 python -m emotiond.daemon
```

## Contributing

1. Create a feature branch
2. Write tests for new functionality
3. Ensure all tests pass
4. Run type checking
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.