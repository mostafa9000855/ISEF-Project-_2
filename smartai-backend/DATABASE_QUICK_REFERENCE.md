# SmartAI Encrypted Database - Quick Reference Card

## Installation
```bash
pip install cryptography
```

## Import
```python
from database_encryption import DatabaseEncryption, EncryptedDatabase
import sqlite3
```

## Initialize Encryption
```python
# Initialize once with your master key
encryption = DatabaseEncryption("your_encryption_key_here")
```

## Basic Usage (Recommended - Context Manager)
```python
# Automatic encryption on exit
with EncryptedDatabase(encryption, "mydb.db") as conn:
    conn.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER, name TEXT)")
    encryption.insert(conn, 'users', {'id': 1, 'name': 'Alice'})
    rows = encryption.select(conn, 'users')
    for row in rows:
        print(f"User: {row['name']}")
```

## Manual Connection (Long-Running Processes)
```python
try:
    conn = encryption.connect("mydb.db")
    
    # Do work...
    encryption.insert(conn, 'table', {...})
    results = encryption.select(conn, 'table')
    
finally:
    # Always close and encrypt
    encryption.close(conn, encrypt=True)
```

## Database Operations

### Insert
```python
encryption.insert(conn, 'table_name', {
    'column1': 'value1',
    'column2': 'value2'
})
```

### Select All
```python
rows = encryption.select(conn, 'table_name')
for row in rows:
    print(row['column_name'])
```

### Select with WHERE
```python
rows = encryption.select(conn, 'table_name', where={'id': 1})
for row in rows:
    print(row)
```

### Update
```python
encryption.update(conn, 'table_name', 
    data={'age': 30, 'city': 'NYC'},
    where={'id': 1}
)
```

### Delete
```python
encryption.delete(conn, 'table_name', where={'id': 1})
```

### Raw SQL
```python
cursor = encryption.execute(conn, 
    "SELECT * FROM table_name WHERE age > ?", 
    (25,)
)
rows = cursor.fetchall()
```

## Key Rotation (Security)
```python
db_paths = ["db1.db", "db2.db", "db3.db"]
new_key = "new_encryption_key_q2_2024"

success = encryption.reencrypt_databases(db_paths, new_key)
if success:
    print("✓ All databases re-encrypted")
```

## Security Best Practice
```python
import os

# Get key from environment (never hardcode!)
KEY = os.getenv('SMARTAI_ENCRYPTION_KEY')
if not KEY:
    raise EnvironmentError("Set SMARTAI_ENCRYPTION_KEY environment variable")

encryption = DatabaseEncryption(KEY)
```

## SmartAI's 7 Databases
```python
DATABASES = [
    "db1_known_threats.db",      # Known threat signatures
    "db2_ai_threats.db",         # AI-discovered threats
    "db3_deception.db",          # Deception intelligence
    "db4_honeypot.db",           # Honeypot data
    "db5_mesh.db",               # Mesh defense
    "db6_vpn.db",                # VPN logs
    "db7_secure_log.db"          # Audit log
]

# All use the same encryption instance and key
for db in DATABASES:
    with EncryptedDatabase(encryption, db) as conn:
        # Work with database
        pass
```

## Error Handling
```python
try:
    with EncryptedDatabase(encryption, "test.db") as conn:
        encryption.insert(conn, 'table', {'id': 1})
except sqlite3.IntegrityError as e:
    print(f"Duplicate key: {e}")
except Exception as e:
    print(f"Database error: {e}")
```

## Verify File is Encrypted
```python
import os

path = "mydb.db"
with open(path, 'rb') as f:
    header = f.read(20)
    if b'SQLite' in header:
        print("❌ Not encrypted!")
    else:
        print(f"✓ Encrypted (header: {header[:10]})")
```

## Performance Notes
- Encryption/decryption: ~10-50ms per database
- Query performance: No impact (runs on decrypted in-memory DB)
- Disk space: No overhead
- CPU: Hardware-accelerated (AES-NI on modern CPUs)

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError: database_encryption` | Ensure file is in Python path |
| `ModuleNotFoundError: cryptography` | `pip install cryptography` |
| `sqlite3.DatabaseError` on open | Wrong encryption key used |
| `Permission denied` on file | Check file permissions (chmod 600) |
| Database looks corrupted | File is encrypted - use correct key to decrypt |

## Migration from SQLCipher

| Old | New |
|-----|-----|
| `import sqlcipher3 as sql3` | `import sqlite3` |
| `sql3.connect(path)` | `encryption.connect(path)` |
| `conn.execute("PRAGMA key = ...")` | ✗ Remove this |
| `conn.close()` | `encryption.close(conn)` |

## Logging
```python
import logging
logging.basicConfig(level=logging.INFO)
# Encryption operations logged automatically
```

## Testing
```python
# Run example file to test installation
python database_integration_guide.py
```

Expected output:
```
============================================================
SmartAI Encrypted Database Integration Examples
============================================================

EXAMPLE 1: Basic Usage with Context Manager
============================================================
✓ Database encrypted and saved to: example_threats.db
  File is binary encrypted on disk...
```

## Environment Setup
```bash
# Set encryption key (production)
export SMARTAI_ENCRYPTION_KEY="your-very-long-random-key-here-32-chars-min"

# Or in Python
import os
os.environ['SMARTAI_ENCRYPTION_KEY'] = "..."

# Load in code
encryption = DatabaseEncryption(os.getenv('SMARTAI_ENCRYPTION_KEY'))
```

## Files Reference
- **Encryption Module**: `src/python/database_encryption.py`
- **Examples**: `src/python/database_integration_guide.py`
- **Migration Guide**: `MIGRATION_SQLCIPHER_TO_CRYPTOGRAPHY.md`
- **AI Module**: `src/python/ai_module_websocket.py` (updated)
- **Dependencies**: `src/python/requirements.txt` (updated)

## Support
For issues:
1. Check logs: Look for `[DB-Encryption]` messages
2. Run examples: `python database_integration_guide.py`
3. Verify key: Ensure same key is used throughout
4. Check file: Verify encrypted file is not corrupted
5. Test permissions: File should be readable/writable

---
**Last Updated**: Q1 2024  
**Encryption**: AES-256 (Fernet)  
**Platform**: Windows, Linux, macOS ✓
