"""Audit log model for security and compliance tracking."""
from enum import Enum
from sqlalchemy import Column, String, JSON, Float, Boolean, Index, Text

from src.models.base import BaseModel


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
    ENCRYPTION_EVENT = "encryption_event"
    AUTHENTICATION_EVENT = "authentication_event"
    AUTHORIZATION_EVENT = "authorization_event"


class AuditSeverity(str, Enum):
    """Severity levels for audit events."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AuditLog(BaseModel):
    """Model for audit logging and compliance tracking."""
    
    __tablename__ = "audit_logs"
    
    # Core identification
    tenant_id = Column(String, nullable=False, index=True)
    user_id = Column(String, nullable=True, index=True)
    session_id = Column(String, nullable=True, index=True)
    
    # Event details
    event_type = Column(String, nullable=False, index=True)
    event_action = Column(String, nullable=False, index=True)
    event_description = Column(Text, nullable=True)
    
    # Resource information
    resource_type = Column(String, nullable=True, index=True)
    resource_id = Column(String, nullable=True, index=True)
    resource_name = Column(String, nullable=True)
    
    # Security context
    ip_address = Column(String, nullable=True, index=True)
    user_agent = Column(Text, nullable=True)
    location = Column(String, nullable=True)
    
    # Event metadata
    severity = Column(String, default=AuditSeverity.LOW.value, index=True)
    success = Column(Boolean, default=True, index=True)
    error_message = Column(Text, nullable=True)
    
    # Data context
    data_before = Column(JSON, nullable=True)
    data_after = Column(JSON, nullable=True)
    data_changes = Column(JSON, nullable=True)
    
    # Performance metrics
    duration_ms = Column(Float, nullable=True)
    request_size_bytes = Column(Float, nullable=True)
    response_size_bytes = Column(Float, nullable=True)
    
    # Compliance and legal
    compliance_tags = Column(JSON, default=[])
    retention_period_days = Column(Float, default=2555)  # 7 years default
    legal_hold = Column(Boolean, default=False, index=True)
    
    # Risk assessment
    risk_score = Column(Float, default=0.0, index=True)
    risk_factors = Column(JSON, default=[])
    anomaly_detected = Column(Boolean, default=False, index=True)
    
    # Investigation and response
    investigated = Column(Boolean, default=False, index=True)
    investigation_notes = Column(Text, nullable=True)
    incident_id = Column(String, nullable=True, index=True)
    response_taken = Column(Text, nullable=True)
    
    # Additional context
    correlation_id = Column(String, nullable=True, index=True)
    trace_id = Column(String, nullable=True, index=True)
    request_id = Column(String, nullable=True, index=True)
    
    # System information
    service_name = Column(String, nullable=True, index=True)
    service_version = Column(String, nullable=True)
    environment = Column(String, nullable=True, index=True)
    
    # Data classification
    data_classification = Column(String, nullable=True, index=True)
    contains_pii = Column(Boolean, default=False, index=True)
    contains_phi = Column(Boolean, default=False, index=True)
    
    # Performance indexes
    __table_args__ = (
        Index('idx_audit_tenant_event_time', 'tenant_id', 'event_type', 'created_at'),
        Index('idx_audit_user_time', 'user_id', 'created_at'),
        Index('idx_audit_resource_type_action', 'resource_type', 'event_action'),
        Index('idx_audit_security_events', 'event_type', 'severity', 'success'),
        Index('idx_audit_risk_anomaly', 'risk_score', 'anomaly_detected'),
        Index('idx_audit_compliance', 'compliance_tags', 'legal_hold'),
        Index('idx_audit_investigation', 'investigated', 'incident_id'),
        Index('idx_audit_ip_time', 'ip_address', 'created_at'),
        Index('idx_audit_correlation', 'correlation_id', 'trace_id'),
    )
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    def mark_investigated(self, notes: str, incident_id: str = None):
        """Mark audit log as investigated."""
        self.investigated = True
        self.investigation_notes = notes
        if incident_id:
            self.incident_id = incident_id
    
    def add_compliance_tag(self, tag: str):
        """Add a compliance tag."""
        if not self.compliance_tags:
            self.compliance_tags = []
        if tag not in self.compliance_tags:
            self.compliance_tags.append(tag)
    
    def set_legal_hold(self, hold: bool = True):
        """Set or remove legal hold."""
        self.legal_hold = hold
        if hold:
            self.add_compliance_tag("legal_hold")
    
    def calculate_risk_score(self) -> float:
        """Calculate risk score based on event characteristics."""
        score = 0.0
        
        # Base score by event type
        high_risk_events = {
            AuditEventType.SECURITY_VIOLATION.value: 0.8,
            AuditEventType.DATA_BREACH.value: 1.0,
            AuditEventType.PERMISSION_CHANGE.value: 0.6,
            AuditEventType.DELETE.value: 0.4,
            AuditEventType.EXPORT.value: 0.5
        }
        
        score += high_risk_events.get(self.event_type, 0.1)
        
        # Severity multiplier
        severity_multipliers = {
            AuditSeverity.LOW.value: 1.0,
            AuditSeverity.MEDIUM.value: 1.5,
            AuditSeverity.HIGH.value: 2.0,
            AuditSeverity.CRITICAL.value: 3.0
        }
        
        score *= severity_multipliers.get(self.severity, 1.0)
        
        # Failure increases risk
        if not self.success:
            score *= 1.5
        
        # PII/PHI data increases risk
        if self.contains_pii or self.contains_phi:
            score *= 1.3
        
        # Anomaly detection increases risk
        if self.anomaly_detected:
            score *= 1.4
        
        # Risk factors
        if self.risk_factors:
            score += len(self.risk_factors) * 0.1
        
        self.risk_score = min(1.0, score)
        return self.risk_score
    
    def should_alert(self) -> bool:
        """Determine if this audit event should trigger an alert."""
        return (
            self.severity in [AuditSeverity.HIGH.value, AuditSeverity.CRITICAL.value] or
            self.event_type in [
                AuditEventType.SECURITY_VIOLATION.value,
                AuditEventType.DATA_BREACH.value
            ] or
            self.risk_score >= 0.7 or
            self.anomaly_detected
        )
    
    def is_security_event(self) -> bool:
        """Check if this is a security-related event."""
        security_events = {
            AuditEventType.LOGIN.value,
            AuditEventType.LOGOUT.value,
            AuditEventType.PERMISSION_CHANGE.value,
            AuditEventType.SECURITY_VIOLATION.value,
            AuditEventType.DATA_BREACH.value,
            AuditEventType.AUTHENTICATION_EVENT.value,
            AuditEventType.AUTHORIZATION_EVENT.value
        }
        return self.event_type in security_events
    
    def is_compliance_relevant(self) -> bool:
        """Check if this event is relevant for compliance."""
        return (
            self.contains_pii or
            self.contains_phi or
            bool(self.compliance_tags) or
            self.legal_hold or
            self.event_type == AuditEventType.COMPLIANCE_EVENT.value
        )
    
    def get_retention_date(self):
        """Get the retention date for this audit log."""
        from datetime import datetime, timedelta
        
        if self.legal_hold:
            return None  # Indefinite retention
        
        created_date = datetime.fromisoformat(self.created_at.replace("Z", "+00:00"))
        return created_date + timedelta(days=self.retention_period_days)
    
    def to_summary(self) -> dict:
        """Create a summary representation for reporting."""
        return {
            "id": self.id,
            "timestamp": self.created_at,
            "event_type": self.event_type,
            "event_action": self.event_action,
            "user_id": self.user_id,
            "tenant_id": self.tenant_id,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "severity": self.severity,
            "success": self.success,
            "risk_score": self.risk_score,
            "ip_address": self.ip_address,
            "anomaly_detected": self.anomaly_detected,
            "investigated": self.investigated
        }
    
    def __repr__(self) -> str:
        return f"<AuditLog(event={self.event_type}, action={self.event_action}, user={self.user_id})>"