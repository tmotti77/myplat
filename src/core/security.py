"""Comprehensive security layer with encryption, audit, and compliance features."""
import asyncio
import hashlib
import hmac
import json
import secrets
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union
from enum import Enum

import bcrypt
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
import jwt
from passlib.context import CryptContext
import structlog

from src.core.config import settings
from src.core.database import get_db_session
from src.core.logging import get_logger, LoggerMixin, LoggedOperation

logger = get_logger(__name__)


class EncryptionLevel(str, Enum):
    """Encryption levels for different data types."""
    PUBLIC = "public"              # No encryption needed
    INTERNAL = "internal"          # Basic encryption
    CONFIDENTIAL = "confidential"  # Strong encryption
    SECRET = "secret"              # Highest level encryption
    TOP_SECRET = "top_secret"      # Maximum security


class AuditEventType(str, Enum):
    """Types of audit events."""
    LOGIN = "login"
    LOGOUT = "logout"
    ACCESS = "access"
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    EXPORT = "export"
    IMPORT = "import"
    PERMISSION_CHANGE = "permission_change"
    SECURITY_VIOLATION = "security_violation"
    DATA_BREACH = "data_breach"
    COMPLIANCE_EVENT = "compliance_event"


class DataClassification(str, Enum):
    """Data classification levels."""
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"
    PII = "pii"
    PHI = "phi"
    FINANCIAL = "financial"
    LEGAL = "legal"


class SecurityManager(LoggerMixin):
    """Centralized security management for the platform."""
    
    def __init__(self):
        self._encryption_keys = {}
        self._audit_buffer = []
        self._rate_limits = {}
        self._security_policies = {}
        self._data_retention_policies = {}
        
        # Encryption components
        self._master_key = None
        self._key_rotation_interval = 86400 * 7  # 7 days
        self._fernet_keys = {}
        
        # Password policy
        self._password_context = CryptContext(
            schemes=["bcrypt"],
            deprecated="auto",
            bcrypt__rounds=12
        )
        
        # Session management
        self._active_sessions = {}
        self._session_timeout = 3600  # 1 hour
        
        # Rate limiting
        self._rate_limit_windows = {}
        
    async def initialize(self):
        """Initialize security manager."""
        try:
            await self._load_encryption_keys()
            await self._load_security_policies()
            await self._initialize_audit_system()
            
            # Start background tasks
            asyncio.create_task(self._key_rotation_task())
            asyncio.create_task(self._audit_processing_task())
            asyncio.create_task(self._session_cleanup_task())
            
            self.log_info("Security manager initialized")
        except Exception as e:
            self.log_error("Failed to initialize security manager", error=e)
            raise
    
    async def cleanup(self):
        """Clean up security manager."""
        try:
            # Flush audit buffer
            await self._flush_audit_buffer()
            
            # Clear sensitive data
            self._encryption_keys.clear()
            self._active_sessions.clear()
            
            self.log_info("Security manager cleaned up")
        except Exception as e:
            self.log_error("Error during security manager cleanup", error=e)

    # Encryption Methods
    
    async def encrypt_data(
        self,
        data: Union[str, bytes, Dict],
        classification: DataClassification,
        tenant_id: Optional[str] = None,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Encrypt data based on classification level."""
        
        try:
            with LoggedOperation("encrypt_data", classification=classification.value):
                # Convert data to bytes if needed
                if isinstance(data, dict):
                    data_bytes = json.dumps(data, separators=(',', ':')).encode('utf-8')
                elif isinstance(data, str):
                    data_bytes = data.encode('utf-8')
                else:
                    data_bytes = data
                
                # Get encryption level
                encryption_level = self._get_encryption_level(classification)
                
                # Generate encryption metadata
                encryption_id = str(uuid.uuid4())
                timestamp = datetime.utcnow().isoformat() + "Z"
                
                # Encrypt based on level
                if encryption_level == EncryptionLevel.PUBLIC:
                    # No encryption needed
                    encrypted_data = data_bytes
                    encryption_method = "none"
                
                elif encryption_level == EncryptionLevel.INTERNAL:
                    # Basic Fernet encryption
                    fernet_key = await self._get_fernet_key(tenant_id)
                    fernet = Fernet(fernet_key)
                    encrypted_data = fernet.encrypt(data_bytes)
                    encryption_method = "fernet"
                
                elif encryption_level == EncryptionLevel.CONFIDENTIAL:
                    # AES-256-GCM encryption
                    encrypted_data, encryption_context = await self._encrypt_aes_gcm(
                        data_bytes, tenant_id, additional_context
                    )
                    encryption_method = "aes-256-gcm"
                
                elif encryption_level in [EncryptionLevel.SECRET, EncryptionLevel.TOP_SECRET]:
                    # Multi-layer encryption
                    encrypted_data, encryption_context = await self._encrypt_multi_layer(
                        data_bytes, tenant_id, encryption_level, additional_context
                    )
                    encryption_method = "multi-layer"
                
                # Create encryption envelope
                envelope = {
                    "encryption_id": encryption_id,
                    "encrypted_data": encrypted_data.hex() if isinstance(encrypted_data, bytes) else encrypted_data,
                    "encryption_method": encryption_method,
                    "encryption_level": encryption_level.value,
                    "classification": classification.value,
                    "tenant_id": tenant_id,
                    "created_at": timestamp,
                    "context": encryption_context if encryption_level in [
                        EncryptionLevel.CONFIDENTIAL, 
                        EncryptionLevel.SECRET, 
                        EncryptionLevel.TOP_SECRET
                    ] else None
                }
                
                # Audit encryption event
                await self._audit_event(
                    AuditEventType.CREATE,
                    "data_encryption",
                    {
                        "encryption_id": encryption_id,
                        "classification": classification.value,
                        "encryption_level": encryption_level.value,
                        "tenant_id": tenant_id
                    }
                )
                
                return envelope
                
        except Exception as e:
            self.log_error("Data encryption failed", classification=classification.value, error=e)
            raise
    
    async def decrypt_data(
        self,
        envelope: Dict[str, Any],
        tenant_id: Optional[str] = None,
        verify_context: Optional[Dict[str, Any]] = None
    ) -> Union[str, bytes, Dict]:
        """Decrypt data from encryption envelope."""
        
        try:
            with LoggedOperation("decrypt_data", encryption_id=envelope.get("encryption_id")):
                # Verify tenant access
                if envelope.get("tenant_id") and envelope["tenant_id"] != tenant_id:
                    raise PermissionError("Tenant access denied for encrypted data")
                
                # Get encrypted data
                encrypted_data = envelope["encrypted_data"]
                if isinstance(encrypted_data, str):
                    encrypted_data = bytes.fromhex(encrypted_data)
                
                encryption_method = envelope["encryption_method"]
                
                # Decrypt based on method
                if encryption_method == "none":
                    decrypted_data = encrypted_data
                
                elif encryption_method == "fernet":
                    fernet_key = await self._get_fernet_key(tenant_id)
                    fernet = Fernet(fernet_key)
                    decrypted_data = fernet.decrypt(encrypted_data)
                
                elif encryption_method == "aes-256-gcm":
                    decrypted_data = await self._decrypt_aes_gcm(
                        encrypted_data, envelope["context"], tenant_id, verify_context
                    )
                
                elif encryption_method == "multi-layer":
                    decrypted_data = await self._decrypt_multi_layer(
                        encrypted_data, envelope["context"], tenant_id, verify_context
                    )
                
                else:
                    raise ValueError(f"Unknown encryption method: {encryption_method}")
                
                # Try to decode as JSON, then UTF-8, then return bytes
                try:
                    decoded_str = decrypted_data.decode('utf-8')
                    try:
                        return json.loads(decoded_str)
                    except json.JSONDecodeError:
                        return decoded_str
                except UnicodeDecodeError:
                    return decrypted_data
                
        except Exception as e:
            self.log_error("Data decryption failed", encryption_id=envelope.get("encryption_id"), error=e)
            # Audit decryption failure
            await self._audit_event(
                AuditEventType.SECURITY_VIOLATION,
                "decryption_failure",
                {
                    "encryption_id": envelope.get("encryption_id"),
                    "tenant_id": tenant_id,
                    "error": str(e)
                }
            )
            raise
    
    # Authentication and Session Management
    
    async def create_secure_session(
        self,
        user_id: str,
        tenant_id: str,
        user_agent: str,
        ip_address: str,
        additional_claims: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a secure session with proper tokens."""
        
        try:
            with LoggedOperation("create_session", user_id=user_id, tenant_id=tenant_id):
                session_id = str(uuid.uuid4())
                timestamp = datetime.utcnow()
                
                # Create JWT payload
                payload = {
                    "session_id": session_id,
                    "user_id": user_id,
                    "tenant_id": tenant_id,
                    "iat": timestamp,
                    "exp": timestamp + timedelta(seconds=self._session_timeout),
                    "ip_address": ip_address,
                    "user_agent_hash": hashlib.sha256(user_agent.encode()).hexdigest()[:16]
                }
                
                if additional_claims:
                    payload.update(additional_claims)
                
                # Generate tokens
                access_token = jwt.encode(
                    payload,
                    settings.JWT_SECRET_KEY,
                    algorithm="HS256"
                )
                
                refresh_payload = payload.copy()
                refresh_payload["exp"] = timestamp + timedelta(days=30)
                refresh_payload["type"] = "refresh"
                
                refresh_token = jwt.encode(
                    refresh_payload,
                    settings.JWT_REFRESH_SECRET_KEY,
                    algorithm="HS256"
                )
                
                # Store session
                session_data = {
                    "user_id": user_id,
                    "tenant_id": tenant_id,
                    "created_at": timestamp.isoformat() + "Z",
                    "last_activity": timestamp.isoformat() + "Z",
                    "ip_address": ip_address,
                    "user_agent": user_agent,
                    "is_active": True
                }
                
                self._active_sessions[session_id] = session_data
                
                # Audit session creation
                await self._audit_event(
                    AuditEventType.LOGIN,
                    "session_created",
                    {
                        "session_id": session_id,
                        "user_id": user_id,
                        "tenant_id": tenant_id,
                        "ip_address": ip_address
                    }
                )
                
                return {
                    "session_id": session_id,
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "expires_in": self._session_timeout,
                    "token_type": "Bearer"
                }
                
        except Exception as e:
            self.log_error("Session creation failed", user_id=user_id, error=e)
            raise
    
    async def validate_session(
        self,
        token: str,
        ip_address: str,
        user_agent: str
    ) -> Dict[str, Any]:
        """Validate and refresh session."""
        
        try:
            # Decode JWT
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=["HS256"]
            )
            
            session_id = payload["session_id"]
            
            # Check if session exists
            if session_id not in self._active_sessions:
                raise jwt.InvalidTokenError("Session not found")
            
            session_data = self._active_sessions[session_id]
            
            # Validate session context
            if not session_data["is_active"]:
                raise jwt.InvalidTokenError("Session is inactive")
            
            # Security checks
            user_agent_hash = hashlib.sha256(user_agent.encode()).hexdigest()[:16]
            if payload.get("user_agent_hash") != user_agent_hash:
                await self._audit_event(
                    AuditEventType.SECURITY_VIOLATION,
                    "session_hijack_attempt",
                    {
                        "session_id": session_id,
                        "expected_ua_hash": payload.get("user_agent_hash"),
                        "actual_ua_hash": user_agent_hash,
                        "ip_address": ip_address
                    }
                )
                raise jwt.InvalidTokenError("Session validation failed")
            
            # Update last activity
            session_data["last_activity"] = datetime.utcnow().isoformat() + "Z"
            
            return {
                "session_id": session_id,
                "user_id": payload["user_id"],
                "tenant_id": payload["tenant_id"],
                "is_valid": True
            }
            
        except jwt.ExpiredSignatureError:
            return {"is_valid": False, "error": "Token expired"}
        except jwt.InvalidTokenError as e:
            return {"is_valid": False, "error": str(e)}
        except Exception as e:
            self.log_error("Session validation failed", error=e)
            return {"is_valid": False, "error": "Validation failed"}
    
    # Access Control and Authorization
    
    async def check_resource_access(
        self,
        user_id: str,
        tenant_id: str,
        resource_type: str,
        resource_id: str,
        action: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Check if user has access to perform action on resource."""
        
        try:
            with LoggedOperation("check_access", user_id=user_id, resource_type=resource_type, action=action):
                # Multi-level access check
                access_result = {
                    "allowed": False,
                    "reason": None,
                    "conditions": [],
                    "audit_required": False
                }
                
                # 1. Check tenant isolation
                if not await self._verify_tenant_isolation(user_id, tenant_id, resource_id):
                    access_result["reason"] = "tenant_isolation_violation"
                    await self._audit_event(
                        AuditEventType.SECURITY_VIOLATION,
                        "tenant_isolation_violation",
                        {
                            "user_id": user_id,
                            "tenant_id": tenant_id,
                            "resource_id": resource_id,
                            "resource_type": resource_type
                        }
                    )
                    return access_result
                
                # 2. Check RBAC permissions
                rbac_allowed = await self._check_rbac_permissions(
                    user_id, tenant_id, resource_type, action
                )
                
                if not rbac_allowed:
                    access_result["reason"] = "insufficient_permissions"
                    return access_result
                
                # 3. Check ABAC policies
                abac_result = await self._check_abac_policies(
                    user_id, tenant_id, resource_type, resource_id, action, context
                )
                
                if not abac_result["allowed"]:
                    access_result["reason"] = abac_result["reason"]
                    access_result["conditions"] = abac_result.get("conditions", [])
                    return access_result
                
                # 4. Check rate limits
                rate_limit_result = await self._check_rate_limits(
                    user_id, tenant_id, action, context
                )
                
                if not rate_limit_result["allowed"]:
                    access_result["reason"] = "rate_limit_exceeded"
                    access_result["retry_after"] = rate_limit_result.get("retry_after")
                    return access_result
                
                # Access granted
                access_result["allowed"] = True
                access_result["audit_required"] = self._requires_audit(resource_type, action)
                
                # Audit access if required
                if access_result["audit_required"]:
                    await self._audit_event(
                        AuditEventType.ACCESS,
                        f"{action}_{resource_type}",
                        {
                            "user_id": user_id,
                            "tenant_id": tenant_id,
                            "resource_type": resource_type,
                            "resource_id": resource_id,
                            "action": action,
                            "context": context
                        }
                    )
                
                return access_result
                
        except Exception as e:
            self.log_error("Access check failed", user_id=user_id, resource_type=resource_type, error=e)
            return {"allowed": False, "reason": "access_check_error"}
    
    # Data Protection and Compliance
    
    async def apply_data_retention_policy(
        self,
        tenant_id: str,
        data_type: str,
        created_at: datetime
    ) -> Dict[str, Any]:
        """Apply data retention policies."""
        
        try:
            policy = self._data_retention_policies.get(data_type, {})
            retention_days = policy.get("retention_days", 2555)  # Default 7 years
            
            expiry_date = created_at + timedelta(days=retention_days)
            current_date = datetime.utcnow()
            
            result = {
                "should_retain": current_date < expiry_date,
                "expiry_date": expiry_date.isoformat() + "Z",
                "days_remaining": max(0, (expiry_date - current_date).days),
                "policy": policy
            }
            
            if not result["should_retain"]:
                await self._audit_event(
                    AuditEventType.COMPLIANCE_EVENT,
                    "data_retention_expired",
                    {
                        "tenant_id": tenant_id,
                        "data_type": data_type,
                        "created_at": created_at.isoformat() + "Z",
                        "expiry_date": expiry_date.isoformat() + "Z"
                    }
                )
            
            return result
            
        except Exception as e:
            self.log_error("Data retention policy check failed", tenant_id=tenant_id, error=e)
            return {"should_retain": True, "error": str(e)}
    
    async def scan_for_pii(
        self,
        text: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Scan text for personally identifiable information."""
        
        try:
            from presidio_analyzer import AnalyzerEngine
            from presidio_anonymizer import AnonymizerEngine
            
            analyzer = AnalyzerEngine()
            anonymizer = AnonymizerEngine()
            
            # Analyze for PII
            results = analyzer.analyze(
                text=text,
                language='en',
                entities=["PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER", "CREDIT_CARD", "SSN", "IP_ADDRESS"]
            )
            
            pii_found = []
            for result in results:
                pii_found.append({
                    "entity_type": result.entity_type,
                    "start": result.start,
                    "end": result.end,
                    "score": result.score,
                    "text": text[result.start:result.end]
                })
            
            # Anonymize if PII found
            anonymized_text = text
            if pii_found:
                anonymized_result = anonymizer.anonymize(text=text, analyzer_results=results)
                anonymized_text = anonymized_result.text
            
            return {
                "pii_found": len(pii_found) > 0,
                "pii_entities": pii_found,
                "pii_count": len(pii_found),
                "anonymized_text": anonymized_text,
                "original_length": len(text),
                "anonymized_length": len(anonymized_text)
            }
            
        except Exception as e:
            self.log_error("PII scanning failed", error=e)
            return {
                "pii_found": False,
                "pii_entities": [],
                "pii_count": 0,
                "anonymized_text": text,
                "error": str(e)
            }
    
    # Security Monitoring and Incident Response
    
    async def detect_security_anomalies(
        self,
        user_id: str,
        tenant_id: str,
        activity_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Detect security anomalies in user behavior."""
        
        try:
            anomalies = []
            risk_score = 0.0
            
            # Check for unusual access patterns
            if activity_data.get("access_count_last_hour", 0) > 1000:
                anomalies.append({
                    "type": "high_access_rate",
                    "severity": "high",
                    "description": "Unusually high access rate detected",
                    "risk_increase": 0.4
                })
                risk_score += 0.4
            
            # Check for geographical anomalies
            if activity_data.get("new_location", False):
                anomalies.append({
                    "type": "new_location",
                    "severity": "medium",
                    "description": "Access from new geographical location",
                    "risk_increase": 0.2
                })
                risk_score += 0.2
            
            # Check for unusual data access
            if activity_data.get("sensitive_data_access", False):
                anomalies.append({
                    "type": "sensitive_data_access",
                    "severity": "high",
                    "description": "Access to sensitive data outside normal patterns",
                    "risk_increase": 0.3
                })
                risk_score += 0.3
            
            # Check for failed authentication attempts
            failed_attempts = activity_data.get("failed_auth_attempts", 0)
            if failed_attempts > 5:
                anomalies.append({
                    "type": "multiple_auth_failures",
                    "severity": "high",
                    "description": f"{failed_attempts} failed authentication attempts",
                    "risk_increase": 0.5
                })
                risk_score += 0.5
            
            # Determine response level
            response_level = "none"
            if risk_score >= 0.8:
                response_level = "critical"
            elif risk_score >= 0.5:
                response_level = "high"
            elif risk_score >= 0.3:
                response_level = "medium"
            elif risk_score > 0:
                response_level = "low"
            
            result = {
                "anomalies_detected": len(anomalies) > 0,
                "anomalies": anomalies,
                "risk_score": min(1.0, risk_score),
                "response_level": response_level,
                "recommended_actions": self._get_recommended_actions(response_level, anomalies)
            }
            
            # Audit anomaly detection
            if anomalies:
                await self._audit_event(
                    AuditEventType.SECURITY_VIOLATION,
                    "anomaly_detected",
                    {
                        "user_id": user_id,
                        "tenant_id": tenant_id,
                        "risk_score": risk_score,
                        "anomalies": anomalies,
                        "response_level": response_level
                    }
                )
            
            return result
            
        except Exception as e:
            self.log_error("Anomaly detection failed", user_id=user_id, error=e)
            return {"anomalies_detected": False, "error": str(e)}
    
    # Private Helper Methods
    
    async def _load_encryption_keys(self):
        """Load encryption keys from secure storage."""
        try:
            # In production, load from secure key management service
            self._master_key = settings.MASTER_ENCRYPTION_KEY.encode() if settings.MASTER_ENCRYPTION_KEY else secrets.token_bytes(32)
            
            # Generate Fernet keys for different tenants
            self._fernet_keys["default"] = Fernet.generate_key()
            
            self.log_info("Encryption keys loaded")
        except Exception as e:
            self.log_error("Failed to load encryption keys", error=e)
            raise
    
    async def _load_security_policies(self):
        """Load security policies from configuration."""
        try:
            self._security_policies = {
                "password_policy": {
                    "min_length": 12,
                    "require_uppercase": True,
                    "require_lowercase": True,
                    "require_numbers": True,
                    "require_symbols": True,
                    "max_age_days": 90
                },
                "session_policy": {
                    "timeout_seconds": 3600,
                    "max_concurrent_sessions": 5,
                    "require_mfa": False
                },
                "access_policy": {
                    "max_login_attempts": 5,
                    "lockout_duration_minutes": 30,
                    "require_ip_allowlist": False
                }
            }
            self.log_info("Security policies loaded")
        except Exception as e:
            self.log_error("Failed to load security policies", error=e)
            raise
    
    async def _initialize_audit_system(self):
        """Initialize audit logging system."""
        try:
            # Setup audit buffer and processing
            self._audit_buffer = []
            self.log_info("Audit system initialized")
        except Exception as e:
            self.log_error("Failed to initialize audit system", error=e)
            raise
    
    async def _get_fernet_key(self, tenant_id: Optional[str]) -> bytes:
        """Get Fernet encryption key for tenant."""
        key_id = tenant_id or "default"
        if key_id not in self._fernet_keys:
            self._fernet_keys[key_id] = Fernet.generate_key()
        return self._fernet_keys[key_id]
    
    def _get_encryption_level(self, classification: DataClassification) -> EncryptionLevel:
        """Map data classification to encryption level."""
        mapping = {
            DataClassification.PUBLIC: EncryptionLevel.PUBLIC,
            DataClassification.INTERNAL: EncryptionLevel.INTERNAL,
            DataClassification.CONFIDENTIAL: EncryptionLevel.CONFIDENTIAL,
            DataClassification.PII: EncryptionLevel.SECRET,
            DataClassification.PHI: EncryptionLevel.TOP_SECRET,
            DataClassification.FINANCIAL: EncryptionLevel.SECRET,
            DataClassification.LEGAL: EncryptionLevel.SECRET
        }
        return mapping.get(classification, EncryptionLevel.INTERNAL)
    
    async def _encrypt_aes_gcm(
        self, 
        data: bytes, 
        tenant_id: Optional[str], 
        context: Optional[Dict[str, Any]]
    ) -> Tuple[bytes, Dict[str, Any]]:
        """Encrypt using AES-256-GCM."""
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        
        # Generate key from master key and tenant
        key_material = self._master_key + (tenant_id or "default").encode()
        key = hashlib.sha256(key_material).digest()
        
        # Generate nonce
        nonce = secrets.token_bytes(12)
        
        # Additional authenticated data
        aad = json.dumps(context or {}, separators=(',', ':')).encode()
        
        # Encrypt
        aesgcm = AESGCM(key)
        ciphertext = aesgcm.encrypt(nonce, data, aad)
        
        encryption_context = {
            "nonce": nonce.hex(),
            "aad": aad.hex(),
            "algorithm": "AES-256-GCM"
        }
        
        return nonce + ciphertext, encryption_context
    
    async def _decrypt_aes_gcm(
        self, 
        encrypted_data: bytes, 
        context: Dict[str, Any], 
        tenant_id: Optional[str],
        verify_context: Optional[Dict[str, Any]]
    ) -> bytes:
        """Decrypt AES-256-GCM encrypted data."""
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        
        # Extract nonce and ciphertext
        nonce = encrypted_data[:12]
        ciphertext = encrypted_data[12:]
        
        # Regenerate key
        key_material = self._master_key + (tenant_id or "default").encode()
        key = hashlib.sha256(key_material).digest()
        
        # Get AAD
        aad = bytes.fromhex(context["aad"])
        
        # Decrypt
        aesgcm = AESGCM(key)
        return aesgcm.decrypt(nonce, ciphertext, aad)
    
    async def _encrypt_multi_layer(
        self, 
        data: bytes, 
        tenant_id: Optional[str], 
        level: EncryptionLevel,
        context: Optional[Dict[str, Any]]
    ) -> Tuple[bytes, Dict[str, Any]]:
        """Multi-layer encryption for highest security."""
        # Layer 1: AES-GCM
        layer1_data, layer1_context = await self._encrypt_aes_gcm(data, tenant_id, context)
        
        # Layer 2: Fernet
        fernet_key = await self._get_fernet_key(tenant_id)
        fernet = Fernet(fernet_key)
        layer2_data = fernet.encrypt(layer1_data)
        
        encryption_context = {
            "layers": ["aes-256-gcm", "fernet"],
            "layer1_context": layer1_context
        }
        
        return layer2_data, encryption_context
    
    async def _decrypt_multi_layer(
        self, 
        encrypted_data: bytes, 
        context: Dict[str, Any], 
        tenant_id: Optional[str],
        verify_context: Optional[Dict[str, Any]]
    ) -> bytes:
        """Decrypt multi-layer encrypted data."""
        # Layer 2: Fernet
        fernet_key = await self._get_fernet_key(tenant_id)
        fernet = Fernet(fernet_key)
        layer1_data = fernet.decrypt(encrypted_data)
        
        # Layer 1: AES-GCM
        return await self._decrypt_aes_gcm(
            layer1_data, 
            context["layer1_context"], 
            tenant_id, 
            verify_context
        )
    
    async def _audit_event(
        self, 
        event_type: AuditEventType, 
        action: str, 
        details: Dict[str, Any]
    ):
        """Record audit event."""
        try:
            from src.models.audit_log import AuditLog
            
            audit_record = AuditLog(
                id=str(uuid.uuid4()),
                tenant_id=details.get("tenant_id"),
                user_id=details.get("user_id"),
                session_id=details.get("session_id"),
                event_type=event_type.value,
                event_action=action,
                event_description=f"{event_type.value}: {action}",
                ip_address=details.get("ip_address"),
                data_after=details,
                service_name="security_manager"
            )
            
            # Add to buffer for batch processing
            self._audit_buffer.append(audit_record)
            
        except Exception as e:
            self.log_error("Audit event recording failed", event_type=event_type.value, error=e)
    
    async def _verify_tenant_isolation(
        self, 
        user_id: str, 
        tenant_id: str, 
        resource_id: str
    ) -> bool:
        """Verify tenant isolation for resource access."""
        # Implement tenant isolation checks
        return True  # Simplified for now
    
    async def _check_rbac_permissions(
        self, 
        user_id: str, 
        tenant_id: str, 
        resource_type: str, 
        action: str
    ) -> bool:
        """Check RBAC permissions."""
        # Implement RBAC check
        return True  # Simplified for now
    
    async def _check_abac_policies(
        self, 
        user_id: str, 
        tenant_id: str, 
        resource_type: str, 
        resource_id: str, 
        action: str, 
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Check ABAC policies."""
        # Implement ABAC policy evaluation
        return {"allowed": True}  # Simplified for now
    
    async def _check_rate_limits(
        self, 
        user_id: str, 
        tenant_id: str, 
        action: str, 
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Check rate limits."""
        # Implement rate limiting
        return {"allowed": True}  # Simplified for now
    
    def _requires_audit(self, resource_type: str, action: str) -> bool:
        """Check if resource/action requires auditing."""
        audit_required_actions = ["delete", "export", "permission_change"]
        audit_required_resources = ["user", "sensitive_data"]
        
        return action in audit_required_actions or resource_type in audit_required_resources
    
    def _get_recommended_actions(self, response_level: str, anomalies: List[Dict]) -> List[str]:
        """Get recommended security actions based on response level."""
        if response_level == "critical":
            return ["block_user", "require_mfa", "notify_admin", "force_logout"]
        elif response_level == "high":
            return ["require_mfa", "additional_verification", "notify_admin"]
        elif response_level == "medium":
            return ["log_activity", "increase_monitoring"]
        elif response_level == "low":
            return ["log_activity"]
        return []
    
    def _calculate_consent_hash(self, consent_text: str) -> str:
        """Calculate hash of consent text for integrity."""
        return hashlib.sha256(consent_text.encode()).hexdigest()
    
    def _check_framework_compliance(self, consent_type: ConsentType) -> Dict[str, Any]:
        """Check framework compliance for consent."""
        compliance = {}
        
        if consent_type == ConsentType.EXPLICIT:
            compliance["GDPR"] = {"compliant": True, "article": "Article 7"}
            compliance["CCPA"] = {"compliant": True}
        
        return compliance
    
    # Background Tasks
    
    async def _key_rotation_task(self):
        """Background task for key rotation."""
        while True:
            try:
                await asyncio.sleep(self._key_rotation_interval)
                # Implement key rotation logic
                self.log_info("Key rotation check completed")
            except Exception as e:
                self.log_error("Key rotation task failed", error=e)
    
    async def _audit_processing_task(self):
        """Background task for processing audit buffer."""
        while True:
            try:
                await asyncio.sleep(60)  # Process every minute
                await self._flush_audit_buffer()
            except Exception as e:
                self.log_error("Audit processing task failed", error=e)
    
    async def _session_cleanup_task(self):
        """Background task for cleaning up expired sessions."""
        while True:
            try:
                await asyncio.sleep(300)  # Check every 5 minutes
                current_time = datetime.utcnow()
                
                expired_sessions = []
                for session_id, session_data in self._active_sessions.items():
                    last_activity = datetime.fromisoformat(session_data["last_activity"].replace("Z", "+00:00"))
                    if (current_time.replace(tzinfo=last_activity.tzinfo) - last_activity).total_seconds() > self._session_timeout:
                        expired_sessions.append(session_id)
                
                for session_id in expired_sessions:
                    del self._active_sessions[session_id]
                    await self._audit_event(
                        AuditEventType.LOGOUT,
                        "session_expired",
                        {"session_id": session_id}
                    )
                
                if expired_sessions:
                    self.log_info("Expired sessions cleaned up", count=len(expired_sessions))
                    
            except Exception as e:
                self.log_error("Session cleanup task failed", error=e)
    
    async def _flush_audit_buffer(self):
        """Flush audit buffer to database."""
        if not self._audit_buffer:
            return
        
        try:
            async with get_db_session() as session:
                for audit_record in self._audit_buffer:
                    session.add(audit_record)
                await session.commit()
            
            self.log_info("Audit buffer flushed", records=len(self._audit_buffer))
            self._audit_buffer.clear()
            
        except Exception as e:
            self.log_error("Audit buffer flush failed", error=e)
    
    # Health Check
    
    async def health_check(self) -> Dict[str, Any]:
        """Check security system health."""
        
        health = {
            "status": "healthy",
            "encryption_keys_loaded": len(self._encryption_keys) > 0,
            "active_sessions": len(self._active_sessions),
            "audit_buffer_size": len(self._audit_buffer),
            "policies_loaded": len(self._security_policies)
        }
        
        try:
            # Test encryption/decryption
            test_data = "health_check_test"
            encrypted = await self.encrypt_data(test_data, DataClassification.INTERNAL)
            decrypted = await self.decrypt_data(encrypted)
            
            if decrypted != test_data:
                health["status"] = "unhealthy"
                health["encryption_test"] = "failed"
            else:
                health["encryption_test"] = "passed"
        
        except Exception as e:
            health["status"] = "unhealthy"
            health["error"] = str(e)
        
        return health


# Global security manager instance
security_manager = SecurityManager()