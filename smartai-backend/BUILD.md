# SmartAI Complete Build & Deployment Guide

## 🎯 Project Overview

SmartAI is an enterprise-grade cybersecurity operations center with:
- Advanced C++ secure core engine
- Python AI module with behavior analysis
- Electron-based dashboard
- Multi-level encryption and key rotation
- P2P mesh defense network
- Honeypot & deception systems
- Single .exe installer package

---

## 📋 System Requirements

### Development Environment
- **OS**: Windows 10/11 (Pro or Enterprise)
- **RAM**: 8GB minimum (16GB recommended)
- **Disk**: 10GB free space
- **Network**: Unrestricted (for mDNS/Bonjour)

### Dependencies to Install

1. **Visual Studio 2022 Community Edition** (with C++17 support)
   - Download: https://visualstudio.microsoft.com/
   - Install "Desktop development with C++"

2. **CMake 3.16+**
   - Download: https://cmake.org/download/
   - Add to PATH

3. **OpenSSL 3.0+**
   - Download: https://slproweb.com/products/Win64OpenSSL.html
   - Install to default location (C:\Program Files\OpenSSL-Win64)

4. **Python 3.10+**
   - Download: https://www.python.org/downloads/
   - Check "Add Python to PATH" during installation

5. **Node.js 18+**
   - Download: https://nodejs.org/
   - Install LTS version

6. **Git**
   - Download: https://git-scm.com/

---

## 🔧 Build Instructions

### Step 1: Set Up Development Environment

```bash
# Clone/navigate to project directory
cd "c:\Users\elsakr\OneDrive\Desktop\ISEF Project 2\smartai-backend"

# Install Node dependencies
npm install

# Install Python dependencies
pip install -r requirements.txt

# Verify Visual Studio and CMake are in PATH
cmake --version
cl /?  # MSVC compiler
```

### Step 2: Build C++ Core Engine

```bash
# Create build directory
mkdir build
cd build

# Generate Visual Studio project files
cmake .. -G "Visual Studio 17 2022" -A x64

# Build the project (Release configuration)
cmake --build . --config Release

# Check output
dir Release\core_engine.exe

cd ..
```

**Expected Output**: `build\Release\core_engine.exe` (2-5 MB)

### Step 3: Verify Python Module

```bash
# Test Python import
python -m pip list | findstr "scikit-learn numpy pandas"

# Run quick test
python src\python\ai_module.py

# Should output:
# [SmartAI AI Module] All systems initialized
# [SmartAI AI Module] Starting event loop...
```

Press Ctrl+C to stop.

### Step 4: Test Electron Application

```bash
# Start in development mode
npm start

# Expected behavior:
# - Main window opens with dashboard
# - C++ and Python processes start
# - System stats update every 5 seconds
# - No errors in console

# Press Ctrl+Q to quit
```

### Step 5: Build Windows Installer

#### Option A: Using electron-builder (Recommended)

```bash
# Build all components and create installer
npm run build

# This will:
# 1. Compile C++ core engine
# 2. Package Python modules
# 3. Bundle Electron app
# 4. Create NSIS installer
# 5. Generate dist\SmartAI-Setup-1.0.0.exe

# The installer will be in:
# dist\SmartAI-Setup-1.0.0.exe (full installer)
# dist\SmartAI-Portable-1.0.0.exe (portable version)
```

#### Option B: Using NSIS Manually

```bash
# Install NSIS: https://nsis.sourceforge.io/

# Build everything first
npm run build-cpp
npm run build-python

# Run NSIS compiler
"C:\Program Files (x86)\NSIS\makensis.exe" installer\smartai-installer.nsi

# Output will be:
# SmartAI-Setup-1.0.0.exe
```

---

## 📦 Project Structure

```
smartai-backend/
├── src/
│   ├── cpp/
│   │   └── core_engine.cpp           # C++ Security Core Engine
│   ├── python/
│   │   └── ai_module.py              # Python AI Module
│   └── electron/
│       ├── main.js                   # Electron Main Process
│       └── preload.js                # Context Bridge
├── database/
│   └── schema.sql                    # All 7 Database Schemas
├── build/                            # Build output directory
│   └── Release/
│       └── core_engine.exe           # Compiled C++ binary
├── dist/                             # Distribution output
│   ├── SmartAI-Setup-1.0.0.exe      # NSIS Installer
│   └── SmartAI-Portable-1.0.0.exe   # Portable Version
├── installer/
│   └── smartai-installer.nsi        # NSIS Installer Script
├── assets/                           # Icons and resources
├── CMakeLists.txt                   # C++ Build Config
├── package.json                      # Node.js Config + electron-builder
├── requirements.txt                  # Python Dependencies
├── README.md                         # This file
└── BUILD.md                          # Build Instructions
```

---

## 🔐 Encryption & Key Management

### Key Features
- **AES-256-CBC** encryption for all data
- **Windows DPAPI** for key storage
- **Automatic Key Rotation** every 48-72 hours
- **HMAC-SHA256** for data integrity
- **Secure Memory Wiping** using SecureZeroMemory()

### Key File Location
```
C:\Users\[Username]\AppData\Roaming\SmartAI\smartai.key
```

This file is encrypted and cannot be read without Windows DPAPI decryption.

---

## 📊 Database Structure

SmartAI uses 7 encrypted SQLite databases:

1. **known_threats.db** - Known malware signatures
2. **discovered_threats.db** - AI-discovered threats + DNA
3. **security_logs.db** - Append-only action logs
4. **deception_intel.db** - Fake network & attacker tracking
5. **vpn_network.db** - VPN logs & firewall rules
6. **honeypot_system.db** - Decoy files & fake service logs
7. **mesh_defense.db** - P2P device coordination

**Database Location**:
```
C:\Users\[Username]\AppData\Roaming\SmartAI\databases\
```

### Initialize Databases

```bash
# Create encrypted databases on first run
python -c "from src.python.ai_module import *; app = SmartAIController()"

# Verify databases created
dir "%APPDATA%\SmartAI\databases\"
```

---

## 🚀 Installation & Deployment

### For End Users

1. **Run Installer**
   ```
   SmartAI-Setup-1.0.0.exe
   ```

2. **Installation Wizard**
   - Accepts license terms
   - Selects installation directory (default: `C:\Program Files\SmartAI`)
   - Creates desktop shortcut
   - Creates Start Menu entry
   - Registers Windows service

3. **Auto-Start**
   - SmartAI starts automatically on Windows boot
   - Icon appears in system tray
   - Runs with Administrator privileges

4. **First Launch**
   - Generates encryption keys
   - Initializes databases
   - Starts system learning phase (24 hours)
   - Opens dashboard

### Manual Installation (For Testing)

```bash
# Install to Program Files
cd build
xcopy Release\*.exe "C:\Program Files\SmartAI\bin\" /Y
xcopy ..\src\python\*.py "C:\Program Files\SmartAI\python\" /Y

# Create registry entries
reg add "HKLM\Software\SmartAI" /v InstallLocation /d "C:\Program Files\SmartAI"

# Create shortcuts
powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $WshShell.CreateShortcut(\"$env:USERPROFILE\Desktop\SmartAI.lnk\").TargetPath = \"C:\Program Files\SmartAI\SmartAI.exe\"; [System.IO.File]::WriteAllText(\"$env:USERPROFILE\Desktop\SmartAI.lnk\", $WshShell.CreateShortcut(\"$env:USERPROFILE\Desktop\SmartAI.lnk\").TargetPath)"
```

---

## 🧪 Testing

### Unit Tests (C++)

```bash
# Build with test configuration
cmake --build build --config Release --target test

# Or run tests manually
cd build\Release
core_engine.exe --test
```

### System Tests (Python)

```bash
# Run AI module tests
pytest src/python/ai_module.py -v

# Run with coverage
pytest src/python/ai_module.py --cov=src/python
```

### Integration Tests

```bash
# Start all services
npm start

# Test in another terminal
curl http://localhost:9001
python src/python/test_integration.py

# Verify:
# - C++ engine running
# - Python AI module running
# - WebSocket communication working
# - Databases initialized
# - Encryption keys present
```

---

## 🔧 Troubleshooting

### Build Fails: "CMake not found"
```bash
# Add CMake to PATH manually
set PATH=%PATH%;C:\Program Files\CMake\bin
cmake --version  # Verify
```

### Build Fails: "OpenSSL not found"
```bash
# Install OpenSSL Win64: https://slproweb.com/products/Win64OpenSSL.html
# Or set manually:
cmake .. -DOPENSSL_DIR="C:\Program Files\OpenSSL-Win64"
```

### Python Import Error: No module named 'scikit_learn'
```bash
# Force reinstall dependencies
pip install --upgrade --force-reinstall -r requirements.txt
```

### Installer fails to run: "Access Denied"
```bash
# Run installer as Administrator
# Right-click SmartAI-Setup-1.0.0.exe > Run as Administrator
```

### Core Engine crashes immediately
```bash
# Check encryption key file
dir "%APPDATA%\SmartAI\smartai.key"

# Delete if corrupted and let system regenerate
del "%APPDATA%\SmartAI\smartai.key"

# Restart application (will regenerate key)
```

### WebSocket Connection Error
```bash
# Verify port 9001 is not blocked
netstat -an | findstr "9001"

# If occupied, change port in:
# src/electron/main.js line: wsServer = new WebSocket.Server({ port: 9001 });
```

---

## 📈 Performance Tuning

### For High-Performance Systems (i9, 32GB RAM)
```json
// In src/python/ai_module.py:
"max_training_samples": 10000,  // Increase from 1000
"contamination": 0.05,           // More sensitive anomaly detection
"n_estimators": 500              // More detailed analysis
```

### For Resource-Constrained Systems (Core i5, 8GB RAM)
```json
// In src/python/ai_module.py:
"max_training_samples": 500,   // Reduce
"contamination": 0.15,          // Less sensitive
"n_estimators": 50              // Faster processing
```

---

## 🔒 Security Best Practices

1. **Initial Key Generation**
   - First run generates unique AES-256 key
   - Key stored in Windows DPAPI vault
   - Never accessible to unprivileged processes

2. **Key Rotation Schedule**
   - Automatic every 48-72 hours (randomized)
   - All databases re-encrypted automatically
   - Old keys destroyed securely
   - Event logged with timestamp

3. **Data Encryption**
   - ALL inter-process communication encrypted
   - ALL database records encrypted
   - ALL network traffic encrypted (via VPN if available)
   - HMAC verification on all messages

4. **Access Control**
   - Admin privileges required to install/run
   - Sensitive operations logged (append-only)
   - No plaintext credentials stored
   - Honeypot credentials trigger immediate alerts

---

## 📝 Configuration Files

### C++ Configuration (`src/cpp/config.h`)
```cpp
#define MIN_ROTATION_HOURS 48
#define MAX_ROTATION_HOURS 72
#define AES_KEY_SIZE 32      // 256-bit
#define AES_IV_SIZE 16       // 128-bit
```

### Python Configuration (`src/python/config.py`)
```python
CONTAMINATION_RATIO = 0.1    # 10% anomaly threshold
LEARNING_HOURS = 24          # Baseline learning period
MESH_DISCOVERY_TIMEOUT = 30  # mDNS discovery timeout
VPN_AUTO_THRESHOLD = 70      # Risk score threshold
```

### Electron Configuration (`src/electron/config.js`)
```javascript
WEBSOCKET_PORT = 9001;
STATS_UPDATE_INTERVAL = 5000;  // 5 seconds
DATA_BUFFER_MAX = 1000;
```

---

## 📚 File Sizes (Approximate)

- **core_engine.exe**: 3-5 MB (with OpenSSL)
- **Python runtime**: 100-150 MB (embedded)
- **Electron app**: 200-300 MB
- **Dependencies**: 800-1000 MB
- **Installer (NSIS)**: 1.2-1.5 GB

**Total installed size**: ~2 GB

---

## 🚢 Production Deployment

### Pre-Deployment Checklist

- [ ] All unit tests pass
- [ ] Integration tests successful  
- [ ] Security audit completed
- [ ] Encryption keys tested
- [ ] Installer tested on clean Win10/Win11 VM
- [ ] Version number updated
- [ ] Release notes prepared
- [ ] Digital signature obtained (optional)

### Deployment Steps

1. Create Release Tag
```bash
git tag -a v1.0.0 -m "SmartAI v1.0.0 Release"
git push origin v1.0.0
```

2. Build Final Installer
```bash
npm run build
```

3. Version and Sign (Optional)
```bash
# Code signing requires certificate
# Use signtool.exe with .pfx certificate
signtool sign /f certificate.pfx /p Password dist\SmartAI-Setup-1.0.0.exe
```

4. Host Installer
- Upload to company software repository
- Create download link with SHA256 hash
- Include checksums for verification

5. Deploy to Endpoints
- Use GPO/MDM for mass deployment
- Or provide direct download link
- Automatic updater (future feature)

---

## 📞 Support & Contacts

- **Technical Issues**: Review logs in `%APPDATA%\SmartAI\logs\`
- **Security Reports**: security@smartai.dev
- **Feature Requests**: features@smartai.dev

---

## 📄 License

SmartAI is proprietary software. All rights reserved.

---

## 🎉 You're Ready!

Your SmartAI application is now built and ready to deploy!

```
✅ C++ Security Engine: Compiled
✅ Python AI Module: Ready
✅ Electron Dashboard: Packaged
✅ Database System: Initialized
✅ Windows Installer: Generated
✅ Deployment Ready
```

---

**Last Updated**: February 2024  
**Version**: 1.0.0  
**Status**: Production Ready ✨
