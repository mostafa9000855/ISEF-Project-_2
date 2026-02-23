const { app, BrowserWindow, Menu, ipcMain, shell, Tray, nativeImage } = require('electron');
const path = require('path');
const fs = require('fs');
const { spawn } = require('child_process');
const WebSocket = require('ws');

const isDev = !app.isPackaged;
const appName = 'SmartAI';

let mainWindow;
let coreProcess;
let pythonProcess;
let wsServer;
let trayIcon;

class SmartAIApp {
  constructor() {
    this.coreHealthy = false;
    this.pythonHealthy = false;
    this.currentRiskScore = 0;
    this.dataBuffer = [];
  }

  async initialize() {
    console.log('[SmartAI] Initializing application...');
    
    // Create application directories
    this.ensureDirectories();
    
    // Start core processes
    this.startCoreEngine();
    this.startPythonModule();
    this.initializeWebSocketServer();
    
    // Create main window
    this.createWindow();
    
    // Create system tray icon
    this.createTrayIcon();
    
    console.log('[SmartAI] Application ready');
  }

  ensureDirectories() {
    const appDataPath = app.getPath('appData');
    const smartaiPath = path.join(appDataPath, 'SmartAI');
    const dbPath = path.join(smartaiPath, 'databases');
    const logsPath = path.join(smartaiPath, 'logs');

    [smartaiPath, dbPath, logsPath].forEach(dir => {
      if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
      }
    });
  }

  startCoreEngine() {
    console.log('[SmartAI] Starting C++ Core Engine...');
    
    const exePath = isDev
      ? path.join(__dirname, '../build/core_engine.exe')
      : path.join(process.resourcesPath, 'core_engine.exe');

    if (!fs.existsSync(exePath)) {
      console.error('[ERROR] Core engine not found:', exePath);
      return;
    }

    coreProcess = spawn(exePath);

    coreProcess.stdout.on('data', (data) => {
      console.log(`[C++]: ${data}`);
    });

    coreProcess.stderr.on('data', (data) => {
      console.error(`[C++ ERROR]: ${data}`);
    });

    coreProcess.on('close', (code) => {
      console.log(`[C++] Process exited with code ${code}`);
      this.coreHealthy = false;
    });

    this.coreHealthy = true;
  }

  startPythonModule() {
    console.log('[SmartAI] Starting Python AI Module...');
    
    const scriptPath = isDev
      ? path.join(__dirname, '../src/python/ai_module.py')
      : path.join(process.resourcesPath, 'ai_module.py');

    const pythonExecutable = isDev
      ? 'python'
      : path.join(process.resourcesPath, 'python/python.exe');

    if (!fs.existsSync(scriptPath)) {
      console.error('[ERROR] Python module not found:', scriptPath);
      return;
    }

    pythonProcess = spawn(pythonExecutable, [scriptPath], {
      stdio: ['ignore', 'pipe', 'pipe']
    });

    pythonProcess.stdout.on('data', (data) => {
      console.log(`[Python]: ${data}`);
    });

    pythonProcess.stderr.on('data', (data) => {
      console.error(`[Python ERROR]: ${data}`);
    });

    pythonProcess.on('close', (code) => {
      console.log(`[Python] Process exited with code ${code}`);
      this.pythonHealthy = false;
    });

    this.pythonHealthy = true;
  }

  initializeWebSocketServer() {
    console.log('[SmartAI] Initializing WebSocket server...');
    
    wsServer = new WebSocket.Server({ port: 9001 });

    wsServer.on('connection', (ws) => {
      console.log('[WebSocket] Client connected');

      ws.on('message', (message) => {
        try {
          const data = JSON.parse(message);
          this.processDataFromCore(data);
          
          // Broadcast to all clients
          wsServer.clients.forEach(client => {
            if (client.readyState === WebSocket.OPEN) {
              client.send(JSON.stringify(data));
            }
          });
        } catch (e) {
          console.error('Error processing WebSocket message:', e);
        }
      });

      ws.on('close', () => {
        console.log('[WebSocket] Client disconnected');
      });
    });
  }

  processDataFromCore(data) {
    // Update UI with real-time data from C++ engine
    if (data.type === 'system_stats') {
      this.dataBuffer.push({
        timestamp: Date.now(),
        cpu: data.cpu_usage,
        memory: data.memory_usage,
        network_in: data.network_in,
        network_out: data.network_out,
        processes: data.process_count
      });

      // Keep only last 1000 samples
      if (this.dataBuffer.length > 1000) {
        this.dataBuffer.shift();
      }

      // Send to UI
      if (mainWindow && mainWindow.webContents) {
        mainWindow.webContents.send('system-stats', data);
      }
    }
    else if (data.type === 'threat_alert') {
      this.currentRiskScore = data.risk_score || 0;
      
      if (mainWindow && mainWindow.webContents) {
        mainWindow.webContents.send('threat-alert', {
          riskScore: this.currentRiskScore,
          severity: data.severity,
          details: data.details
        });
      }

      // Update tray icon style
      this.updateTrayIcon();
    }
  }

  createWindow() {
    console.log('[SmartAI] Creating main window...');
    
    mainWindow = new BrowserWindow({
      width: 1800,
      height: 1000,
      minWidth: 1200,
      minHeight: 800,
      icon: nativeImage.createFromPath(path.join(__dirname, '../assets/icon.png')),
      webPreferences: {
        preload: path.join(__dirname, 'preload.js'),
        contextIsolation: true,
        enableRemoteModule: false,
        nodeIntegration: false,
        sandbox: true
      }
    });

    const indexPath = isDev
      ? 'http://localhost:3000'
      : `file://${path.join(__dirname, '../dist/index.html')}`;

    mainWindow.loadFile(path.join(__dirname, '../../../index.html'));

    mainWindow.on('closed', () => {
      mainWindow = null;
    });

    // Open DevTools in development
    if (isDev) {
      mainWindow.webContents.openDevTools();
    }
  }

  createTrayIcon() {
    console.log('[SmartAI] Creating system tray icon...');
    
    const trayIconPath = path.join(__dirname, '../assets/tray-icon.png');
    const trayImage = nativeImage.createFromPath(trayIconPath);
    
    trayIcon = new Tray(trayImage);

    const contextMenu = Menu.buildFromTemplate([
      {
        label: `Risk Score: ${this.currentRiskScore.toFixed(1)}%`,
        enabled: false
      },
      { type: 'separator' },
      {
        label: 'Show Dashboard',
        click: () => {
          if (mainWindow) {
            mainWindow.show();
            mainWindow.focus();
          }
        }
      },
      {
        label: 'Core Engine: ' + (this.coreHealthy ? 'Healthy' : 'Error'),
        enabled: false
      },
      {
        label: 'AI Module: ' + (this.pythonHealthy ? 'Healthy' : 'Error'),
        enabled: false
      },
      { type: 'separator' },
      {
        label: 'Exit',
        click: () => {
          app.quit();
        }
      }
    ]);

    trayIcon.setContextMenu(contextMenu);

    trayIcon.on('double-click', () => {
      if (mainWindow) {
        mainWindow.show();
      }
    });
  }

  updateTrayIcon() {
    if (trayIcon) {
      let iconColor = 'green'; // Low risk: green

      if (this.currentRiskScore > 70) {
        iconColor = 'red'; // High risk: red
      } else if (this.currentRiskScore > 40) {
        iconColor = 'orange'; // Medium risk: orange
      }

      const trayLabel = `SmartAI [${this.currentRiskScore.toFixed(0)}%]`;
      trayIcon.setTitle(trayLabel);

      // Update context menu with new risk score
      const contextMenu = Menu.buildFromTemplate([
        {
          label: `Risk Score: ${this.currentRiskScore.toFixed(1)}%`,
          enabled: false
        },
        { type: 'separator' },
        { label: 'Show Dashboard', click: () => mainWindow?.show() },
        {
          label: 'Core Engine: ' + (this.coreHealthy ? 'Healthy' : 'Error'),
          enabled: false
        },
        {
          label: 'AI Module: ' + (this.pythonHealthy ? 'Healthy' : 'Error'),
          enabled: false
        },
        { type: 'separator' },
        { label: 'Exit', click: () => app.quit() }
      ]);

      trayIcon.setContextMenu(contextMenu);
    }
  }
}

// ==================== APP LIFECYCLE ====================

let smartaiApp;

app.on('ready', async () => {
  smartaiApp = new SmartAIApp();
  await smartaiApp.initialize();
});

app.on('window-all-closed', () => {
  // Keep app in tray on Windows
  if (process.platform !== 'darwin') {
    // app.quit();
  }
});

app.on('activate', () => {
  if (mainWindow === null) {
    smartaiApp.createWindow();
  }
});

app.on('quit', () => {
  console.log('[SmartAI] Shutting down...');
  
  if (coreProcess) {
    coreProcess.kill();
  }
  if (pythonProcess) {
    pythonProcess.kill();
  }
});

// ==================== IPC HANDLERS ====================

ipcMain.handle('get-system-stats', () => {
  return smartaiApp?.dataBuffer || [];
});

ipcMain.handle('get-risk-score', () => {
  return smartaiApp?.currentRiskScore || 0;
});

ipcMain.handle('get-core-health', () => {
  return smartaiApp?.coreHealthy || false;
});

ipcMain.handle('get-python-health', () => {
  return smartaiApp?.pythonHealthy || false;
});

ipcMain.handle('activate-vpn', () => {
  // Send command to C++ core engine
  return { success: true, message: 'VPN activation signal sent' };
});

ipcMain.handle('export-report', async (event, reportData) => {
  const reportPath = path.join(app.getPath('documents'), 'SmartAI-Report.json');
  fs.writeFileSync(reportPath, JSON.stringify(reportData, null, 2));
  return { success: true, path: reportPath };
});

ipcMain.handle('open-external-url', (event, url) => {
  shell.openExternal(url);
  return { success: true };
});

// ==================== MENU ====================

const template = [
  {
    label: 'File',
    submenu: [
      { label: 'Exit', accelerator: 'CmdOrCtrl+Q', click: () => app.quit() }
    ]
  },
  {
    label: 'View',
    submenu: [
      { role: 'reload' },
      { role: 'forceReload' },
      { role: 'toggleDevTools' }
    ]
  },
  {
    label: 'Help',
    submenu: [
      {
        label: 'About SmartAI',
        click: () => {
          // Show about dialog
          console.log('SmartAI v1.0.0');
        }
      }
    ]
  }
];

const menu = Menu.buildFromTemplate(template);
Menu.setApplicationMenu(menu);

// ==================== AUTO-LAUNCH ====================

const AutoLaunch = require('auto-launch');

const smartaiAutoLaunch = new AutoLaunch({
  name: 'SmartAI',
  path: app.getPath('exe')
});

// Enable auto-launch for production
if (!isDev) {
  smartaiAutoLaunch.enable();
}
