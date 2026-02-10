---
name: appfnd-agent-run-local
description: Run an App Foundation agent locally for development and testing. Use when the user wants to run, test, or debug their agent on their local machine.
---

# Running App Foundation Agent Locally

This skill provides instructions for running an App Foundation agent locally for development and testing purposes.

## Prerequisites

Before running locally, ensure you have:

- **Python 3.13+** installed
- **SAP Artifactory access** for private packages
- **AI Core credentials** for LLM access

## Step 1: Get Artifactory Credentials

1. Go to [Artifactory User Profile](https://common.repositories.cloud.sap/ui/user_profile)
2. Click on **Edit Profile**
3. Generate an **Identity Token**
4. Copy the generated token

## Step 2: Create Environment File

Create `app/.env.local` with the following content:

```env
# Artifactory Credentials (for installing private packages)
ARTIFACTORY_USER=<your-i-number>
ARTIFACTORY_TOKEN=<your-artifactory-token>

# SAP AI Core Credentials
AICORE_CLIENT_ID=<your-client-id>
AICORE_CLIENT_SECRET=<your-client-secret>
AICORE_AUTH_URL=<your-auth-url>
AICORE_BASE_URL=<your-base-url>
AICORE_RESOURCE_GROUP=<your-resource-group>

# Server Configuration (optional)
HOST=0.0.0.0
PORT=5000
AGENT_PUBLIC_URL=http://localhost:5000/
```

**Note:** Replace all `<placeholder>` values with your actual credentials.

## Step 3: Create Virtual Environment

Create an isolated Python environment for the project:

```bash
# Create virtual environment
python3 -m venv .venv

# Activate virtual environment (macOS/Linux)
source .venv/bin/activate

# Activate virtual environment (Windows)
.venv\Scripts\activate
```

## Step 4: Install Dependencies

Run the following commands to install dependencies using SAP Artifactory:

```bash
# Export Artifactory credentials
export $(grep -E '^ARTIFACTORY_' app/.env.local | xargs)

# Install dependencies in virtual environment
.venv/bin/pip install -r requirements.txt \
  --index-url "https://${ARTIFACTORY_USER}:${ARTIFACTORY_TOKEN}@common.repositories.cloud.sap/artifactory/api/pypi/application-foundation-sdk-python/simple" \
  --extra-index-url "https://pypi.org/simple"
```

## Step 5: Run the Agent

Start the agent server:

```bash
# Export all environment variables and run the agent
export $(grep -v '^#' app/.env.local | xargs) && .venv/bin/python app/main.py --host 0.0.0.0 --port 5000
```

The agent will start and listen on `http://localhost:5000`.

**Expected output:**
```
INFO:application_foundation.aicore:Loaded AICORE_CLIENT_ID from environment variable
INFO:application_foundation.aicore:Loaded AICORE_CLIENT_SECRET from environment variable
INFO:application_foundation.aicore:Loaded AICORE_AUTH_URL from environment variable
INFO:application_foundation.aicore:Loaded AICORE_BASE_URL from environment variable
INFO:application_foundation.aicore:Loaded AICORE_RESOURCE_GROUP from environment variable
INFO:__main__:Starting A2A server at http://0.0.0.0:5000
INFO:     Started server process [...]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:5000 (Press CTRL+C to quit)
```

## Step 6: Test the Agent

### 6.1 Verify Agent is Running

Check the agent card endpoint to verify the agent is responding:

```bash
curl http://localhost:5000/.well-known/agent.json
```

**Expected response:** JSON containing agent metadata including name, description, capabilities, and skills.

Example response:
```json
{
  "name": "Sample Agent",
  "description": "A sample AI agent demonstrating Application Foundation Agent capabilities.",
  "capabilities": {"pushNotifications": false, "streaming": true},
  "protocolVersion": "0.3.0",
  "skills": [...]
}
```

### 6.2 Send a Test Message

Send a message to the agent using the A2A protocol to verify end-to-end functionality:

```bash
curl --request POST \
  --url http://localhost:5000/ \
  --header 'content-type: application/json' \
  --data '{
  "jsonrpc": "2.0",
  "method": "message/send",
  "id": "test-1",
  "params": {
    "message": {
      "messageId": "msg-001",
      "role": "user",
      "parts": [
        {
          "kind": "text",
          "text": "Hello, what can you help me with?"
        }
      ]
    }
  }
}'
```

**Expected response:** JSON containing the agent's response with:
- `result.status.state`: Should be `"completed"`
- `result.artifacts`: Contains the agent's text response
- `result.contextId`: A unique context ID for the conversation
- `result.id`: The task ID

Example successful response structure:
```json
{
  "id": "test-1",
  "jsonrpc": "2.0",
  "result": {
    "status": {"state": "completed", "timestamp": "..."},
    "artifacts": [{
      "artifactId": "...",
      "name": "agent_result",
      "parts": [{"kind": "text", "text": "Hello! I'm happy to help you with..."}]
    }],
    "contextId": "...",
    "id": "..."
  }
}
```

### 6.3 Test with Context (Multi-turn Conversation)

To continue a conversation, include the `contextId` from the previous response:

```bash
curl --request POST \
  --url http://localhost:5000/ \
  --header 'content-type: application/json' \
  --data '{
  "jsonrpc": "2.0",
  "method": "message/send",
  "id": "test-2",
  "params": {
    "message": {
      "messageId": "msg-002",
      "role": "user",
      "parts": [{"kind": "text", "text": "Tell me more about coding assistance."}],
      "contextId": "<contextId-from-previous-response>"
    }
  }
}'
```

## Troubleshooting

### Common Issues

1. **Artifactory authentication failed**
   - Verify your I-number and token are correct
   - Ensure the token hasn't expired
   - Regenerate the token if needed

2. **AI Core connection failed**
   - Check all AICORE_* environment variables are set
   - Verify credentials are valid
   - Ensure you have access to the specified AI Core instance
   - Check the AICORE_AUTH_URL and AICORE_BASE_URL are correct

3. **Port already in use**
   - Change the port: `.venv/bin/python app/main.py --port 5001`
   - Or kill the process using the port: `lsof -ti:5000 | xargs kill`

4. **Module not found errors**
   - Ensure you're using the virtual environment: `.venv/bin/python`
   - Ensure dependencies are installed with the correct index URL
   - Try reinstalling: `.venv/bin/pip install -r requirements.txt --force-reinstall`

5. **LLM response errors**
   - Check the terminal logs for LiteLLM errors
   - Verify AI Core credentials have access to the specified model
   - Check if the model name in the agent configuration is correct

### Debug Mode

For more verbose logging, set the log level:

```bash
export LOG_LEVEL=DEBUG
export $(grep -v '^#' app/.env.local | xargs) && .venv/bin/python app/main.py --host 0.0.0.0 --port 5000
```

### Checking Server Logs

The server logs will show:
- Incoming requests with HTTP method and path
- LiteLLM model calls (e.g., `LiteLLM completion() model= anthropic--claude-4.5-sonnet; provider = sap`)
- Response status codes

## Quick Reference

| Command | Description |
|---------|-------------|
| `python3 -m venv .venv` | Create virtual environment |
| `source .venv/bin/activate` | Activate virtual environment (macOS/Linux) |
| `.venv/bin/pip install -r requirements.txt ...` | Install dependencies |
| `export $(grep -v '^#' app/.env.local \| xargs)` | Load environment variables |
| `.venv/bin/python app/main.py --host 0.0.0.0 --port 5000` | Run the agent |
| `curl http://localhost:5000/.well-known/agent.json` | Get agent metadata |
| `curl -X POST http://localhost:5000/ -H 'content-type: application/json' -d '...'` | Send message |
| `lsof -ti:5000 \| xargs kill` | Kill process on port 5000 |
| `CTRL+C` | Stop the running agent |

## Restarting the Agent

To restart the agent after stopping it:

```bash
# If virtual environment is not activated
export $(grep -v '^#' app/.env.local | xargs) && .venv/bin/python app/main.py --host 0.0.0.0 --port 5000

# If virtual environment is activated
export $(grep -v '^#' app/.env.local | xargs) && python app/main.py --host 0.0.0.0 --port 5000