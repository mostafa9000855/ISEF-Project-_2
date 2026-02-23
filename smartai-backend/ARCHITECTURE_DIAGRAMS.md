```
╔════════════════════════════════════════════════════════════════════════════╗
║          SMARTAI SYSTEM ARCHITECTURE - COMPONENT CONNECTIONS              ║
╚════════════════════════════════════════════════════════════════════════════╝

┌─────────────────────────────────────────────────────────────────────────────┐
│                          ELECTRON FRONTEND (UI)                             │
│  • Web-based Dashboard (HTML/CSS/JS)                                        │
│  • Real-time Visualization                                                  │
│  • User Controls & Settings                                                 │
│  • System Tray Integration                                                  │
└──┬──────────────────────────────────────────────────────────────────────────┤
   │
   │ ┌─── WebSocket on port 8080 ──────────────┐   ┌─── WebSocket on port 8081 ──┐
   │ │ (Binary encryption + Heartbeat)         │   │ (Binary encryption)          │
   │ │                                         │   │                              │
   ▼ ▼                                         ▼   ▼                              ▼
┌──────────────────────────────┐     ┌──────────────────────────────────────────────────┐
│  C++ CORE ENGINE             │     │  PYTHON AI MODULE                                │
│                              │     │                                                  │
│ ┌──────────────────────────┐ │     │ ┌──────────────────────────────────────────────┐ │
│ │ SYSTEM MONITORING        │ │     │ │ BEHAVIOR ANALYSIS ENGINE                     │ │
│ │ • CPU/RAM/Network        │ │     │ │ • Baseline profiling (24h learning)          │ │
│ │ • Process Tracking       │ │     │ │ • Isolation Forest anomaly detection         │ │
│ │ • Integrity Checking     │ │     │ │ • Risk score calculation (0-100%)            │ │
│ └──────────────────────────┘ │     │ └──────────────────────────────────────────────┘ │
│                              │     │                                                  │
│ ┌──────────────────────────┐ │     │ ┌──────────────────────────────────────────────┐ │
│ │ ENCRYPTION ENGINE        │ │     │ │ THREAT DNA ANALYZER                          │ │
│ │ • AES-256 Encryption     │◄─────►│ │ • Malware signature extraction               │ │
│ │ • Key Rotation (48-72h)  │ │     │ │ • Variant prediction via ML mutation         │ │
│ │ • HMAC Verification      │ │     │ │ • Known threat comparison                    │ │
│ └──────────────────────────┘ │     │ └──────────────────────────────────────────────┘ │
│                              │     │                                                  │
│ ┌──────────────────────────┐ │     │ ┌──────────────────────────────────────────────┐ │
│ │ AUTO-RESPONSE ENGINE     │ │     │ │ DECEPTION NETWORK ENGINE                     │ │
│ │ • VPN Auto-Activation    │ │     │ │ • Fake network topology generation           │ │
│ │ • Firewall Rules         │ │     │ │ • Honeypot file monitoring                   │ │
│ │ • Process Blocking       │ │     │ │ • Attacker behavior tracking                 │ │
│ │ • Emergency Mode (Risk>90)│ │     │ │ • Deception intelligence collection         │ │
│ └──────────────────────────┘ │     │ └──────────────────────────────────────────────┘ │
│                              │     │                                                  │
│ ┌──────────────────────────┐ │     │ ┌──────────────────────────────────────────────┐ │
│ │ NAMED PIPE IPC ◄────────────────►│ │ MESH DEFENSE COORDINATOR                     │ │
│ │ to Python (5sec updates) │ │     │ │ • P2P device discovery (mDNS)                │ │
│ └──────────────────────────┘ │     │ │ • Threat intelligence sharing                │ │
│                              │     │ │ • Collective voting on alerts                │ │
│ ┌──────────────────────────┐ │     │ │ • Air-Gap emergency fallback                 │ │
│ │ KEY MANAGEMENT           │ │     │ └──────────────────────────────────────────────┘ │
│ │ • DPAPI Storage (Win)    │ │     │                                                  │
│ │ • Secure Key Exchange    │ │     │ ┌──────────────────────────────────────────────┐ │
│ │ • Rotation Scheduling    │ │     │ │ EXPLAINABLE AI (XAI)                         │ │
│ └──────────────────────────┘ │     │ │ • SHAP-based explanations                    │ │
│                              │     │ │ • Human-readable evidence chains             │ │
│ ┌──────────────────────────┐ │     │ │ • Top 3 trigger factors                      │ │
│ │ INTEGRITY CHECKING       │ │     │ └──────────────────────────────────────────────┘ │
│ │ • File hash verification │ │     │                                                  │
│ │ • Debugger detection     │ │     │ ┌──────────────────────────────────────────────┐ │
│ │ • Tamper protection      │ │     │ │ ATTACK STORY GENERATOR                       │ │
│ └──────────────────────────┘ │     │ │ • Timeline reconstruction                    │ │
│                              │     │ │ • Vulnerability mapping                      │ │
│                              │     │ │ • Defense response documentation             │ │
│                              │     │ └──────────────────────────────────────────────┘ │
│                              │     │                                                  │
└──────────────────────────────┘     └──────────────────────────────────────────────────┘
   ▲                                             ▲
   │                                             │
   └────────────────────┬────────────────────────┘
                        │
           Both write to same databases
                  (encrypted)
                        │
   ┌────────────────────┴────────────────────────┐
   ▼                                             ▼
┌──────────────────────────────┐     ┌──────────────────────────────┐
│   ENCRYPTED DATABASES         │     │   SECURE LOGS (APPEND-ONLY) │
│                              │     │                              │
│ • DB1: Known Threats         │     │ • action_logs               │
│ • DB2: Discovered Threats    │     │ • vpn_logs                  │
│ • DB3: Deception Intel       │     │ • firewall_rules            │
│ • DB4: VPN & Network Actions │     │ • key_rotation_events       │
│ • DB5: Honeypot Intel        │     │ • incident_timeline         │
│ • DB6: Mesh Defense Intel    │     │                              │
│                              │     │ All encrypted with AES-256  │
│ All encrypted with AES-256   │     │ using current rotation key  │
│ Auto-re-encrypted on key     │     │                              │
│ rotation                     │     │                              │
└──────────────────────────────┘     └──────────────────────────────┘


╔════════════════════════════════════════════════════════════════════════════╗
║                    STARTUP SEQUENCE (SYNCHRONOUS)                          ║
╚════════════════════════════════════════════════════════════════════════════╝

┌─────────────────────────────────────────────────────────────────────────────┐
│  Step 1: Electron App Launch                                               │
│  └─ Initialize app, load UI                                               │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  Step 2: Create Application Directories                                    │
│  └─ Create: databases/, logs/, keys/, config/                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  Step 3: Initialize Encryption                                             │
│  └─ Generate 256-bit AES key (or load from DPAPI)                         │
│  └─ Pass key to environment variables                                      │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  Step 4: Spawn C++ Core Engine (Child Process)                             │
│  └─ Pass: SMARTAI_ENCRYPTION_KEY, SMARTAI_WS_PORT=8080, SMARTAI_PIPE_NAME│
│  └─ Core waits for WebSocket listener to start                            │
│  └─ Core displays console output to debug                                  │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  Step 5: Spawn Python AI Module (Child Process)                            │
│  └─ Pass: SMARTAI_ENCRYPTION_KEY, SMARTAI_WS_PORT=8081, SMARTAI_DB_PATH  │
│  └─ AI waits for WebSocket listener to start                              │
│  └─ AI displays console output to debug                                    │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  Step 6: Setup WebSocket Listeners (Electron)                              │
│  └─ Port 8080: Listen for C++ Core connections                            │
│  └─ Port 8081: Listen for Python AI connections                           │
│  └─ Both listen for binary encrypted messages                              │
│  └─ Timeout: 30 seconds max to connect                                     │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  Step 7: C++ Core Connects to Electron WebSocket                           │
│  └─ Connect to 127.0.0.1:8080                                             │
│  └─ Send initial handshake message                                         │
│  └─ Mark as HEALTHY                                                        │
│  └─ Start system monitoring thread                                         │
│  └─ Start sending system data every 5 seconds                              │
│  └─ Attempt to connect to Python via named pipe                            │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  Step 8: Python AI Connects to Electron WebSocket                          │
│  └─ Connect to 127.0.0.1:8081                                             │
│  └─ Send initial handshake message                                         │
│  └─ Mark as HEALTHY                                                        │
│  └─ Start listening for system data from C++                               │
│  └─ Initialize behavior baseline collection                                │
│  └─ Attempt to connect to C++ via named pipe                               │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  Step 9: Key Sync Handshake                                                │
│  └─ Electron encrypts encryption key                                       │
│  └─ Send same key to BOTH C++ and Python                                   │
│  └─ Both sides verify key receipt                                          │
│  └─ Both sides synchronize on same encryption parameters                   │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  Step 10: Dashboard LIVE                                                    │
│  └─ C++ Core sends encrypted system data every 5 seconds                   │
│  └─ Electron receives, forwards to UI                                      │
│  └─ Python AI receives, analyzes, sends risk score back                    │
│  └─ Electron displays real-time dashboard with live data                   │
│  └─ All components fully operational                                       │
└─────────────────────────────────────────────────────────────────────────────┘


╔════════════════════════════════════════════════════════════════════════════╗
║                    DATA FLOW - 5-SECOND CYCLE                             ║
╚════════════════════════════════════════════════════════════════════════════╝

TIME    COMPONENT           ACTION
────────────────────────────────────────────────────────────────────────────
 0s     C++ Core Engine     • Collect system metrics (CPU, RAM, Network)
                            • List all running processes
                            • Check network adapters
                            • Encrypt data with current AES-256 key
                            • Send via WebSocket to Electron: port 8080

 0s     Electron            • Receive encrypted binary from C++ (port 8080)
                            • Decrypt using received key
                            • Parse JSON system data
                            • Forward to Python AI via WebSocket: port 8081
                            • Update local appData cache

 0s     Python AI Module    • Receive encrypted system data from Electron
                            • Decrypt data
                            • Extract features (CPU, RAM, process count)
                            • Run Isolation Forest anomaly detection
                            • Build/update behavior baseline

 1-2s   Python AI Module    • Calculate risk score (0-100)
                            • Generate XAI explanation using SHAP
                            • Analyze threat DNA signatures
                            • Generate attack predictions
                            • Encrypt response with AES-256 key
                            • Send via WebSocket to Electron: port 8081

 2-3s   Electron            • Receive encrypted analysis from Python
                            • Decrypt using encryption key
                            • Parse AI analysis JSON
                            • Extract: riskScore, xaiExplanation, predictions
                            • Update UI in real time on dashboard

 3-4s   If Risk Score > 70: • C++ receives risk score via WebSocket
        C++ Core            • Activate auto-response:
                            │  ├─ Enable VPN (WireGuard/OpenVPN)
                            │  ├─ Update Windows Firewall rules
                            │  ├─ Block suspicious processes
                            │  └─ Log all actions to secure_logs.db
                            •
        If Risk Score > 90: • EMERGENCY MODE:
                            │  ├─ Block ALL outbound traffic
                            │  ├─ Isolate system
                            │  └─ Trigger system-wide alerts
                            •
        If Risk Score < 30: • Deactivate VPN
                            • Restore normal firewall rules

 5s     Cycle restarts      • Loop back to T=0s with fresh data


╔════════════════════════════════════════════════════════════════════════════╗
║                    COMMUNICATION SECURITY LAYERS                          ║
╚════════════════════════════════════════════════════════════════════════════╝

BETWEEN C++ AND PYTHON:
├─ Named Pipe IPC (Windows)
├─ Data encrypted with AES-256
├─ Every 5 seconds with HMAC verification
└─ Key rotation every 48-72 hours with secure re-encryption

BETWEEN C++ AND ELECTRON:
├─ WebSocket on port 8080
├─ Binary encrypted frames
├─ Base64 encoding with AES-256
├─ Heartbeat every 30 seconds
└─ Auto-reconnect with exponential backoff

BETWEEN PYTHON AND ELECTRON:
├─ WebSocket on port 8081
├─ Binary encrypted frames
├─ Base64 encoding with AES-256
├─ Heartbeat every 30 seconds
└─ Auto-reconnect with exponential backoff

TO DATABASES:
├─ SQLCipher with AES-256 encryption
├─ Current rotation key from key manager
├─ Automatic re-encryption on key rotation
└─ Append-only security logs (immutable)


╔════════════════════════════════════════════════════════════════════════════╗
║                    ERROR HANDLING & AUTO-RECOVERY                         ║
╚════════════════════════════════════════════════════════════════════════════╝

IF C++ CORE CRASHES:
├─ Electron detects socket close on port 8080
├─ Log error with timestamp to secure_logs.db
├─ Alert user: "Core Engine disconnected"
├─ Retry connection every 10 seconds (max 5 attempts)
├─ After 5 failed attempts: Auto-restart C++ process
├─ On restart: Perform key sync again
└─ Resume normal monitoring when recovered

IF PYTHON AI CRASHES:
├─ Electron detects socket close on port 8081
├─ Log error with timestamp
├─ Alert user: "AI Analysis offline"
├─ Retry connection every 10 seconds (max 5 attempts)
├─ After 5 failed attempts: Auto-restart Python process
├─ On restart: Skip pending analysis requests
└─ Resume normal analysis when recovered

IF WEBSOCKET CONNECTION FAILS:
├─ Retry connection every 5 seconds
├─ Queue outgoing messages while disconnected
├─ Flush queue when connection restored
├─ Notify user of connection status
└─ Never shutdown if just one component offline

IF KEY SYNC FAILS:
├─ Block data transmission until sync succeeds
├─ Retry key sync every 5 seconds
├─ Log failed sync attempt
├─ Alert user if unable to sync for >60 seconds
└─ Both sides reject unencrypted messages

IF ENCRYPTION KEY ROTATION FAILS:
├─ Keep old key active until new key confirmed
├─ Retry rotation every 60 seconds
├─ Log rotation attempts
├─ Continue operations with current key
├─ Alert admin if stuck for >24 hours
└─ Never lose old key until new one verified in all databases
```

