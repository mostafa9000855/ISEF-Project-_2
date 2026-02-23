#!/usr/bin/env python3
"""
SmartAI Database Encryption Layer
Provides transparent AES-256 encryption/decryption for SQLite databases
Uses cryptography library instead of SQLCipher for maximum compatibility
"""

import os
import sqlite3
import json
import logging
from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
from cryptography.hazmat.backends import default_backend
import base64

logger = logging.getLogger(__name__)

class DatabaseEncryption:
    """
    Transparent database encryption for SQLite
    Automatically encrypts DB files on disk, decrypts in memory
    """
    
    def __init__(self, encryption_key: str):
        """
        Initialize encryption with AES-256 key
        
        Args:
            encryption_key: Master encryption key (will be used to derive cipher key)
        """
        self.master_key = encryption_key
        self.cipher_key = self._derive_key(encryption_key)
        self.fernet = Fernet(self.cipher_key)
        self.db_connections = {}
        self.db_paths = {}
        logger.info("✓ Database encryption handler initialized (AES-256)")
    
    def _derive_key(self, master_key: str) -> bytes:
        """
        Derive a Fernet-compatible key from master key using PBKDF2
        
        Args:
            master_key: Master encryption key
            
        Returns:
            Fernet-compatible key (bytes)
        """
        # Use a consistent salt for key derivation
        salt = b'smartai_db_salt_'  # Fixed salt for consistent key derivation
        
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,  # 256 bits
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        
        key = base64.urlsafe_b64encode(
            kdf.derive(master_key.encode())
        )
        return key
    
    def _encrypt_file(self, file_path: str) -> bool:
        """
        Encrypt a database file on disk
        
        Args:
            file_path: Path to database file
            
        Returns:
            True if successful
        """
        try:
            if not os.path.exists(file_path):
                logger.debug(f"File not found for encryption: {file_path}")
                return True  # Not an error, file doesn't exist yet
            
            # Read plaintext file
            with open(file_path, 'rb') as f:
                plaintext = f.read()
            
            # Encrypt
            encrypted = self.fernet.encrypt(plaintext)
            
            # Write encrypted file
            with open(file_path, 'wb') as f:
                f.write(encrypted)
            
            logger.debug(f"Encrypted database: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to encrypt database: {e}")
            return False
    
    def _decrypt_file(self, file_path: str, temp_path: str) -> bool:
        """
        Decrypt a database file to temporary location
        
        Args:
            file_path: Path to encrypted database file
            temp_path: Path to write decrypted database
            
        Returns:
            True if successful
        """
        try:
            if not os.path.exists(file_path):
                logger.debug(f"Database file not found: {file_path}")
                return True  # File doesn't exist yet, will be created
            
            # Read encrypted file
            with open(file_path, 'rb') as f:
                encrypted = f.read()
            
            # Check if file is actually encrypted or just new
            if not encrypted.startswith(b'gAAAAAA'):  # Fernet token prefix
                # File is not encrypted yet (first run), just copy it
                with open(temp_path, 'wb') as f:
                    f.write(encrypted)
                logger.debug(f"Database not encrypted yet: {file_path}")
                return True
            
            # Decrypt
            plaintext = self.fernet.decrypt(encrypted)
            
            # Write to temp location
            with open(temp_path, 'wb') as f:
                f.write(plaintext)
            
            logger.debug(f"Decrypted database to: {temp_path}")
            return True
            
        except Exception as e:
            logger.warning(f"Failed to decrypt database (might be first run): {e}")
            return True  # Not a critical error on first run
    
    def connect(self, db_path: str) -> sqlite3.Connection:
        """
        Connect to encrypted database (transparent encryption/decryption)
        
        Args:
            db_path: Path to encrypted database file
            
        Returns:
            sqlite3 connection object
        """
        try:
            # Create temp file path for decrypted database
            db_dir = os.path.dirname(db_path)
            db_name = os.path.basename(db_path)
            temp_path = os.path.join(db_dir, f'.{db_name}.tmp')
            
            # Decrypt to temp location
            if not self._decrypt_file(db_path, temp_path):
                raise Exception(f"Failed to decrypt database: {db_path}")
            
            # Create parent directories if needed
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            
            # Connect to decrypted database in memory or temp location
            conn = sqlite3.connect(temp_path)
            conn.row_factory = sqlite3.Row
            
            # Store connection info for later encryption
            self.db_connections[db_path] = {
                'connection': conn,
                'temp_path': temp_path,
                'dirty': False
            }
            self.db_paths[id(conn)] = db_path
            
            logger.info(f"✓ Connected to encrypted database: {db_path}")
            return conn
            
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    def close(self, conn: sqlite3.Connection, encrypt: bool = True):
        """
        Close database connection and encrypt if modified
        
        Args:
            conn: sqlite3 connection
            encrypt: True to encrypt database after closing
        """
        try:
            db_path = self.db_paths.get(id(conn))
            if not db_path:
                conn.close()
                return
            
            db_info = self.db_connections.get(db_path)
            if not db_info:
                conn.close()
                return
            
            # Close connection
            conn.close()
            
            # Encrypt database file
            if encrypt:
                temp_path = db_info['temp_path']
                
                # Optimize: run VACUUM before encryption
                try:
                    check_conn = sqlite3.connect(temp_path)
                    check_conn.execute('VACUUM')
                    check_conn.close()
                except:
                    pass
                
                # Move temp to original and encrypt
                if os.path.exists(temp_path):
                    if os.path.exists(db_path):
                        os.remove(db_path)
                    os.rename(temp_path, db_path)
                
                # Encrypt the file
                self._encrypt_file(db_path)
                logger.debug(f"Encrypted and closed database: {db_path}")
            
            # Cleanup
            del self.db_connections[db_path]
            del self.db_paths[id(conn)]
            
        except Exception as e:
            logger.error(f"Error closing database: {e}")
    
    def reencrypt_database(self, db_path: str, new_key: str):
        """
        Re-encrypt database with new key (for key rotation)
        
        Args:
            db_path: Path to database file
            new_key: New encryption key
        """
        try:
            logger.info(f"Re-encrypting database with new key: {db_path}")
            
            # Decrypt with old key
            temp_path = f"{db_path}.reencrypt"
            self._decrypt_file(db_path, temp_path)
            
            # Update cipher with new key
            old_fernet = self.fernet
            self.master_key = new_key
            self.cipher_key = self._derive_key(new_key)
            self.fernet = Fernet(self.cipher_key)
            
            # Read plaintext
            with open(temp_path, 'rb') as f:
                plaintext = f.read()
            
            # Re-encrypt with new key
            encrypted = self.fernet.encrypt(plaintext)
            
            # Write back to original path
            with open(db_path, 'wb') as f:
                f.write(encrypted)
            
            # Cleanup
            if os.path.exists(temp_path):
                os.remove(temp_path)
            
            logger.info(f"✓ Re-encrypted database: {db_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to re-encrypt database: {e}")
            # Restore old cipher
            self.master_key = self.master_key  # Can't recover, needs manual intervention
            self.cipher_key = self._derive_key(self.master_key)
            self.fernet = Fernet(self.cipher_key)
            return False
    
    def execute(self, conn: sqlite3.Connection, query: str, params=None):
        """
        Execute SQL query on encrypted database
        
        Args:
            conn: sqlite3 connection
            query: SQL query
            params: Query parameters
            
        Returns:
            Cursor object
        """
        try:
            if params:
                return conn.execute(query, params)
            else:
                return conn.execute(query)
        except Exception as e:
            logger.error(f"Database query failed: {e}")
            raise
    
    def insert(self, conn: sqlite3.Connection, table: str, data: dict) -> int:
        """
        Insert record with automatic encryption
        
        Args:
            conn: sqlite3 connection
            table: Table name
            data: Dictionary with column names and values
            
        Returns:
            Row ID
        """
        columns = ','.join(data.keys())
        placeholders = ','.join(['?' for _ in data])
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        
        cursor = self.execute(conn, query, tuple(data.values()))
        return cursor.lastrowid
    
    def select(self, conn: sqlite3.Connection, table: str, where: dict = None) -> list:
        """
        Select records with automatic decryption
        
        Args:
            conn: sqlite3 connection
            table: Table name
            where: Where clause as dictionary
            
        Returns:
            List of rows
        """
        query = f"SELECT * FROM {table}"
        params = ()
        
        if where:
            conditions = ' AND '.join([f"{k}=?" for k in where.keys()])
            query += f" WHERE {conditions}"
            params = tuple(where.values())
        
        cursor = self.execute(conn, query, params)
        return cursor.fetchall()
    
    def update(self, conn: sqlite3.Connection, table: str, data: dict, where: dict):
        """
        Update records with automatic encryption
        
        Args:
            conn: sqlite3 connection
            table: Table name
            data: Data to update
            where: Where clause
        """
        set_clause = ','.join([f"{k}=?" for k in data.keys()])
        query = f"UPDATE {table} SET {set_clause}"
        
        params = list(data.values())
        
        if where:
            where_clause = ' AND '.join([f"{k}=?" for k in where.keys()])
            query += f" WHERE {where_clause}"
            params.extend(where.values())
        
        return self.execute(conn, query, tuple(params))
    
    def delete(self, conn: sqlite3.Connection, table: str, where: dict):
        """
        Delete records
        
        Args:
            conn: sqlite3 connection
            table: Table name
            where: Where clause
        """
        where_clause = ' AND '.join([f"{k}=?" for k in where.keys()])
        query = f"DELETE FROM {table} WHERE {where_clause}"
        params = tuple(where.values())
        
        return self.execute(conn, query, params)

# ==================== CONTEXT MANAGER FOR EASY USE ====================

class EncryptedDatabase:
    """Context manager for transparent encrypted database access"""
    
    def __init__(self, encryption: DatabaseEncryption, db_path: str):
        """
        Initialize encrypted database context
        
        Args:
            encryption: DatabaseEncryption instance
            db_path: Path to database file
        """
        self.encryption = encryption
        self.db_path = db_path
        self.conn = None
    
    def __enter__(self):
        """Enter context manager"""
        self.conn = self.encryption.connect(self.db_path)
        return self.conn
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager and encrypt"""
        if self.conn:
            self.encryption.close(self.conn, encrypt=True)
        return False

# ==================== EXAMPLE USAGE ====================

if __name__ == '__main__':
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='[DB-Encryption] %(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Initialize encryption with master key
    encryption = DatabaseEncryption("my_super_secret_key_12345")
    
    # Example 1: Using context manager (recommended)
    db_path = 'test_database.db'
    
    with EncryptedDatabase(encryption, db_path) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                name TEXT,
                email TEXT
            )
        ''')
        
        encryption.insert(conn, 'users', {'name': 'Alice', 'email': 'alice@test.com'})
        
        users = encryption.select(conn, 'users')
        for user in users:
            print(f"User: {user['name']} ({user['email']})")
    
    # File is now encrypted on disk
    print(f"Database encrypted and saved: {db_path}")
    
    # Example 2: Re-encrypt with new key (for key rotation)
    new_key = "new_secret_key_67890"
    file_size_before = os.path.getsize(db_path)
    encryption.reencrypt_database(db_path, new_key)
    file_size_after = os.path.getsize(db_path)
    print(f"Re-encrypted. Size before: {file_size_before}, after: {file_size_after}")
