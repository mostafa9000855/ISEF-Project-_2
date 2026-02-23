# SmartAI Component Integration Guide

## Overview

This guide explains how all SmartAI components work together as one unified system.

## System Components

### 1. Electron Frontend (UI Layer)
- **File**: `src/electron/main-integrated.js`
- **Port**: N/A (local UI)
- **Responsibility**: 
  - Start all processes
  - Orchestrate communication
  - Display real-time dashboard
  - Handle user interactions
- **Lifecycle**: Started first, stays alive throughout

### 2. C++ Core Engine
- **File**: `src/cpp/core_engine_websocket.cpp`
- **Port**: 8080 (WebSocket to Electron)
- **IPC**: Named pipe to Python
- **Responsibility**:
  - Monitor system in real-time
  - Encrypt all data
  - Execute auto-responses
  - Manage VPN/firewall
- **Lifecycle**: Child process of Electron, auto-restarts if crashes

### 3. Python AI Module
- **File**: `src/python/ai_module_websocket.py`
- **Port**: 8081 (WebSocket to Electron)
- **IPC**: Named pipe from C++
- **Responsibility**:
  - Analyze behavior patterns
  - Detect anomalies
  - Generate predictions
  - Track deception networks
- **Lifecycle**: Child process of Electron, auto-restarts if crashes

### 4. IPC Handler (Message Bus)
- **File**: `src/electron/ipc_handler.js`
- **Responsibility**:
  - Route messages between components
  - Handle request-response patterns
  - Queue messages when unavailable
  - Manage message types and schemas

## Communication Flows

### Flow 1: System Monitoring (Every 5 Seconds)

```
C++ Core                     Electron                    Python AI
    │                            │                          │
    ├─ Collect system data       │                          │
    │  (CPU, RAM, processes)     │                          │
    │                            │                          │
    ├─ Encrypt with AES-256      │                          │
    │                            │                          │
    └──── WebSocket port 8080 ──→│                          │
                                 │                          │
                                 ├─ Decrypt data            │
                                 ├─ Update UI cache         │
                                 ├─ Forward via WebSocket ──→│
                                 │   port 8081              │
                                 │                          │
                                 │          Decrypt data    │
                                 │          Analyze with    │
                                 │          Isolation Forest│
                                 │          Calculate risk  │
                                 │          score            │
                                 │                          │
                                 │←─── Encrypted response ──┤
                                 │    (Risk Score, XAI)     │
                                 │                          │
                                 │ Update real-time         │
                                 │ dashboard with:          │
                                 │ • Risk score             │
                                 │ • Threat explanation     │
                                 │ • Attack predictions     │
                                 │ • Honeypot status        │
```

### Flow 2: Auto-Response Execution

```
Risk Score > 70                Risk Score > 90
     │                              │
     ├─ VPN Auto-Activation    ├─ Emergency Mode
     ├─ Firewall Rule Updates  ├─ Block ALL outbound
     ├─ Process Blocking       └─ Critical alert
     └─ Enhanced Monitoring
```

### Flow 3: Key Rotation (Every 48-72 hours)

```
Timer triggers (48-72h random interval)
         │
         ▼
C++ Generates new 256-bit AES key
         │
         ├─ Secure old key in memory
         │
         ├─ Send new key to Python via encrypted channel
         │
         ├─ Both sides confirm receipt
         │
         ├─ Re-encrypt all 6 databases with new key
         │
         ├─ Verify all data still readable
         │
         ├─ Log rotation event to append-only log
         │
         └─ Securely destroy old key using SecureZeroMemory()
```

## Startup Sequence Details

### Phase 1: Electron Initialization (0-2 seconds)

1. **Electron.app.ready** event fires
2. Create application data directories:
   - `%APPDATA%\SmartAI\databases\`
   - `%APPDATA%\SmartAI\logs\`
   - `%APPDATA%\SmartAI\keys\`
   - `%APPDATA%\SmartAI\config\`
3. Initialize encryption:
   - Generate or load 256-bit AES key
   - Store in memory (not on disk for prod)
4. Create main BrowserWindow for UI
5. Create IPC message handler

### Phase 2: C++ Core Spawn (2-4 seconds)

1. **Electron** spawns C++ process:
   ```bash
   core_engine.exe
   ```
   
2. Environment variables passed:
   ```
   SMARTAI_ENCRYPTION_KEY=<base64_key>
   SMARTAI_WS_PORT=8080
   SMARTAI_PIPE_NAME=smartai_core_pipe
   ```

3. **C++ Core** initializes:
   - Load encryption key from env
   - Start system monitoring thread
   - Attempt to connect to Electron WebSocket (port 8080)
   - Attempt to connect to Python named pipe
   - Output: `✓ Connected to Electron WebSocket on 127.0.0.1:8080`

### Phase 3: Python AI Spawn (4-6 seconds)

1. **Electron** spawns Python process:
   ```bash
   python.exe ai_module_websocket.py
   ```
   
2. Environment variables passed:
   ```
   SMARTAI_ENCRYPTION_KEY=<base64_key>
   SMARTAI_WS_PORT=8081
   SMARTAI_PIPE_NAME=smartai_core_pipe
   SMARTAI_DB_PATH=<path>
   ```

3. **Python AI** initializes:
   - Load encryption key from env
   - Initialize WebSocket server on port 8081
   - Start listening for connections
   - Output: `✓ WebSocket listening on 127.0.0.1:8081`

### Phase 4: Connection Establishment (6-8 seconds)

1. **Electron** waits for WebSocket connections from both components
2. **C++ Core** connects to port 8080
   - Electron marks coreHealthy = true
   - Start sending system data every 5 seconds
3. **Python AI** connects to port 8081
   - Electron marks pythonHealthy = true
   - Ready to receive system data

### Phase 5: Key Sync (8-10 seconds)

1. Electron creates KEY_SYNC message:
   ```json
   {
     "type": "KEY_SYNC",
     "key": "base64_encrypted_key",
     "timestamp": "2026-02-23T...",
     "nonce": "random_nonce"
   }
   ```

2. Encrypt message with current key
3. Send to both C++ (port 8080) and Python (port 8081)
4. Both sides acknowledge receipt
5. Sync complete

### Phase 6: Dashboard Live (10-15 seconds)

1. C++ monitoring thread sends first system data
2. Electron receives and updates UI
3. Python AI receives, analyzes, sends risk score
4. Electron displays all real-time data
5. Dashboard shows: ✓ System monitoring active
6. All components report: **READY**

## Error Handling & Recovery

### If C++ Crashes

```
Detection: Electron receives EOF on WebSocket port 8080
│
└─ Log error: "[C++ CRASH] Connection closed at HH:MM:SS UTC"
   │
   ├─ Alert user: "Core Engine disconnected"
   │
   ├─ Attempt reconnect (5 retries, 10 sec apart)
   │
   └─ If retries exhausted:
      ├─ Kill old process
      ├─ Wait 5 seconds
      └─ Spawn new C++ process
         └─ Return to Phase 2 startup
```

### If Python Crashes

```
Detection: Electron receives EOF on WebSocket port 8081
│
└─ Log error: "[Python CRASH] Connection closed at HH:MM:SS UTC"
   │
   ├─ Alert user: "AI Analysis offline"
   │
   ├─ Attempt reconnect (5 retries, 10 sec apart)
   │
   └─ If retries exhausted:
      ├─ Kill old process
      ├─ Wait 5 seconds
      └─ Spawn new Python process
         └─ Return to Phase 3 startup
```

### If WebSocket Disconnects

```
Retry logic for connection loss (not process crash):
│
├─ Backoff: 5s, 10s, 15s, 20s, 30s
├─ Max retries: 5
├─ Queue messages while reconnecting
└─ Auto-flush queue when reconnected
```

### If Encryption Key Sync Fails

```
Detection: Key sync timeout after 5 seconds
│
├─ Block data transmission (safety first)
├─ Log sync failure
├─ Retry key sync every 5 seconds
└─ Alert user if still failing after 60 seconds
```

## Database Layer Integration

All databases use **SQLCipher** with current AES-256 key:

```
C++ Core writes to:
├─ secure_logs.db (action_logs table)
├─ vpn_logs.db
└─ firewall_rules.db

Python AI writes to:
├─ known_threats.db
├─ discovered_threats.db (threat DNA)
├─ deception_intel.db (fake network data)
├─ honeypot_intel.db
└─ mesh_defense.db

Both coordinated through SQLCipher PRAGMA key:
PRAGMA key = 'current_aes_256_key_base64';
```

## Component Health Monitoring

Electron continuously monitors component health:

```javascript
// Every 2 seconds
{
  core: {
    status: 'RUNNING' | 'OFFLINE' | 'CRASHED',
    lastDataReceived: timestamp,
    connectionRetries: number
  },
  python: {
    status: 'RUNNING' | 'OFFLINE' | 'CRASHED',
    lastDataReceived: timestamp,
    connectionRetries: number
  },
  database: { status: 'OPERATIONAL' },
  webSockets: {
    core: 'OPEN' | 'CLOSED',
    python: 'OPEN' | 'CLOSED'
  }
}
```

## Message Queue Management

When components disconnect, messages are queued:

```
Outgoing message received
│
├─ Is target connected?
│  ├─ YES → Send immediately
│  └─ NO → Queue with timestamp
│
When target reconnects:
├─ Check queued messages
├─ Send in FIFO order
├─ Validate delivery
└─ Remove from queue
```

## Security Considerations

### Encryption Key Management
- **Generated**: On first app launch
- **Storage**: Windows DPAPI (encrypted at OS level)
- **In Memory**: Kept in Electron process only
- **Rotation**: Every 48-72 hours (randomized)
- **Destruction**: SecureZeroMemory() after rotation

### Communication Integrity
- **All data**: Encrypted with AES-256
- **Verification**: HMAC-SHA256 on every message
- **Integrity**: WebSocket + TLS (localhost only)
- **Certificates**: Self-signed for local communication

### Process Isolation
- **C++ Core**: Runs as separate process, monitor-only privileges needed
- **Python AI**: Runs as separate process, read-only to monitored data
- **Electron**: Runs as main orchestrator with elevated privileges (for firewall/VPN)

## Troubleshooting

### Dashboard shows Risk Score = 0

**Possible cause**: C++ Core or Python AI not connected

**Check**:
1. Open system tray menu → Check component status
2. Click "Open SmartAI" → Look for error messages
3. Check logs: `%APPDATA%\SmartAI\logs\`

### "Core Engine disconnected" Alert

**Recovery**:
1. Wait 10 seconds (auto-restart in progress)
2. If still showing, restart SmartAI application
3. Check `build\Release\core_engine.exe` exists

### "AI Analysis offline" Alert

**Recovery**:
1. Wait 10 seconds (auto-restart in progress)
2. If still showing, check Python installation: `python --version`
3. Reinstall Python dependencies: `pip install -r requirements.txt`

### No data in Attack Story

**Cause**: No threats detected yet (normal if risk score < 50)

**Verify**: 
1. Open "Threat DNA" panel
2. Check "Threat Family" shows detected malware
3. Wait for next auto-analysis cycle (5 seconds)

## Performance Tuning

### Reduce CPU Usage
1. Increase system data collection interval (default 5s)
2. Reduce process monitoring depth
3. Disable deception network mapping if not needed

### Reduce Memory Usage
1. Limit behavior baseline history (default 1000 samples)
2. Reduce honeypot file monitoring scope
3. Disable mesh defense if single-device setup

### Increase Detection Speed
1. Reduce WebSocket message compression
2. Increase AI analysis frequency
3. Enable GPU acceleration for Isolation Forest (if available)

