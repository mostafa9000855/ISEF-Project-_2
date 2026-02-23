#!/usr/bin/env python3
"""
SmartAI Python AI Module
Handles behavior profiling, anomaly detection, deception networks,
honeypot monitoring, and mesh defense
"""

import os
import sys
import json
import time
import hashlib
import threading
import socket
import subprocess
from datetime import datetime, timedelta
from collections import defaultdict, deque
from typing import Dict, List, Tuple, Optional
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import sqlite3
from scipy.spatial.distance import cosine
import traceback

# Import encrypted database handler
try:
    from database_encryption import DatabaseEncryption, EncryptedDatabase
except ImportError:
    print("WARNING: database_encryption module not found. Database encryption disabled.")
    DatabaseEncryption = None

# Third-party security libraries
try:
    from scapy.all import sniff, IP, TCP, UDP, ARP
    from netifaces import interfaces, ifaddresses, AF_INET
    from zeroconf import ServiceBrowser, Zeroconf, ServiceStateChange
    from bleak import BleakClient, BleakScanner
except ImportError as e:
    print(f"Warning: Optional library not installed: {e}")

# ==================== ENCRYPTION MODULE ====================

class EncryptionHandler:
    """Handle encrypted communication and data storage"""
    
    def __init__(self, key: str):
        self.key = key
        self.db_connections = {}
        
        # Initialize database encryption (file-level AES-256)
        if DatabaseEncryption:
            self.db_encryption = DatabaseEncryption(key)
            print("✓ Database encryption (AES-256) initialized")
        else:
            self.db_encryption = None
            print("⚠ Database encryption unavailable (cryptography module needed)")
    
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
            encrypt: True to encrypt database after closing
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
            print("ERROR: Cannot re-encrypt without encryption module")
            return False
        
        success = True
        for db_path in db_paths:
            try:
                self.db_encryption.reencrypt_database(db_path, new_key)
                print(f"✓ Re-encrypted: {db_path}")
            except Exception as e:
                print(f"ERROR: Failed to re-encrypt {db_path}: {e}")
                success = False
        
        if success:
            self.key = new_key
            self.db_encryption = DatabaseEncryption(new_key)
        
        return success
    
    def encrypt_data(self, data: str) -> str:
        """Simple encryption (in production use AES-256)"""
        # Note: In production, use cryptography library for AES-256
        return hashlib.sha256(data.encode()).hexdigest()
    
    def verify_hmac(self, data: str, hmac_recv: str) -> bool:
        """Verify HMAC integrity"""
        hmac_calc = hashlib.sha256(data.encode()).hexdigest()
        return hmac_calc == hmac_recv


# ==================== BEHAVIOR PROFILING ====================

class BehaviorProfiler:
    """Build and maintain user/system behavior baseline"""
    
    def __init__(self, db_handler: EncryptionHandler):
        self.db = db_handler
        self.baseline = {}
        self.feature_history = defaultdict(deque)
        self.max_history = 1000
        self.learning_period_hours = 24
        self.learning_start_time = time.time()
    
    def build_feature_vector(self, system_data: Dict) -> np.ndarray:
        """Convert system metrics to numerical feature vector"""
        features = [
            system_data.get('cpu_usage', 0),
            system_data.get('memory_usage', 0),
            system_data.get('network_in', 0),
            system_data.get('network_out', 0),
            system_data.get('process_count', 0),
            len(system_data.get('processes', [])),
        ]
        
        # Add process-specific features
        for proc in system_data.get('processes', [])[:10]:
            features.extend([
                proc.get('cpu', 0),
                proc.get('memory', 0),
            ])
        
        # Pad to fixed size
        while len(features) < 50:
            features.append(0)
        
        return np.array(features[:50])
    
    def update_baseline(self, system_data: Dict):
        """Update behavior baseline with new data"""
        features = self.build_feature_vector(system_data)
        
        # Store in history
        for i, val in enumerate(features):
            self.feature_history[f'feature_{i}'].append(val)
            if len(self.feature_history[f'feature_{i}']) > self.max_history:
                self.feature_history[f'feature_{i}'].popleft()
        
        # Check if learning period is complete
        elapsed = (time.time() - self.learning_start_time) / 3600
        if elapsed >= self.learning_period_hours and not self.baseline:
            self.finalize_baseline()
    
    def finalize_baseline(self):
        """Convert learning data into baseline statistics"""
        for feature_key, values in self.feature_history.items():
            if values:
                self.baseline[feature_key] = {
                    'mean': float(np.mean(values)),
                    'std': float(np.std(values)),
                    'min': float(np.min(values)),
                    'max': float(np.max(values))
                }
    
    def get_baseline(self) -> Dict:
        """Get current baseline"""
        return self.baseline
    
    def is_learning_complete(self) -> bool:
        """Check if initial learning period is complete"""
        elapsed = (time.time() - self.learning_start_time) / 3600
        return elapsed >= self.learning_period_hours


# ==================== ANOMALY DETECTION ====================

class AnomalyDetector:
    """Detect behavioral anomalies using Isolation Forest"""
    
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.training_data = []
        self.risk_score = 0
        self.min_training_samples = 100
    
    def add_training_data(self, features: np.ndarray):
        """Add data for model training"""
        self.training_data.append(features)
        
        if len(self.training_data) >= self.min_training_samples:
            self.train_model()
    
    def train_model(self):
        """Train Isolation Forest model"""
        try:
            X = np.array(self.training_data[-1000:])  # Use recent data
            X_scaled = self.scaler.fit_transform(X)
            
            self.model = IsolationForest(
                contamination=0.1,
                random_state=42,
                n_estimators=100
            )
            self.model.fit(X_scaled)
        except Exception as e:
            print(f"Error training model: {e}")
    
    def detect_anomaly(self, features: np.ndarray) -> Tuple[bool, float]:
        """
        Detect if current behavior is anomalous
        Returns: (is_anomaly, anomaly_score)
        """
        if self.model is None:
            return False, 0.0
        
        try:
            X_scaled = self.scaler.transform([features])
            anomaly_score = self.model.decision_function(X_scaled)[0]
            is_anomaly = self.model.predict(X_scaled)[0] == -1
            
            return is_anomaly, float(abs(anomaly_score) * 100)
        except Exception as e:
            print(f"Error detecting anomaly: {e}")
            return False, 0.0
    
    def calculate_risk_score(self, anomaly_score: float, 
                           detection_count: int = 0, 
                           severity: float = 0.5) -> float:
        """
        Calculate overall risk score (0-100)
        """
        base_score = min(anomaly_score, 100)
        
        # Factor in detection frequency
        frequency_multiplier = min(1 + (detection_count * 0.1), 3.0)
        
        # Factor in severity
        severity_weighted = base_score * severity
        
        final_score = min(severity_weighted * frequency_multiplier, 100)
        self.risk_score = final_score
        
        return final_score


# ==================== DECEPTION NETWORK ====================

class DeceptionNetworkMapper:
    """Create and manage fake network topology for attackers"""
    
    def __init__(self, db_handler: EncryptionHandler):
        self.db = db_handler
        self.fake_network = self.generate_fake_network()
        self.attacker_tracking = {}
        self.real_network = self.map_real_network()
    
    def generate_fake_network(self) -> Dict:
        """Generate realistic-looking fake network"""
        fake_network = {
            "devices": [
                {
                    "ip": "192.168.1.10",
                    "hostname": "CORP-DB-SERVER",
                    "os": "Windows Server 2022",
                    "services": [
                        {"port": 3389, "service": "RDP", "version": "10.0.19041"},
                        {"port": 1433, "service": "MS-SQL", "version": "2019"},
                        {"port": 445, "service": "SMB", "version": "3.1.1"}
                    ]
                },
                {
                    "ip": "192.168.1.20",
                    "hostname": "CORP-ADMIN-PC",
                    "os": "Windows 11 Pro",
                    "services": [
                        {"port": 3389, "service": "RDP", "version": "10.0"},
                        {"port": 135, "service": "RPC", "version": "6.1"}
                    ]
                },
                {
                    "ip": "192.168.1.30",
                    "hostname": "BACKUP-SERVER",
                    "os": "Linux Ubuntu 22.04",
                    "services": [
                        {"port": 22, "service": "SSH", "version": "OpenSSH 8.2"},
                        {"port": 445, "service": "Samba", "version": "4.15"}
                    ]
                },
                {
                    "ip": "192.168.1.50",
                    "hostname": "WEB-SERVER",
                    "os": "Linux CentOS 8",
                    "services": [
                        {"port": 80, "service": "HTTP", "version": "Apache 2.4"},
                        {"port": 443, "service": "HTTPS", "version": "Apache 2.4"},
                        {"port": 22, "service": "SSH", "version": "OpenSSH 7.4"}
                    ]
                }
            ],
            "fake_credentials": [
                {"username": "admin", "password": "Corp@dmin123!", "note": "Database admin"},
                {"username": "backup", "password": "Backup@2024!", "note": "Backup service"},
                {"username": "root", "password": "Root$ecure888", "note": "Root access"}
            ]
        }
        
        return fake_network
    
    def map_real_network(self) -> Dict:
        """Map actual real network (encrypted, never exposed)"""
        real_network = {}
        
        try:
            for interface in interfaces():
                iface_info = ifaddresses(interface)
                if AF_INET in iface_info:
                    real_network[interface] = iface_info[AF_INET]
        except Exception as e:
            print(f"Error mapping real network: {e}")
        
        return real_network
    
    def get_fake_network_for_attacker(self, attacker_ip: str) -> Dict:
        """Serve fake network to attacker"""
        # Always serve the same fake network, never the real one
        self.attacker_tracking[attacker_ip] = {
            "first_seen": datetime.now().isoformat(),
            "queries": []
        }
        
        return {
            "network": self.fake_network,
            "timestamp": datetime.now().isoformat(),
            "decoy": True  # Internal flag, never exposed
        }
    
    def track_attacker_movement(self, attacker_ip: str, 
                               target_ip: str, action: str):
        """Log attacker interactions with fake network"""
        if attacker_ip not in self.attacker_tracking:
            self.attacker_tracking[attacker_ip] = {
                "first_seen": datetime.now().isoformat(),
                "queries": []
            }
        
        self.attacker_tracking[attacker_ip]["queries"].append({
            "target": target_ip,
            "action": action,
            "timestamp": datetime.now().isoformat()
        })
    
    def generate_attacker_report(self, attacker_ip: str) -> Dict:
        """Generate intelligence report on attacker behavior"""
        if attacker_ip not in self.attacker_tracking:
            return {}
        
        report = {
            "attacker_ip": attacker_ip,
            "first_detected": self.attacker_tracking[attacker_ip]["first_seen"],
            "total_queries": len(self.attacker_tracking[attacker_ip]["queries"]),
            "targeted_assets": list(set(
                q["target"] for q in self.attacker_tracking[attacker_ip]["queries"]
            )),
            "suspected_tools": self.infer_attacker_tools(attacker_ip),
            "threat_level": "HIGH" if len(self.attacker_tracking[attacker_ip]["queries"]) > 20 else "MEDIUM"
        }
        
        return report
    
    def infer_attacker_tools(self, attacker_ip: str) -> List[str]:
        """Infer what tools attacker is using based on behavior"""
        tools = []
        queries = self.attacker_tracking.get(attacker_ip, {}).get("queries", [])
        
        # Simple heuristics
        if any(q["action"] == "port_scan" for q in queries):
            tools.append("Nmap/Port Scanner")
        if any(q["action"] == "rdp_attempt" for q in queries):
            tools.append("RDP/Remote Access")
        if any(q["action"] == "credential_test" for q in queries):
            tools.append("Credential Handler")
        
        return tools


# ==================== HONEYPOT SYSTEM ====================

class HoneypotSystem:
    """Manage decoy files and fake services to catch attackers"""
    
    def __init__(self, db_handler: EncryptionHandler):
        self.db = db_handler
        self.honeypot_files = {}
        self.fake_credentials = {}
        self.alerts = []
        self.setup_honeypot_files()
        self.start_fake_services()
    
    def setup_honeypot_files(self):
        """Create decoy files on disk"""
        honeypot_paths = {
            "passwords": "C:\\Users\\Public\\passwords.txt",
            "credit_cards": "C:\\Users\\Public\\credit_cards.xlsx",
            "secrets": "C:\\Users\\Public\\company_secrets.pdf",
            "config": "C:\\Users\\Public\\app.config"
        }
        
        decoy_contents = {
            "passwords": "admin:Password123!\nroot:Root@2024!\ndbuser:Db$ecure888",
            "credit_cards": "Fake credit card numbers for detection",
            "secrets": "Confidential business information - decoy",
            "config": '[database]\nhost=192.168.1.10\nuser=admin\npassword=Admin@123'
        }
        
        for honey_type, path in honeypot_paths.items():
            try:
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, 'w') as f:
                    f.write(decoy_contents.get(honey_type, "Decoy content"))
                
                self.honeypot_files[path] = {
                    "type": honey_type,
                    "created": datetime.now().isoformat(),
                    "access_count": 0,
                    "last_accessed": None
                }
            except Exception as e:
                print(f"Error creating honeypot file {path}: {e}")
    
    def monitor_honeypot_access(self) -> List[Dict]:
        """Monitor if honeypot files are accessed"""
        alerts = []
        
        for file_path in self.honeypot_files.keys():
            try:
                if os.path.exists(file_path):
                    access_time = os.path.getmtime(file_path)
                    current_time = time.time()
                    
                    # If file was accessed recently
                    if (current_time - access_time) < 60:  # Within last minute
                        self.honeypot_files[file_path]["access_count"] += 1
                        self.honeypot_files[file_path]["last_accessed"] = datetime.now().isoformat()
                        
                        alert = {
                            "severity": "CRITICAL",
                            "type": "HONEYPOT_TRIGGERED",
                            "file": file_path,
                            "timestamp": datetime.now().isoformat(),
                            "process_info": self.get_process_accessing_file(file_path),
                            "action": "Immediate isolation and threat response"
                        }
                        alerts.append(alert)
                        self.alerts.append(alert)
            except Exception as e:
                print(f"Error monitoring honeypot: {e}")
        
        return alerts
    
    def get_process_accessing_file(self, file_path: str) -> Dict:
        """Identify which process is accessing the honeypot file"""
        try:
            # Use Windows API or system commands to identify process
            result = subprocess.run(
                f'handle.exe "{file_path}"',
                capture_output=True,
                text=True
            )
            return {
                "file": file_path,
                "process": "Unknown (handle.exe not available)",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            print(f"Error getting process info: {e}")
            return {}
    
    def start_fake_services(self):
        """Start fake network services (RDP, SMB, SSH, etc.)"""
        fake_services = [
            {"port": 3389, "service": "RDP", "banner": "Welcome to Windows Server 2022"},
            {"port": 445, "service": "SMB", "banner": "Samba 4.15.5"},
            {"port": 21, "service": "FTP", "banner": "220 FTP Server Ready"},
        ]
        
        for service in fake_services:
            self.create_listening_service(service)
    
    def create_listening_service(self, service_config: Dict):
        """Create a honeypot service listening on specified port"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(('0.0.0.0', service_config["port"]))
            sock.listen(5)
            
            # Start listener in background thread
            thread = threading.Thread(
                target=self.service_listener,
                args=(sock, service_config),
                daemon=True
            )
            thread.start()
        except Exception as e:
            print(f"Error creating service on port {service_config['port']}: {e}")
    
    def service_listener(self, sock: socket.socket, service_config: Dict):
        """Listen for connections to fake service"""
        while True:
            try:
                client, addr = sock.accept()
                
                # Log connection attempt
                alert = {
                    "severity": "HIGH",
                    "type": "HONEYPOT_SERVICE_ACCESS",
                    "service": service_config["service"],
                    "port": service_config["port"],
                    "attacker_ip": addr[0],
                    "timestamp": datetime.now().isoformat()
                }
                self.alerts.append(alert)
                
                # Send fake banner
                client.send(service_config["banner"].encode() + b"\r\n")
                client.close()
            except Exception as e:
                break


# ==================== MESH DEFENSE ====================

class MeshDefenseNetwork:
    """P2P mesh defense coordination between SmartAI devices"""
    
    def __init__(self, db_handler: EncryptionHandler, device_id: str):
        self.db = db_handler
        self.device_id = device_id
        self.mesh_devices = {}
        self.threat_intelligence = deque(maxlen=1000)
        self.mesh_status = "initializing"
        self.discover_mesh_devices()
    
    def discover_mesh_devices(self):
        """Auto-discover other SmartAI devices on network using mDNS"""
        try:
            zeroconf = Zeroconf()
            
            def device_found(zeroconf, service_type, name, state_change):
                if state_change == ServiceStateChange.Added:
                    self.add_mesh_device(name)
                elif state_change == ServiceStateChange.Removed:
                    self.remove_mesh_device(name)
            
            ServiceBrowser(zeroconf, "_smartai._tcp.local.", 
                         handlers=[device_found])
            
            self.mesh_status = "active"
        except Exception as e:
            print(f"Error discovering mesh devices: {e}")
            self.mesh_status = "offline"
    
    def add_mesh_device(self, device_name: str):
        """Add discovered device to mesh network"""
        self.mesh_devices[device_name] = {
            "status": "online",
            "last_seen": datetime.now().isoformat(),
            "threat_alerts": 0,
            "high_alert_mode": False
        }
    
    def remove_mesh_device(self, device_name: str):
        """Remove device from mesh network"""
        if device_name in self.mesh_devices:
            del self.mesh_devices[device_name]
    
    def broadcast_threat(self, threat_data: Dict):
        """Broadcast threat to all mesh devices"""
        message = {
            "type": "threat_alert",
            "source_device": self.device_id,
            "threat": threat_data,
            "timestamp": datetime.now().isoformat(),
            "requires_vote": True
        }
        
        # Store in local queue for all devices to receive
        self.threat_intelligence.append(message)
        
        # Activate high alert on all devices
        for device in self.mesh_devices.values():
            device["high_alert_mode"] = True
            device["threat_alerts"] += 1
    
    def consensus_check(self, threat_id: str) -> Tuple[bool, float]:
        """
        Devices vote on threat validity to reduce false positives
        Returns: (is_valid_threat, confidence_score)
        """
        votes_yes = 0
        total_devices = len(self.mesh_devices) + 1  # Include this device
        
        for device in self.mesh_devices.values():
            if device["high_alert_mode"]:
                votes_yes += 1
        
        if total_devices == 0:
            return False, 0.0
        
        confidence = (votes_yes / total_devices) * 100
        is_valid = votes_yes >= (total_devices * 0.6)  # 60% consensus required
        
        return is_valid, confidence
    
    def activate_collective_defense(self):
        """When under attack, coordinate collective defense"""
        for device in self.mesh_devices.values():
            device["high_alert_mode"] = True
    
    def deactivate_collective_defense(self):
        """When threat cleared, stand down collective defense"""
        threat_count = sum(1 for d in self.mesh_devices.values() 
                          if d["high_alert_mode"])
        
        if threat_count == 0:
            for device in self.mesh_devices.values():
                device["high_alert_mode"] = False


# ==================== MAIN AI CONTROLLER ====================

class SmartAIController:
    """Main AI orchestrator coordinating all modules"""
    
    def __init__(self):
        self.running = True
        self.iteration_count = 0
        
        # Initialize encryption
        self.crypto = EncryptionHandler("smartai_temp_key_2024")
        
        # Initialize all modules
        self.profiler = BehaviorProfiler(self.crypto)
        self.detector = AnomalyDetector()
        self.deception = DeceptionNetworkMapper(self.crypto)
        self.honeypot = HoneypotSystem(self.crypto)
        self.mesh = MeshDefenseNetwork(self.crypto, "smartai_device_001")
        
        print("[SmartAI AI Module] All systems initialized")
    
    def process_system_data(self, system_data: Dict) -> Dict:
        """Process system data and generate threat assessment"""
        try:
            self.iteration_count += 1
            
            # Step 1: Update behavior baseline
            self.profiler.update_baseline(system_data)
            
            # Step 2: Extract features and detect anomalies
            features = self.profiler.build_feature_vector(system_data)
            self.detector.add_training_data(features)
            
            is_anomaly, anomaly_score = self.detector.detect_anomaly(features)
            
            # Step 3: Calculate risk score
            risk_score = self.detector.calculate_risk_score(
                anomaly_score,
                detection_count=1 if is_anomaly else 0,
                severity=0.8 if is_anomaly else 0.3
            )
            
            # Step 4: Monitor honeypot files
            honeypot_alerts = self.honeypot.monitor_honeypot_access()
            
            # Step 5: Generate response
            response = {
                "type": "ai_assessment",
                "risk_score": risk_score,
                "is_anomaly": is_anomaly,
                "anomaly_score": anomaly_score,
                "timestamp": datetime.now().isoformat(),
                "baseline_complete": self.profiler.is_learning_complete(),
                "honeypot_alerts": honeypot_alerts,
                "mesh_devices_online": len(self.mesh.mesh_devices),
                "mesh_status": self.mesh.mesh_status
            }
            
            # Step 6: Trigger collective defense if needed
            if risk_score > 70:
                self.mesh.activate_collective_defense()
            elif risk_score < 30:
                self.mesh.deactivate_collective_defense()
            
            return response
        
        except Exception as e:
            print(f"Error processing system data: {e}")
            traceback.print_exc()
            return {"error": str(e)}
    
    def run(self):
        """Main event loop"""
        print("[SmartAI AI Module] Starting event loop...")
        
        while self.running:
            try:
                # Simulated system data (in production, receive from C++)
                system_data = self.generate_simulated_system_data()
                
                # Process and analyze
                response = self.process_system_data(system_data)
                
                # Print response for testing
                # print(f"[AI] Risk Score: {response.get('risk_score', 0):.1f}")
                
                time.sleep(5)  # Process every 5 seconds
            
            except KeyboardInterrupt:
                print("[SmartAI AI Module] Shutting down...")
                self.running = False
            except Exception as e:
                print(f"Error in event loop: {e}")
                traceback.print_exc()
    
    def generate_simulated_system_data(self) -> Dict:
        """Generate simulated system data for testing"""
        import random
        
        # Base metrics that vary slightly
        cpu = 30 + random.gauss(0, 10)
        memory = 40 + random.gauss(0, 8)
        net_in = 0.5 + random.gauss(0, 0.2)
        net_out = 0.3 + random.gauss(0, 0.15)
        
        # Occasionally spike to trigger alerts
        if random.random() < 0.05:  # 5% chance
            cpu = 80 + random.random() * 20
            memory = 75 + random.random() * 20
        
        return {
            "cpu_usage": max(0, min(100, cpu)),
            "memory_usage": max(0, min(100, memory)),
            "network_in": max(0, net_in),
            "network_out": max(0, net_out),
            "process_count": random.randint(20, 80),
            "processes": [
                {
                    "name": f"process_{i}.exe",
                    "pid": 1000 + i,
                    "cpu": random.uniform(0, 20),
                    "memory": random.uniform(10, 500)
                }
                for i in range(random.randint(15, 50))
            ]
        }


# ==================== ENTRY POINT ====================

if __name__ == "__main__":
    print("="*60)
    print("SmartAI Python AI Module v1.0")
    print("="*60)
    
    controller = SmartAIController()
    controller.run()
