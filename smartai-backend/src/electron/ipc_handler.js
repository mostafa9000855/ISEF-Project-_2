// SmartAI IPC Communication Layer
// Handles inter-process communication and data routing between all components
// File: ipc_handler.js (Electron-side)

const { ipcMain, ipcRenderer } = require('electron');
const WebSocket = require('ws');

/**
 * IPC Handler - Central message bus for SmartAI components
 * Routes messages between:
 * - Electron (Frontend)
 * - C++ Core Engine
 * - Python AI Module
 * - Databases
 */

class IPCHandler {
  constructor(smartaiIntegration) {
    this.smartai = smartaiIntegration;
    this.messageQueue = [];
    this.listeners = new Map();
    this.requestId = 0;
  }

  /**
   * Register an IPC listener
   */
  on(channel, callback) {
    if (!this.listeners.has(channel)) {
      this.listeners.set(channel, []);
    }
    this.listeners.get(channel).push(callback);
  }

  /**
   * Send message to C++ Core
   */
  sendToCore(message) {
    if (!this.smartai.coreWebSocket || !this.smartai.coreWebSocket.readyState === WebSocket.OPEN) {
      console.error('[IPC] C++ Core not connected');
      return false;
    }

    try {
      const encrypted = this.smartai.encrypt(JSON.stringify(message));
      this.smartai.coreWebSocket.send(encrypted);
      console.log(`[IPC] → Core: ${message.type}`);
      return true;
    } catch (error) {
      console.error('[IPC] Error sending to Core:', error);
      return false;
    }
  }

  /**
   * Send message to Python AI
   */
  sendToPython(message) {
    if (!this.smartai.pythonWebSocket || !this.smartai.pythonWebSocket.readyState === WebSocket.OPEN) {
      console.error('[IPC] Python AI not connected');
      return false;
    }

    try {
      const encrypted = this.smartai.encrypt(JSON.stringify(message));
      this.smartai.pythonWebSocket.send(encrypted);
      console.log(`[IPC] → Python: ${message.type}`);
      return true;
    } catch (error) {
      console.error('[IPC] Error sending to Python:', error);
      return false;
    }
  }

  /**
   * Send message to Frontend (Renderer Process)
   */
  sendToUI(channel, data) {
    if (this.smartai.mainWindow) {
      this.smartai.mainWindow.webContents.send(channel, data);
      console.log(`[IPC] → UI: ${channel}`);
    }
  }

  /**
   * Request-Response pattern with timeout
   */
  request(target, message, timeoutMs = 5000) {
    return new Promise((resolve, reject) => {
      const requestId = ++this.requestId;
      const responseChannel = `response_${requestId}`;

      const timeout = setTimeout(() => {
        reject(new Error(`Request timeout to ${target} after ${timeoutMs}ms`));
      }, timeoutMs);

      // Send request
      const request = {
        ...message,
        requestId,
        responseChannel
      };

      let sent = false;
      if (target === 'core') {
        sent = this.sendToCore(request);
      } else if (target === 'python') {
        sent = this.sendToPython(request);
      }

      if (!sent) {
        clearTimeout(timeout);
        reject(new Error(`Failed to send request to ${target}`));
        return;
      }

      // Wait for response
      const responseListener = (data) => {
        if (data.requestId === requestId) {
          clearTimeout(timeout);
          ipcMain.removeListener(responseChannel, responseListener);
          resolve(data);
        }
      };

      ipcMain.on(responseChannel, responseListener);
    });
  }

  /**
   * Broadcast message to multiple targets
   */
  broadcast(message) {
    const results = {
      core: this.sendToCore(message),
      python: this.sendToPython(message),
      ui: this.sendToUI('broadcast', message) || true
    };
    return results;
  }

  /**
   * Emit event to listeners
   */
  emit(channel, data) {
    if (this.listeners.has(channel)) {
      this.listeners.get(channel).forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          console.error(`[IPC] Error in listener for ${channel}:`, error);
        }
      });
    }
  }

  /**
   * Queue message if target unavailable
   */
  queueMessage(target, message) {
    this.messageQueue.push({ target, message, timestamp: Date.now() });
    console.log(`[IPC] Message queued for ${target}. Queue size: ${this.messageQueue.length}`);
  }

  /**
   * Flush queued messages when target becomes available
   */
  async flushQueue(target) {
    const targetMessages = this.messageQueue.filter(m => m.target === target);

    for (const item of targetMessages) {
      try {
        if (target === 'core') {
          this.sendToCore(item.message);
        } else if (target === 'python') {
          this.sendToPython(item.message);
        }
        
        // Remove from queue
        const index = this.messageQueue.indexOf(item);
        if (index > -1) {
          this.messageQueue.splice(index, 1);
        }
      } catch (error) {
        console.error(`[IPC] Error flushing message to ${target}:`, error);
      }
    }

    console.log(`[IPC] Flushed ${targetMessages.length} messages to ${target}`);
  }

  /**
   * Get component health status
   */
  getComponentStatus() {
    return {
      electron: { status: 'RUNNING' },
      core: {
        status: this.smartai.coreHealthy ? 'RUNNING' : 'OFFLINE',
        lastUpdate: this.smartai.lastCoreUpdated
      },
      python: {
        status: this.smartai.pythonHealthy ? 'RUNNING' : 'OFFLINE',
        lastUpdate: this.smartai.lastPythonUpdated
      },
      database: { status: 'OPERATIONAL' },
      websockets: {
        core: this.smartai.coreWebSocket ? 'OPEN' : 'CLOSED',
        python: this.smartai.pythonWebSocket ? 'OPEN' : 'CLOSED'
      }
    };
  }

  /**
   * Log communication statistics
   */
  getStatistics() {
    return {
      messagesQueued: this.messageQueue.length,
      listeners: this.listeners.size,
      lastRequestId: this.requestId,
      uptime: process.uptime()
    };
  }
}

// ==================== CORE MESSAGE TYPES ====================

const MessageTypes = {
  // System control
  SYSTEM_DATA: 'SYSTEM_DATA',
  KEY_SYNC: 'KEY_SYNC',
  FULL_SCAN: 'FULL_SCAN',
  
  // Responses
  AI_ANALYSIS: 'AI_ANALYSIS',
  CORE_STATUS: 'CORE_STATUS',
  
  // Commands
  ACTIVATE_VPN: 'ACTIVATE_VPN',
  BLOCK_PROCESS: 'BLOCK_PROCESS',
  MODIFY_FIREWALL: 'MODIFY_FIREWALL',
  EMERGENCY_MODE: 'EMERGENCY_MODE',
  
  // Auto-Response
  AUTO_RESPONSE_TRIGGERED: 'AUTO_RESPONSE_TRIGGERED',
  
  // Deception
  HONEYPOT_TRIGGERED: 'HONEYPOT_TRIGGERED',
  
  // Mesh
  MESH_ALERT: 'MESH_ALERT'
};

// ==================== MESSAGE BUILDERS ====================

const MessageBuilder = {
  systemData(stats) {
    return {
      type: MessageTypes.SYSTEM_DATA,
      timestamp: new Date().toISOString(),
      systemStats: stats
    };
  },

  keySync(key, nonce) {
    return {
      type: MessageTypes.KEY_SYNC,
      key,
      nonce,
      timestamp: new Date().toISOString()
    };
  },

  fullScan() {
    return {
      type: MessageTypes.FULL_SCAN,
      timestamp: new Date().toISOString()
    };
  },

  activateVPN(profile) {
    return {
      type: MessageTypes.ACTIVATE_VPN,
      profile,
      timestamp: new Date().toISOString()
    };
  },

  blockProcess(pid, reason) {
    return {
      type: MessageTypes.BLOCK_PROCESS,
      pid,
      reason,
      timestamp: new Date().toISOString()
    };
  },

  modifyFirewall(rule) {
    return {
      type: MessageTypes.MODIFY_FIREWALL,
      rule,
      timestamp: new Date().toISOString()
    };
  },

  emergencyMode(enable) {
    return {
      type: MessageTypes.EMERGENCY_MODE,
      enable,
      timestamp: new Date().toISOString()
    };
  }
};

// ==================== EVENT EMITTER ====================

class EventEmitter {
  constructor() {
    this.events = {};
  }

  on(event, listener) {
    if (!this.events[event]) {
      this.events[event] = [];
    }
    this.events[event].push(listener);
  }

  emit(event, data) {
    if (this.events[event]) {
      this.events[event].forEach(listener => listener(data));
    }
  }

  removeListener(event, listener) {
    if (this.events[event]) {
      this.events[event] = this.events[event].filter(l => l !== listener);
    }
  }
}

module.exports = {
  IPCHandler,
  MessageTypes,
  MessageBuilder,
  EventEmitter
};
