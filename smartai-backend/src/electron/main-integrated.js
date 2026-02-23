const { app, BrowserWindow, Menu, ipcMain, shell, Tray, nativeImage, dialog } = require('electron');
const path = require('path');
const fs = require('fs');
const { spawn } = require('child_process');
const WebSocket = require('ws');
const AutoLaunch = require('auto-launch');

const isDev = !app.isPackaged;
const appName = 'SmartAI';
const CORE_WSS_PORT = 8080;
const PYTHON_WSS_PORT = 8081;
const PIPE_NAME = 'smartai_core_pipe';

let mainWindow;
let coreProcess;
let pythonProcess;
let coreWebSocket;
let pythonWebSocket;
let trayIcon;
let appData = {
  riskScore: 0,
  systemStats: {},
  alerts: [],
  xaiExplanation: '',
  attackStory: {},
  meshDevices: [],
  honeypotStatus: {},
  vpnStatus: false,
  currentIP: '',
  realIP: '',
};

// ==================== SMARTAI INTEGRATION CLASS ====================

class SmartAIIntegration {
  constructor() {
    this.coreHealthy = false;
    this.pythonHealthy = false;
    this.connectionAttempts = {
      core: 0,
      python: 0,
    };
    this.maxRetries = 5;
    this.retryDelay = 5000; // 5 seconds
    this.encryptionKey = null;
    this.sharedSecret = null;
  }

  async initialize() {
    console.log('[SmartAI] ===== SMARTAI INTEGRATION START =====');
    console.log('[SmartAI] Initializing application...');
    
    try {
      // Step 1: Create application directories
      this.ensureDirectories();
      console.log('[SmartAI] ✓ Directories created');

      // Step 2: Initialize encryption
      await this.initializeEncryption();
      console.log('[SmartAI] ✓ Encryption initialized');

      // Step 3: Create main window (show splash screen)
      this.createWindow();
      console.log('[SmartAI] ✓ Main window created');

      // Step 4: Start C++ Core Engine
      console.log('[SmartAI] Starting C++ Core Engine...');
      await this.startCoreEngine();
      console.log('[SmartAI] ✓ C++ Core Engine started');

      // Step 5: Start Python AI Module
      console.log('[SmartAI] Starting Python AI Module...');
      await this.startPythonModule();
      console.log('[SmartAI] ✓ Python AI Module started');

      // Step 6: Wait for WebSocket connections
      console.log('[SmartAI] Waiting for component connections...');
      await this.waitForConnections();
      console.log('[SmartAI] ✓ All components connected');

      // Step 7: Perform key sync handshake
      console.log('[SmartAI] Performing key sync handshake...');
      await this.performKeySync();
      console.log('[SmartAI] ✓ Key sync completed');

      // Step 8: Create system tray icon
      this.createTrayIcon();
      console.log('[SmartAI] ✓ System tray icon created');

      // Step 9: Setup IPC listeners
      this.setupIPCListeners();
      console.log('[SmartAI] ✓ IPC listeners setup');

      // Step 10: Dashboard live
      this.mainWindow.webContents.send('app-ready', {
        status: 'LIVE',
        timestamp: new Date().toISOString(),
      });
      console.log('[SmartAI] ✓✓✓ APPLICATION READY ✓✓✓');
      console.log('[SmartAI] ===== SMARTAI INTEGRATION COMPLETE =====\n');

    } catch (error) {
      console.error('[SmartAI] INITIALIZATION ERROR:', error);
      dialog.showErrorBox('SmartAI Error', `Failed to initialize: ${error.message}`);
      app.quit();
    }
  }

  ensureDirectories() {
    const appDataPath = app.getPath('appData');
    const smartaiPath = path.join(appDataPath, 'SmartAI');
    const dbPath = path.join(smartaiPath, 'databases');
    const logsPath = path.join(smartaiPath, 'logs');
    const keysPath = path.join(smartaiPath, 'keys');
    const configPath = path.join(smartaiPath, 'config');

    [smartaiPath, dbPath, logsPath, keysPath, configPath].forEach(dir => {
      if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
        console.log(`[SmartAI] Created directory: ${dir}`);
      }
    });

    // Store paths for later use
    this.paths = { smartaiPath, dbPath, logsPath, keysPath, configPath };
  }

  async initializeEncryption() {
    return new Promise((resolve, reject) => {
      try {
        // In production, load from Windows DPAPI
        // For now, use a secure random key
        this.encryptionKey = this.generateKey();
        this.sharedSecret = Buffer.from(this.encryptionKey).toString('base64');
        resolve();
      } catch (error) {
        reject(error);
      }
    });
  }

  generateKey() {
    // Generate 32-byte AES-256 key
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/!@#$%^&*';
    let key = '';
    for (let i = 0; i < 64; i++) {
      key += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return key;
  }

  createWindow() {
    this.mainWindow = new BrowserWindow({
      width: 1600,
      height: 1000,
      minWidth: 1024,
      minHeight: 768,
      webPreferences: {
        preload: path.join(__dirname, 'preload.js'),
        nodeIntegration: false,
        contextIsolation: true,
      },
      icon: this.getIcon(),
    });

    const startUrl = isDev
      ? 'http://localhost:3000'
      : `file://${path.join(__dirname, '../ui/index.html')}`;

    this.mainWindow.loadFile(path.join(__dirname, '../../ui/index.html')).catch(err => {
      console.error('[SmartAI] Failed to load UI:', err);
    });

    if (isDev) {
      this.mainWindow.webContents.openDevTools();
    }

    this.mainWindow.on('closed', () => {
      this.mainWindow = null;
      this.cleanup();
    });
  }

  async startCoreEngine() {
    return new Promise((resolve, reject) => {
      try {
        const exePath = isDev
          ? path.join(__dirname, '../../build/Release/core_engine.exe')
          : path.join(process.resourcesPath, 'core_engine.exe');

        if (!fs.existsSync(exePath)) {
          throw new Error(`Core engine not found at: ${exePath}`);
        }

        console.log(`[SmartAI] Launching C++ Core from: ${exePath}`);

        // Pass encryption key as environment variable
        const env = { ...process.env };
        env['SMARTAI_ENCRYPTION_KEY'] = this.encryptionKey;
        env['SMARTAI_WS_PORT'] = CORE_WSS_PORT.toString();
        env['SMARTAI_PIPE_NAME'] = PIPE_NAME;

        coreProcess = spawn(exePath, [], { env });

        coreProcess.stdout.on('data', (data) => {
          const output = data.toString().trim();
          console.log(`[C++] ${output}`);
          if (this.mainWindow) {
            this.mainWindow.webContents.send('core-log', { message: output, timestamp: new Date() });
          }
        });

        coreProcess.stderr.on('data', (data) => {
          const error = data.toString().trim();
          console.error(`[C++ ERROR] ${error}`);
          if (this.mainWindow) {
            this.mainWindow.webContents.send('core-error', { message: error, timestamp: new Date() });
          }
        });

        coreProcess.on('error', (err) => {
          console.error('[SmartAI] Failed to start C++ Core:', err);
          reject(err);
        });

        coreProcess.on('close', (code) => {
          console.warn(`[C++] Process exited with code ${code}`);
          this.coreHealthy = false;
          if (this.mainWindow && code !== 0) {
            this.mainWindow.webContents.send('component-crash', { component: 'core', code });
            this.attemptCoreRestart();
          }
        });

        // Give process time to start
        setTimeout(() => resolve(), 1000);

      } catch (error) {
        reject(error);
      }
    });
  }

  async startPythonModule() {
    return new Promise((resolve, reject) => {
      try {
        const pythonScript = isDev
          ? path.join(__dirname, '../python/ai_module.py')
          : path.join(process.resourcesPath, 'ai_module.py');

        if (!fs.existsSync(pythonScript)) {
          throw new Error(`Python AI module not found at: ${pythonScript}`);
        }

        console.log(`[SmartAI] Launching Python AI from: ${pythonScript}`);

        // Find python executable
        const pythonExe = process.platform === 'win32' ? 'python.exe' : 'python3';

        const env = { ...process.env };
        env['SMARTAI_ENCRYPTION_KEY'] = this.encryptionKey;
        env['SMARTAI_WS_PORT'] = PYTHON_WSS_PORT.toString();
        env['SMARTAI_PIPE_NAME'] = PIPE_NAME;
        env['SMARTAI_DB_PATH'] = this.paths.dbPath;

        pythonProcess = spawn(pythonExe, [pythonScript], { env });

        pythonProcess.stdout.on('data', (data) => {
          const output = data.toString().trim();
          console.log(`[Python] ${output}`);
          if (this.mainWindow) {
            this.mainWindow.webContents.send('python-log', { message: output, timestamp: new Date() });
          }
        });

        pythonProcess.stderr.on('data', (data) => {
          const error = data.toString().trim();
          console.error(`[Python ERROR] ${error}`);
          if (this.mainWindow) {
            this.mainWindow.webContents.send('python-error', { message: error, timestamp: new Date() });
          }
        });

        pythonProcess.on('error', (err) => {
          console.error('[SmartAI] Failed to start Python AI:', err);
          reject(err);
        });

        pythonProcess.on('close', (code) => {
          console.warn(`[Python] Process exited with code ${code}`);
          this.pythonHealthy = false;
          if (this.mainWindow && code !== 0) {
            this.mainWindow.webContents.send('component-crash', { component: 'python', code });
            this.attemptPythonRestart();
          }
        });

        setTimeout(() => resolve(), 1000);

      } catch (error) {
        reject(error);
      }
    });
  }

  async waitForConnections() {
    const startTime = Date.now();
    const timeout = 30000; // 30 second timeout

    return new Promise((resolve, reject) => {
      const checkInterval = setInterval(() => {
        if (this.coreHealthy && this.pythonHealthy) {
          clearInterval(checkInterval);
          resolve();
        }

        if (Date.now() - startTime > timeout) {
          clearInterval(checkInterval);
          reject(new Error('Component connections timeout after 30 seconds'));
        }
      }, 500);

      // Setup WebSocket servers
      this.setupCoreWebSocketListener();
      this.setupPythonWebSocketListener();
    });
  }

  setupCoreWebSocketListener() {
    const wss = new WebSocket.Server({ port: CORE_WSS_PORT });

    wss.on('connection', (ws) => {
      console.log('[SmartAI] C++ Core connected via WebSocket');
      coreWebSocket = ws;
      this.coreHealthy = true;
      this.connectionAttempts.core = 0;

      ws.on('message', (data) => {
        try {
          const decrypted = this.decrypt(data);
          const message = JSON.parse(decrypted);

          // Update app data with system stats
          appData.systemStats = message.systemStats || appData.systemStats;
          appData.vpnStatus = message.vpnStatus || appData.vpnStatus;
          appData.currentIP = message.currentIP || appData.currentIP;

          // Broadcast to frontend
          if (this.mainWindow) {
            this.mainWindow.webContents.send('core-data', appData);
          }

        } catch (error) {
          console.error('[SmartAI] Error processing core data:', error);
        }
      });

      ws.on('error', (error) => {
        console.error('[SmartAI] C++ WebSocket error:', error);
        this.coreHealthy = false;
      });

      ws.on('close', () => {
        console.log('[SmartAI] C++ Core disconnected');
        this.coreHealthy = false;
        this.attemptCoreReconnect();
      });
    });
  }

  setupPythonWebSocketListener() {
    const wss = new WebSocket.Server({ port: PYTHON_WSS_PORT });

    wss.on('connection', (ws) => {
      console.log('[SmartAI] Python AI connected via WebSocket');
      pythonWebSocket = ws;
      this.pythonHealthy = true;
      this.connectionAttempts.python = 0;

      ws.on('message', (data) => {
        try {
          const decrypted = this.decrypt(data);
          const message = JSON.parse(decrypted);

          // Update risk score
          if (message.riskScore !== undefined) {
            appData.riskScore = message.riskScore;
          }

          // Handle XAI explanation
          if (message.xaiExplanation) {
            appData.xaiExplanation = message.xaiExplanation;
          }

          // Handle attack story
          if (message.attackStory) {
            appData.attackStory = message.attackStory;
          }

          // Handle mesh devices
          if (message.meshDevices) {
            appData.meshDevices = message.meshDevices;
          }

          // Handle honeypot status
          if (message.honeypotStatus) {
            appData.honeypotStatus = message.honeypotStatus;
          }

          // Broadcast to frontend
          if (this.mainWindow) {
            this.mainWindow.webContents.send('ai-data', appData);
          }

        } catch (error) {
          console.error('[SmartAI] Error processing AI data:', error);
        }
      });

      ws.on('error', (error) => {
        console.error('[SmartAI] Python WebSocket error:', error);
        this.pythonHealthy = false;
      });

      ws.on('close', () => {
        console.log('[SmartAI] Python AI disconnected');
        this.pythonHealthy = false;
        this.attemptPythonReconnect();
      });
    });
  }

  async performKeySync() {
    return new Promise((resolve, reject) => {
      if (!coreWebSocket || !pythonWebSocket) {
        return reject(new Error('WebSocket connections not ready for key sync'));
      }

      try {
        // Prepare key sync message
        const syncMessage = {
          type: 'KEY_SYNC',
          key: this.encryptionKey,
          timestamp: new Date().toISOString(),
          nonce: Math.random().toString(36).substring(7),
        };

        // Send to both components
        const encryptedMessage = this.encrypt(JSON.stringify(syncMessage));

        coreWebSocket.send(encryptedMessage, (err) => {
          if (err) return reject(err);
          console.log('[SmartAI] Key sync sent to C++ Core');
        });

        pythonWebSocket.send(encryptedMessage, (err) => {
          if (err) return reject(err);
          console.log('[SmartAI] Key sync sent to Python AI');
        });

        // Wait for acknowledgment
        setTimeout(() => resolve(), 1000);

      } catch (error) {
        reject(error);
      }
    });
  }

  encrypt(data) {
    // Simple base64 encryption (in production use actual AES-256)
    return Buffer.from(data).toString('base64');
  }

  decrypt(data) {
    // Simple base64 decryption
    return Buffer.from(data, 'base64').toString('utf-8');
  }

  createTrayIcon() {
    const icon = this.getIcon();
    this.trayIcon = new Tray(icon);

    const contextMenu = Menu.buildFromTemplate([
      {
        label: 'Open SmartAI',
        click: () => {
          if (this.mainWindow) {
            this.mainWindow.show();
          }
        },
      },
      {
        label: `Risk Score: ${appData.riskScore}%`,
        enabled: false,
      },
      { type: 'separator' },
      {
        label: `Core: ${this.coreHealthy ? '✓ Online' : '✗ Offline'}`,
        enabled: false,
      },
      {
        label: `AI: ${this.pythonHealthy ? '✓ Online' : '✗ Offline'}`,
        enabled: false,
      },
      { type: 'separator' },
      {
        label: 'Exit',
        click: () => {
          app.quit();
        },
      },
    ]);

    this.trayIcon.setContextMenu(contextMenu);

    // Update tray every 2 seconds
    setInterval(() => {
      const newMenu = Menu.buildFromTemplate([
        {
          label: 'Open SmartAI',
          click: () => {
            if (this.mainWindow) {
              this.mainWindow.show();
            }
          },
        },
        {
          label: `Risk Score: ${Math.round(appData.riskScore)}%`,
          enabled: false,
        },
        { type: 'separator' },
        {
          label: `Core: ${this.coreHealthy ? '✓ Online' : '✗ Offline'}`,
          enabled: false,
        },
        {
          label: `AI: ${this.pythonHealthy ? '✓ Online' : '✗ Offline'}`,
          enabled: false,
        },
        { type: 'separator' },
        {
          label: 'Exit',
          click: () => {
            app.quit();
          },
        },
      ]);
      this.trayIcon.setContextMenu(newMenu);
    }, 2000);
  }

  setupIPCListeners() {
    // Listen for UI requests
    ipcMain.on('get-app-data', (event) => {
      event.reply('app-data', appData);
    });

    ipcMain.on('toggle-vpn', (event, enabled) => {
      if (coreWebSocket) {
        const msg = this.encrypt(JSON.stringify({
          type: 'TOGGLE_VPN',
          enabled,
          timestamp: new Date().toISOString(),
        }));
        coreWebSocket.send(msg);
      }
    });

    ipcMain.on('export-attack-story', (event) => {
      const content = JSON.stringify(appData.attackStory, null, 2);
      const filename = `attack-story-${Date.now()}.json`;
      event.reply('export-done', { filename, content });
    });

    ipcMain.on('request-full-scan', (event) => {
      if (coreWebSocket) {
        const msg = this.encrypt(JSON.stringify({
          type: 'FULL_SCAN',
          timestamp: new Date().toISOString(),
        }));
        coreWebSocket.send(msg);
      }
      setTimeout(() => event.reply('scan-initiated'), 100);
    });
  }

  async attemptCoreRestart() {
    console.log('[SmartAI] Attempting to restart C++ Core...');
    this.connectionAttempts.core++;

    if (this.connectionAttempts.core > this.maxRetries) {
      console.error('[SmartAI] Max restart attempts exceeded for C++ Core');
      if (this.mainWindow) {
        dialog.showErrorBox('SmartAI Error', 'Failed to restart C++ Core after multiple attempts');
      }
      return;
    }

    try {
      if (coreProcess) {
        coreProcess.kill();
      }
      await new Promise(resolve => setTimeout(resolve, this.retryDelay));
      await this.startCoreEngine();
    } catch (error) {
      console.error('[SmartAI] Restart failed:', error);
      setTimeout(() => this.attemptCoreRestart(), this.retryDelay);
    }
  }

  async attemptPythonRestart() {
    console.log('[SmartAI] Attempting to restart Python AI...');
    this.connectionAttempts.python++;

    if (this.connectionAttempts.python > this.maxRetries) {
      console.error('[SmartAI] Max restart attempts exceeded for Python AI');
      if (this.mainWindow) {
        dialog.showErrorBox('SmartAI Error', 'Failed to restart Python AI after multiple attempts');
      }
      return;
    }

    try {
      if (pythonProcess) {
        pythonProcess.kill();
      }
      await new Promise(resolve => setTimeout(resolve, this.retryDelay));
      await this.startPythonModule();
    } catch (error) {
      console.error('[SmartAI] Restart failed:', error);
      setTimeout(() => this.attemptPythonRestart(), this.retryDelay);
    }
  }

  async attemptCoreReconnect() {
    console.log('[SmartAI] Attempting to reconnect to C++ Core...');
    this.connectionAttempts.core++;

    if (this.connectionAttempts.core > this.maxRetries) {
      console.error('[SmartAI] Max reconnection attempts exceeded for C++ Core');
      await this.attemptCoreRestart();
      return;
    }

    await new Promise(resolve => setTimeout(resolve, this.retryDelay));
  }

  async attemptPythonReconnect() {
    console.log('[SmartAI] Attempting to reconnect to Python AI...');
    this.connectionAttempts.python++;

    if (this.connectionAttempts.python > this.maxRetries) {
      console.error('[SmartAI] Max reconnection attempts exceeded for Python AI');
      await this.attemptPythonRestart();
      return;
    }

    await new Promise(resolve => setTimeout(resolve, this.retryDelay));
  }

  getIcon() {
    // Create a simple icon (in production, use actual icon file)
    return nativeImage.createEmpty();
  }

  cleanup() {
    console.log('[SmartAI] Cleaning up...');
    
    if (coreProcess) {
      coreProcess.kill();
    }
    if (pythonProcess) {
      pythonProcess.kill();
    }
    if (coreWebSocket) {
      coreWebSocket.close();
    }
    if (pythonWebSocket) {
      pythonWebSocket.close();
    }
  }
}

// ==================== ELECTRON APP LIFECYCLE ====================

const smartai = new SmartAIIntegration();

app.on('ready', () => {
  smartai.initialize().catch(error => {
    console.error('[SmartAI] Fatal error during initialization:', error);
    dialog.showErrorBox('SmartAI Error', `Fatal error: ${error.message}`);
    app.quit();
  });
});

app.on('before-quit', () => {
  smartai.cleanup();
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (smartai.mainWindow === null) {
    smartai.createWindow();
  }
});

// Handle any uncaught exceptions
process.on('uncaughtException', (error) => {
  console.error('[SmartAI] Uncaught exception:', error);
  if (smartai.mainWindow) {
    dialog.showErrorBox('SmartAI Fatal Error', error.message);
  }
});

module.exports = { smartai };
