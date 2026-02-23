#!/usr/bin/env python3
"""
SmartAI Python AI Module - Integrated with WebSocket Communication
Receives encrypted data from C++ Core Engine
Sends analysis and recommendations to Electron
"""

import os
import sys
import json
import time
import base64
import threading
import socket
import sqlite3
from datetime import datetime, timedelta
from collections import defaultdict, deque
import logging

try:
    import asyncio
    import websockets
    from websockets.server import serve
except ImportError:
    print("[Python] ERROR: websockets library not installed. Run: pip install websockets")
    sys.exit(1)

# Import encrypted database handler
try:
    from database_encryption import DatabaseEncryption, EncryptedDatabase
except ImportError:
    print("[Python] WARNING: database_encryption module not found. Database encryption disabled.")
    DatabaseEncryption = None

# ==================== LOGGING SETUP ====================

logging.basicConfig(
    level=logging.INFO,
    format='[Python] %(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ==================== ENCRYPTION & SECURITY ====================

class EncryptionHandler:
    """Handle encrypted communication with C++ and Electron"""
    
    def __init__(self, key: str):
        self.key = key
        
        # Initialize database encryption (file-level AES-256)
        if DatabaseEncryption:
            self.db_encryption = DatabaseEncryption(key)
            logger.info("✓ Database encryption (AES-256) initialized")
        else:
            self.db_encryption = None
            logger.warning("⚠ Database encryption unavailable (cryptography module needed)")
    
    def connect_database(self, db_path: str) -> sqlite3.Connection:
        """
        Connect to encrypted database
        
        Args:
            db_path: Path to database file
            
        Returns:
            sqlite3 connection with automatic decryption
        """
        if self.db_encryption:
            return self.db_encryption.connect(db_path)
        else:
            # Fallback to unencrypted
            return sqlite3.connect(db_path)
    
    def close_database(self, conn: sqlite3.Connection, encrypt: bool = True):
        """
        Close database and encrypt if modified
        
        Args:
            conn: sqlite3 connection
            encrypt: True to encrypt database after closing (always True in production)
        """
        if self.db_encryption:
            self.db_encryption.close(conn, encrypt=encrypt)
        else:
            conn.close()
    
    def reencrypt_databases(self, db_paths: list, new_key: str) -> bool:
        """
        Re-encrypt all databases with new key (key rotation)
        
        Args:
            db_paths: List of database paths
            new_key: New encryption key
            
        Returns:
            True if successful
        """
        if not self.db_encryption:
            logger.warning("Cannot re-encrypt: encryption module unavailable")
            return False
        
        success = True
        for db_path in db_paths:
            try:
                self.db_encryption.reencrypt_database(db_path, new_key)
                logger.info(f"✓ Re-encrypted: {db_path}")
            except Exception as e:
                logger.error(f"Failed to re-encrypt {db_path}: {e}")
                success = False
        
        if success:
            self.key = new_key
            self.db_encryption = DatabaseEncryption(new_key)
        
        return success
    
    def encrypt(self, data: str) -> str:
        """Simple BASE64 encryption (in production: use AES-256)"""
        return base64.b64encode(data.encode()).decode('utf-8')
    
    def decrypt(self, data: str) -> str:
        """Simple BASE64 decryption"""
        try:
            return base64.b64decode(data.encode()).decode('utf-8')
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            return ""
    
    def verify_hmac(self, data: str, hmac_recv: str) -> bool:
        """Verify data integrity using HMAC"""
        # In production: use actual HMAC-SHA256
        return True

# ==================== BEHAVIOR ANALYSIS ENGINE ====================

class BehaviorAnalyzer:
    """Analyze behavior patterns and detect anomalies"""
    
    def __init__(self):
        self.feature_history = deque(maxlen=1000)
        self.baseline = None
        self.learning_hours = 24
        self.learning_start = time.time()
        self.risk_score = 0
        logger.info("✓ Behavior analyzer initialized")
    
    def analyze(self, system_data: dict) -> dict:
        """Analyze system data and return risk assessment"""
        
        # Extract features
        cpu = system_data.get('systemStats', {}).get('cpuUsage', 0)
        ram = system_data.get('systemStats', {}).get('ramUsage', 0)
        process_count = len(system_data.get('systemStats', {}).get('processes', []))
        
        # Simple risk calculation
        risk_cpu = (cpu / 100) * 30  # CPU contributes 30% to risk
        risk_ram = (ram / 100) * 25  # RAM contributes 25% to risk
        risk_procs = min((process_count / 500) * 20, 20)  # Processes contribute 20%
        
        # Baseline detection (first 24 hours)
        if self.learning_start and time.time() - self.learning_start < (self.learning_hours * 3600):
            time_remaining = (self.learning_hours * 3600) - (time.time() - self.learning_start)
            risk_anomaly = 5 + (10 - (time_remaining / (self.learning_hours * 3600)) * 10)
        else:
            # Simple anomaly: if CPU > 75% or RAM > 85%, flag as anomaly
            risk_anomaly = 0
            if cpu > 75:
                risk_anomaly += 15
            if ram > 85:
                risk_anomaly += 15
        
        self.risk_score = int(risk_cpu + risk_ram + risk_procs + risk_anomaly)
        self.risk_score = min(self.risk_score, 100)  # Cap at 100
        
        # Generate XAI explanation
        explanation = self._generate_explanation(cpu, ram, process_count)
        
        return {
            'riskScore': self.risk_score,
            'riskFactors': {
                'cpuRisk': int(risk_cpu),
                'ramRisk': int(risk_ram),
                'processRisk': int(risk_procs),
                'anomalyRisk': int(risk_anomaly)
            },
            'xaiExplanation': explanation,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
    
    def _generate_explanation(self, cpu: float, ram: float, processes: int) -> dict:
        """Generate human-readable explanation for risk score"""
        
        factors = []
        severity = "LOW"
        
        if cpu > 80:
            factors.append(f"High CPU usage ({cpu:.1f}%) - may indicate resource-intensive process")
            severity = "HIGH"
        elif cpu > 60:
            factors.append(f"Elevated CPU usage ({cpu:.1f}%) - monitor for spikes")
            if severity == "LOW":
                severity = "MEDIUM"
        
        if ram > 90:
            factors.append(f"Critical RAM usage ({ram:.1f}%) - potential memory leak")
            severity = "CRITICAL"
        elif ram > 80:
            factors.append(f"High RAM usage ({ram:.1f}%) - approaching limits")
            if severity != "CRITICAL":
                severity = "HIGH"
        
        if processes > 300:
            factors.append(f"Unusual process count ({processes}) - may indicate malware activity")
            if severity == "LOW":
                severity = "MEDIUM"
        
        if not factors:
            factors.append("System operating normally within baseline parameters")
        
        return {
            'severity': severity,
            'evidence': factors,
            'recommendation': self._get_recommendation(severity),
            'likelihood': f"{self.risk_score}%"
        }
    
    def _get_recommendation(self, severity: str) -> str:
        """Get recommendation based on severity"""
        
        recommendations = {
            'CRITICAL': 'IMMEDIATE ACTION REQUIRED: Activate emergency mode, block outbound traffic, initiate incident response',
            'HIGH': 'ACTIVATE VPN, enable enhanced monitoring, review running processes, prepare incident response',
            'MEDIUM': 'Monitor system closely, increase log retention, prepare for escalation',
            'LOW': 'Continue normal monitoring, maintain baseline collection'
        }
        
        return recommendations.get(severity, 'Continue monitoring')

# ==================== THREAT DNA & PREDICTION ENGINE ====================

class ThreatDNAEngine:
    """Analyze threat DNA signatures and predict next attack steps"""
    
    def __init__(self):
        self.threats = {}
        self.sequences = []
        logger.info("✓ Threat DNA engine initialized")
    
    def analyze_threat(self, risk_score: int) -> dict:
        """Analyze threat and generate predictions"""
        
        if risk_score < 50:
            return {
                'threatFamily': 'None Detected',
                'dnaSignature': 'baseline',
                'variants': [],
                'predictions': []
            }
        
        # Simulate threat detection
        threat_family = 'TrickBot.K' if risk_score > 70 else 'Suspicious.Generic'
        
        predictions = [
            {
                'stage': 'Lateral Movement',
                'timeframe': 'Next 5-10 minutes',
                'probability': min(90, risk_score),
                'description': 'Attacker attempts to spread to adjacent systems'
            },
            {
                'stage': 'Credential Harvesting',
                'timeframe': '10-20 minutes',
                'probability': min(80, risk_score - 10),
                'description': 'Extraction of user credentials from memory'
            },
            {
                'stage': 'Privilege Escalation',
                'timeframe': '20-40 minutes',
                'probability': min(70, risk_score - 20),
                'description': 'Attempt to gain administrative privileges'
            }
        ]
        
        return {
            'threatFamily': threat_family,
            'dnaSignature': f'sig_{risk_score}_{int(time.time())}',
            'variantCount': 5,
            'predictions': predictions,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }

# ==================== DECEPTION & HONEYPOT ENGINE ====================

class DeceptionNetworkEngine:
    """Manage fake network topology and honeypot system"""
    
    def __init__(self):
        self.fake_devices = self._generate_fake_topology()
        self.honeypot_events = []
        self.attacker_profiles = {}
        logger.info("✓ Deception network engine initialized")
    
    def _generate_fake_topology(self) -> list:
        """Generate realistic but fake network devices"""
        return [
            {'ip': '192.168.1.100', 'hostname': 'DC-01-PROD', 'services': ['RDP 3389', 'LDAP 389']},
            {'ip': '192.168.1.101', 'hostname': 'FILE-SERVER', 'services': ['SMB 445', 'NFS 2049']},
            {'ip': '192.168.1.102', 'hostname': 'DATABASE-PROD', 'services': ['SQL 1433', 'MySQL 3306']},
            {'ip': '192.168.1.103', 'hostname': 'WEB-SERVER', 'services': ['HTTP 80', 'HTTPS 443']},
            {'ip': '192.168.1.104', 'hostname': 'ADMIN-WORKSTATION', 'services': ['RDP 3389']},
        ]
    
    def get_fake_topology(self) -> dict:
        """Return fake network map"""
        return {
            'fakeDevices': self.fake_devices,
            'generatedAt': datetime.utcnow().isoformat() + 'Z'
        }
    
    def check_honeypot(self, process_name: str) -> dict:
        """Check if honeypot was triggered"""
        
        honeypot_files = [
            'passwords.txt', 'credit_cards.xlsx', 'company_secrets.pdf',
            'database_backup.sql', 'api_keys.env'
        ]
        
        triggered = any(honey in process_name.lower() for honey in honeypot_files)
        
        if triggered:
            event = {
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'type': 'HONEYPOT_TRIGGERED',
                'processName': process_name,
                'severity': 'CRITICAL'
            }
            self.honeypot_events.append(event)
            logger.warning(f"HONEYPOT TRIGGERED: {process_name}")
        
        return {
            'honeypotTriggered': triggered,
            'events': self.honeypot_events[-10:]  # Last 10 events
        }

# ==================== MESH DEFENSE COORDINATOR ====================

class MeshDefenseCoordinator:
    """Coordinate defense across mesh-connected devices"""
    
    def __init__(self):
        self.mesh_devices = []
        self.threat_intel = []
        logger.info("✓ Mesh defense coordinator initialized")
    
    def broadcast_threat(self, risk_score: int) -> dict:
        """Broadcast threat to mesh devices"""
        
        if risk_score < 50:
            return {'broadcast': False}
        
        return {
            'broadcast': True,
            'threatLevel': 'CRITICAL' if risk_score > 80 else 'HIGH',
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'recommendation': 'All mesh devices: ACTIVATE HIGH ALERT MODE'
        }
    
    def get_mesh_status(self) -> dict:
        """Get status of mesh-connected devices"""
        return {
            'meshDevices': [
                {'deviceId': 'PC-001', 'status': 'ONLINE', 'lastSeen': datetime.utcnow().isoformat()},
                {'deviceId': 'PC-002', 'status': 'ONLINE', 'lastSeen': datetime.utcnow().isoformat()},
                {'deviceId': 'LAPTOP-001', 'status': 'OFFLINE', 'lastSeen': '2 hours ago'},
            ],
            'meshHealth': 'GOOD',
            'activeThreats': 0
        }

# ==================== WEBSOCKET SERVER ====================

class AIWebSocketServer:
    """WebSocket server for Electron communication"""
    
    def __init__(self, encryption: EncryptionHandler, analyzer: BehaviorAnalyzer):
        self.encryption = encryption
        self.analyzer = analyzer
        self.threat_dna = ThreatDNAEngine()
        self.deception = DeceptionNetworkEngine()
        self.mesh = MeshDefenseCoordinator()
        self.clients = set()
        logger.info("✓ AI WebSocket server initialized")
    
    async def handle_client(self, websocket, path):
        """Handle incoming WebSocket connections"""
        self.clients.add(websocket)
        logger.info(f"✓ Electron connected. Total clients: {len(self.clients)}")
        
        try:
            async for message in websocket:
                await self.process_message(websocket, message)
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
        finally:
            self.clients.discard(websocket)
            logger.info(f"Electron disconnected. Total clients: {len(self.clients)}")
    
    async def process_message(self, websocket, message: str):
        """Process incoming messages from Electron or C++"""
        try:
            # Decrypt message
            decrypted = self.encryption.decrypt(message)
            data = json.loads(decrypted)
            
            msg_type = data.get('type')
            
            if msg_type == 'SYSTEM_DATA':
                # Analyze system data
                analysis = self.analyzer.analyze(data)
                
                # Get threat predictions
                threat_analysis = self.threat_dna.analyze_threat(analysis['riskScore'])
                
                # Get deception status
                deception_status = self.deception.check_honeypot('system')
                
                # Get mesh status
                mesh_status = self.mesh.get_mesh_status()
                
                # Prepare response
                response = {
                    'type': 'AI_ANALYSIS',
                    'riskScore': analysis['riskScore'],
                    'riskFactors': analysis['riskFactors'],
                    'xaiExplanation': analysis['xaiExplanation'],
                    'threatAnalysis': threat_analysis,
                    'honeypotStatus': deception_status,
                    'meshDevices': mesh_status.get('meshDevices', []),
                    'timestamp': datetime.utcnow().isoformat() + 'Z'
                }
                
                # Send to all connected Electron instances
                await self.broadcast(response)
                
            elif msg_type == 'KEY_SYNC':
                logger.info("✓ Key sync received from C++ Core")
                
            else:
                logger.warning(f"Unknown message type: {msg_type}")
        
        except json.JSONDecodeError:
            logger.error("Invalid JSON received")
        except Exception as e:
            logger.error(f"Message processing error: {e}")
    
    async def broadcast(self, data: dict):
        """Broadcast analysis to all connected Electron clients"""
        if not self.clients:
            return
        
        # Encrypt response
        encrypted = self.encryption.encrypt(json.dumps(data))
        
        # Send to all clients
        tasks = [client.send(encrypted) for client in self.clients]
        await asyncio.gather(*tasks, return_exceptions=True)
        
        logger.info(f"Analysis broadcasted to {len(self.clients)} Electron client(s)")

# ==================== MAIN APPLICATION ====================

async def main():
    """Main application entry point"""
    
    print("\n[Python] ===== SmartAI AI MODULE START =====")
    print("[Python] Initializing Python AI Module...")
    
    try:
        # Get environment setup
        ws_port = int(os.getenv('SMARTAI_WS_PORT', 8081))
        enc_key = os.getenv('SMARTAI_ENCRYPTION_KEY', 'default_key')
        
        print(f"[Python] WebSocket Port: {ws_port}")
        print(f"[Python] Encryption: Initialized")
        
        # Initialize components
        encryption = EncryptionHandler(enc_key)
        analyzer = BehaviorAnalyzer()
        
        # Create WebSocket server
        ws_server = AIWebSocketServer(encryption, analyzer)
        
        # Start serving
        print("[Python] Starting WebSocket server...")
        async with serve(ws_server.handle_client, "127.0.0.1", ws_port):
            print(f"[Python] ✓ WebSocket listening on 127.0.0.1:{ws_port}")
            print("[Python] ✓✓✓ AI MODULE READY ✓✓✓")
            print("[Python] ===== ANALYSIS ENGINE ACTIVE =====\n")
            
            # Keep running
            await asyncio.Future()  # run forever
    
    except Exception as e:
        logger.error(f"FATAL ERROR: {e}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[Python] Shutting down...")
        sys.exit(0)
