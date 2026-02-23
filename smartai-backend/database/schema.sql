-- SmartAI Database Schema
-- All databases encrypted with AES-256
-- Created: 2024

-- ==================== DB1: Known Threats ====================
CREATE TABLE known_threats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    signature TEXT NOT NULL,
    severity TEXT CHECK(severity IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
    threat_type TEXT,
    detection_method TEXT,
    date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP,
    quarantine_path TEXT,
    is_encrypted INTEGER DEFAULT 1
);

CREATE INDEX idx_threat_severity ON known_threats(severity);
CREATE INDEX idx_threat_type ON known_threats(threat_type);

-- ==================== DB2: AI Discovered Threats + DNA ====================
CREATE TABLE discovered_threats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    threat_name TEXT NOT NULL,
    threat_family TEXT,
    severity TEXT CHECK(severity IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
    dna_signature TEXT NOT NULL,
    features TEXT,  -- JSON array of feature vectors
    variants TEXT,  -- JSON array of variants
    risk_score REAL,
    confidence REAL,
    detection_method TEXT,
    is_encrypted INTEGER DEFAULT 1
);

CREATE TABLE threat_dna_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    threat_family TEXT UNIQUE,
    primary_dna_signature TEXT,
    variant_count INTEGER DEFAULT 1,
    first_detected TIMESTAMP,
    last_detected TIMESTAMP,
    mutation_patterns TEXT,  -- JSON: evolution of threat
    is_encrypted INTEGER DEFAULT 1
);

CREATE TABLE predicted_variants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    parent_threat_id INTEGER,
    predicted_signature TEXT,
    prediction_confidence REAL,
    mutation_type TEXT,
    created_timestamp TIMESTAMP,
    is_encrypted INTEGER DEFAULT 1,
    FOREIGN KEY(parent_threat_id) REFERENCES discovered_threats(id)
);

CREATE INDEX idx_discovered_family ON discovered_threats(threat_family);
CREATE INDEX idx_discovered_risk ON discovered_threats(risk_score);

-- ==================== DB3: Secure Action Logs (Append-Only) ====================
CREATE TABLE action_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    action TEXT NOT NULL,  -- FIREWALL_MODIFIED, PROCESS_BLOCKED, VPN_ACTIVATED, etc.
    source TEXT,  -- Component that performed action (C++, Python, Auto-Response)
    target TEXT,  -- What was affected (process name, IP, port, etc.)
    result TEXT CHECK(result IN ('SUCCESS', 'FAILED', 'PARTIAL')),
    details TEXT,  -- JSON with additional info
    risk_score REAL,
    is_encrypted INTEGER DEFAULT 1
);

CREATE INDEX idx_logs_timestamp ON action_logs(timestamp);
CREATE INDEX idx_logs_action ON action_logs(action);
CREATE INDEX idx_logs_result ON action_logs(result);

-- ==================== DB4: Deception Intelligence ====================
CREATE TABLE fake_network_map (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fake_ip TEXT UNIQUE,
    fake_hostname TEXT,
    fake_os TEXT,
    fake_services TEXT,  -- JSON array of fake services
    fake_credentials TEXT,  -- JSON array of fake creds
    date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    views_by_attackers INTEGER DEFAULT 0,
    is_encrypted INTEGER DEFAULT 1
);

CREATE TABLE attacker_movements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    attacker_ip TEXT NOT NULL,
    targeted_fake_asset TEXT,  -- IP or service
    action_taken TEXT,  -- port_scan, login_attempt, credential_test
    tools_detected TEXT,  -- JSON array
    intelligence_gathered TEXT,  -- What we learned
    is_encrypted INTEGER DEFAULT 1
);

CREATE TABLE deception_alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    trigger_type TEXT,  -- fake_service_access, fake_credential_used, etc.
    attacker_ip TEXT,
    attacker_profile TEXT,  -- JSON: inferred tools, patterns
    risk_score REAL,
    confidence REAL,
    response_action TEXT,
    is_encrypted INTEGER DEFAULT 1
);

CREATE INDEX idx_attacker_movements ON attacker_movements(attacker_ip);
CREATE INDEX idx_deception_alerts ON deception_alerts(attacker_ip);

-- ==================== DB5: VPN & Network Actions ====================
CREATE TABLE vpn_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    action TEXT CHECK(action IN ('CONNECT', 'DISCONNECT', 'FAILOVER', 'SWITCH')),
    vpn_profile TEXT,
    old_ip_address TEXT,
    new_ip_address TEXT,
    trigger_risk_score REAL,
    duration_seconds INTEGER,
    success INTEGER,
    is_encrypted INTEGER DEFAULT 1
);

CREATE TABLE firewall_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    rule_type TEXT CHECK(rule_type IN ('BLOCK', 'ALLOW', 'ALERT')),
    target_process TEXT,
    target_ip TEXT,
    target_port INTEGER,
    protocol TEXT CHECK(protocol IN ('TCP', 'UDP', 'BOTH')),
    reason TEXT,
    active INTEGER DEFAULT 1,
    triggered_count INTEGER DEFAULT 0,
    is_encrypted INTEGER DEFAULT 1
);

CREATE TABLE network_topology (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    interface_name TEXT,
    ip_address TEXT,
    subnet_mask TEXT,
    gateway TEXT,
    dns_servers TEXT,
    mac_address TEXT,
    is_encrypted INTEGER DEFAULT 1,
    UNIQUE(interface_name, ip_address)
);

CREATE INDEX idx_vpn_logs ON vpn_logs(timestamp);
CREATE INDEX idx_firewall_active ON firewall_rules(active);

-- ==================== DB6: Honeypot Intelligence ====================
CREATE TABLE honeypot_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path TEXT UNIQUE PRIMARY KEY,
    file_type TEXT,  -- passwords, credit_cards, secrets, config
    file_size_bytes INTEGER,
    date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    access_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMP,
    is_encrypted INTEGER DEFAULT 1
);

CREATE TABLE honeypot_alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    file_accessed TEXT,
    file_type TEXT,
    process_name TEXT,
    process_pid INTEGER,
    process_parent_pid INTEGER,
    process_command_line TEXT,
    source_ip TEXT,
    source_port INTEGER,
    severity TEXT CHECK(severity IN ('HIGH', 'CRITICAL')),
    memory_snapshot_path TEXT,
    memory_snapshot_hash TEXT,
    actions_recorded TEXT,  -- Path to recorded actions
    is_encrypted INTEGER DEFAULT 1
);

CREATE TABLE honey_credentials (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    password_hash TEXT,
    planted_location TEXT,  -- file_path or service
    planted_timestamp TIMESTAMP,
    used_timestamp TIMESTAMP,
    used_from_ip TEXT,
    used_from_machine TEXT,
    authentication_log_entry TEXT,
    is_encrypted INTEGER DEFAULT 1
);

CREATE TABLE fake_service_connections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    attacker_ip TEXT,
    attacker_port INTEGER,
    targeted_service TEXT,  -- RDP, SMB, SSH, FTP
    targeted_port INTEGER,
    banner_sent TEXT,
    tools_detected TEXT,  -- JSON array: nmap, metasploit, etc.
    severity TEXT DEFAULT 'HIGH',
    is_encrypted INTEGER DEFAULT 1
);

CREATE INDEX idx_honeypot_alerts ON honeypot_alerts(timestamp);
CREATE INDEX idx_honey_credentials ON honey_credentials(used_timestamp);
CREATE INDEX idx_fake_service ON fake_service_connections(attacker_ip);

-- ==================== DB7: Mesh Defense Intelligence ====================
CREATE TABLE mesh_devices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id TEXT UNIQUE,
    device_name TEXT,
    ip_address TEXT,
    mac_address TEXT,
    smartai_version TEXT,
    status TEXT CHECK(status IN ('ONLINE', 'OFFLINE', 'COMPROMISED')),
    first_seen TIMESTAMP,
    last_seen TIMESTAMP,
    threat_alerts_received INTEGER DEFAULT 0,
    threat_alerts_confirmed INTEGER DEFAULT 0,
    high_alert_mode INTEGER DEFAULT 0,
    is_encrypted INTEGER DEFAULT 1
);

CREATE TABLE shared_threats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    source_device_id TEXT,
    threat_signature TEXT,
    attacker_ip TEXT,
    attack_type TEXT,  -- malware, intrusion, deception, etc.
    risk_score REAL,
    confidence REAL,
    votes_received INTEGER DEFAULT 0,
    votes_confirmed INTEGER DEFAULT 0,
    consensus_reached INTEGER DEFAULT 0,
    is_encrypted INTEGER DEFAULT 1
);

CREATE TABLE mesh_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    event_type TEXT CHECK(event_type IN ('DEVICE_ADDED', 'DEVICE_REMOVED', 'THREAT_DETECTED', 'CONSENSUS_REACHED', 'COLLECTIVE_DEFENSE')),
    affected_devices TEXT,  -- JSON array of device IDs
    description TEXT,
    severity TEXT,
    is_encrypted INTEGER DEFAULT 1
);

CREATE TABLE mesh_communications_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    source_device_id TEXT,
    destination_device_id TEXT,
    message_type TEXT,
    message_size_bytes INTEGER,
    encrypted INTEGER DEFAULT 1,
    authenticated INTEGER DEFAULT 1,
    is_encrypted INTEGER DEFAULT 1
);

CREATE INDEX idx_mesh_devices ON mesh_devices(device_id);
CREATE INDEX idx_shared_threats ON shared_threats(source_device_id);
CREATE INDEX idx_mesh_events ON mesh_events(timestamp);

-- ==================== DB8: Key Management ====================
CREATE TABLE key_rotations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rotation_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    old_key_hash TEXT,  -- Hash of old key (never store actual key)
    new_key_hash TEXT,
    rotation_interval_hours INTEGER,
    trigger_reason TEXT,  -- scheduled, manual, emergency
    success INTEGER,
    databases_re_encrypted INTEGER DEFAULT 0,
    old_key_destruction_timestamp TIMESTAMP
);

CREATE TABLE encryption_metadata (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    database_name TEXT UNIQUE,
    current_key_hash TEXT,
    encryption_algorithm TEXT CHECK(encryption_algorithm IN ('AES-256-CBC', 'AES-256-GCM')),
    last_rotation TIMESTAMP,
    next_rotation TIMESTAMP,
    record_count INTEGER,
    total_size_bytes INTEGER
);

-- ==================== Views for Reporting ====================

-- Overview of current threat landscape
CREATE VIEW threat_overview AS
SELECT 
    COUNT(*) as total_threats,
    SUM(CASE WHEN severity = 'CRITICAL' THEN 1 ELSE 0 END) as critical_threats,
    SUM(CASE WHEN severity = 'HIGH' THEN 1 ELSE 0 END) as high_threats,
    AVG(risk_score) as avg_risk_score,
    MAX(risk_score) as max_risk_score
FROM discovered_threats;

-- Active attacker profile
CREATE VIEW active_attackers AS
SELECT 
    attacker_ip,
    COUNT(*) as interaction_count,
    COUNT(DISTINCT targeted_fake_asset) as unique_targets,
    MAX(timestamp) as last_seen,
    GROUP_CONCAT(DISTINCT tools_detected) as suspected_tools
FROM attacker_movements
WHERE timestamp > datetime('now', '-24 hours')
GROUP BY attacker_ip
ORDER BY interaction_count DESC;

-- System security posture
CREATE VIEW security_posture AS
SELECT 
    (SELECT COUNT(*) FROM firewall_rules WHERE active = 1) as active_rules,
    (SELECT COUNT(*) FROM honeypot_files WHERE access_count > 0) as triggered_honeypots,
    (SELECT COUNT(*) FROM mesh_devices WHERE status = 'ONLINE') as online_mesh_devices,
    (SELECT AVG(risk_score) FROM discovered_threats WHERE timestamp > datetime('now', '-1 hour')) as recent_avg_threat,
    (SELECT COUNT(DISTINCT source_device_id) FROM shared_threats WHERE timestamp > datetime('now', '-1 hour')) as threats_from_mesh;

-- ==================== Table Comments ====================

-- All tables are encrypted with the current AES-256 key
-- On key rotation, all records are re-encrypted with the new key
-- Append-only logs cannot have records modified after creation
-- All timestamps in UTC
-- All IP addresses are stored encrypted
-- All credentials are hashed and salted
