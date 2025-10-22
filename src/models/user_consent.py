"""User consent model for privacy compliance."""
from enum import Enum
from sqlalchemy import Column, String, JSON, Boolean, Text, Index

from src.models.base import BaseModel


class ConsentType(str, Enum):
    """Types of consent for data processing."""
    EXPLICIT = "explicit"
    IMPLIED = "implied"
    LEGITIMATE_INTEREST = "legitimate_interest"
    CONTRACTUAL = "contractual"
    LEGAL_OBLIGATION = "legal_obligation"
    VITAL_INTERESTS = "vital_interests"


class ConsentStatus(str, Enum):
    """Consent status."""
    ACTIVE = "active"
    REVOKED = "revoked"
    EXPIRED = "expired"
    WITHDRAWN = "withdrawn"


class UserConsent(BaseModel):
    """Model for tracking user consent for data processing."""
    
    __tablename__ = "user_consents"
    
    # Core identification
    user_id = Column(String, nullable=False, index=True)
    tenant_id = Column(String, nullable=False, index=True)
    
    # Consent details
    consent_type = Column(String, nullable=False, index=True)
    consent_text = Column(Text, nullable=False)
    consent_hash = Column(String, nullable=False)  # Hash of consent text
    
    # Processing scope
    processing_purposes = Column(JSON, default=[])  # List of purposes
    data_categories = Column(JSON, default=[])     # List of data categories
    
    # Consent lifecycle
    granted_at = Column(String, nullable=False, index=True)
    expires_at = Column(String, nullable=True, index=True)
    revoked_at = Column(String, nullable=True, index=True)
    last_confirmed_at = Column(String, nullable=True)
    
    # Status and validity
    status = Column(String, default=ConsentStatus.ACTIVE.value, index=True)
    revoked = Column(Boolean, default=False, index=True)
    
    # Context information
    ip_address = Column(String, nullable=True, index=True)
    user_agent = Column(Text, nullable=True)
    location = Column(String, nullable=True)
    
    # Legal basis and compliance
    legal_basis = Column(String, nullable=True)
    framework_compliance = Column(JSON, default={})  # GDPR, CCPA, etc.
    withdrawal_method = Column(String, nullable=True)
    
    # Proof and evidence
    consent_evidence = Column(JSON, default={})
    digital_signature = Column(String, nullable=True)
    witness_info = Column(JSON, default={})
    
    # Renewal and updates
    parent_consent_id = Column(String, nullable=True, index=True)
    renewal_required = Column(Boolean, default=False)
    renewal_frequency_days = Column(String, nullable=True)
    
    # Granular permissions
    granular_permissions = Column(JSON, default={})
    opt_out_options = Column(JSON, default={})
    
    # Child consent (for minors)
    is_child_consent = Column(Boolean, default=False, index=True)
    child_age = Column(String, nullable=True)
    parental_consent_required = Column(Boolean, default=False)
    parental_consent_id = Column(String, nullable=True)
    
    # Performance indexes
    __table_args__ = (
        Index('idx_consent_user_tenant_active', 'user_id', 'tenant_id', 'status'),
        Index('idx_consent_purposes', 'processing_purposes'),
        Index('idx_consent_expiry', 'expires_at', 'status'),
        Index('idx_consent_type_granted', 'consent_type', 'granted_at'),
        Index('idx_consent_revoked_time', 'revoked', 'revoked_at'),
        Index('idx_consent_framework', 'framework_compliance'),
        Index('idx_consent_child', 'is_child_consent', 'parental_consent_required'),
    )
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    def revoke_consent(self, method: str = "user_request", reason: str = None):
        """Revoke the consent."""
        from datetime import datetime
        
        self.status = ConsentStatus.REVOKED.value
        self.revoked = True
        self.revoked_at = datetime.utcnow().isoformat() + "Z"
        self.withdrawal_method = method
        
        if reason:
            if not self.consent_evidence:
                self.consent_evidence = {}
            self.consent_evidence["revocation_reason"] = reason
    
    def is_valid(self) -> bool:
        """Check if consent is currently valid."""
        if self.revoked or self.status != ConsentStatus.ACTIVE.value:
            return False
        
        if self.expires_at:
            from datetime import datetime
            expires = datetime.fromisoformat(self.expires_at.replace("Z", "+00:00"))
            if datetime.utcnow().replace(tzinfo=expires.tzinfo) > expires:
                return False
        
        return True
    
    def covers_purpose(self, purpose: str) -> bool:
        """Check if consent covers a specific processing purpose."""
        return purpose in (self.processing_purposes or [])
    
    def covers_data_category(self, category: str) -> bool:
        """Check if consent covers a specific data category."""
        return category in (self.data_categories or [])
    
    def needs_renewal(self) -> bool:
        """Check if consent needs renewal."""
        if not self.renewal_frequency_days:
            return False
        
        from datetime import datetime, timedelta
        
        granted = datetime.fromisoformat(self.granted_at.replace("Z", "+00:00"))
        renewal_frequency = int(self.renewal_frequency_days)
        next_renewal = granted + timedelta(days=renewal_frequency)
        
        return datetime.utcnow().replace(tzinfo=granted.tzinfo) >= next_renewal
    
    def is_compliant_with_framework(self, framework: str) -> bool:
        """Check if consent is compliant with specific framework."""
        return self.framework_compliance.get(framework, {}).get("compliant", False)
    
    def get_withdrawal_instructions(self) -> dict:
        """Get instructions for withdrawing consent."""
        return {
            "methods": ["email", "account_settings", "support_ticket"],
            "email": "privacy@example.com",
            "account_url": "/account/privacy",
            "support_url": "/support/privacy",
            "processing_time": "30 days maximum",
            "effects": "We will stop processing your data for the specified purposes"
        }
    
    def to_privacy_record(self) -> dict:
        """Convert to privacy record for data subject access."""
        return {
            "consent_id": self.id,
            "granted_date": self.granted_at,
            "consent_type": self.consent_type,
            "purposes": self.processing_purposes,
            "data_categories": self.data_categories,
            "status": self.status,
            "expires_date": self.expires_at,
            "revoked": self.revoked,
            "revocation_date": self.revoked_at,
            "legal_basis": self.legal_basis,
            "withdrawal_method": self.withdrawal_method,
            "framework_compliance": self.framework_compliance
        }
    
    def __repr__(self) -> str:
        return f"<UserConsent(user={self.user_id}, type={self.consent_type}, status={self.status})>"