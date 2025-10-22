"""Data subject request model for privacy rights management."""
from enum import Enum
from sqlalchemy import Column, String, JSON, Boolean, Text, Float, Index

from src.models.base import BaseModel


class RequestType(str, Enum):
    """Types of data subject requests."""
    ACCESS = "access"                    # Right to access
    RECTIFICATION = "rectification"      # Right to rectification
    ERASURE = "erasure"                 # Right to erasure/be forgotten
    RESTRICT = "restrict"               # Right to restrict processing
    PORTABILITY = "portability"         # Right to data portability
    OBJECT = "object"                   # Right to object
    OPT_OUT = "opt_out"                 # CCPA opt-out
    DELETE = "delete"                   # CCPA deletion
    KNOW = "know"                       # CCPA right to know


class RequestStatus(str, Enum):
    """Status of data subject requests."""
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    IDENTITY_VERIFICATION = "identity_verification"
    PROCESSING = "processing"
    COMPLETED = "completed"
    REJECTED = "rejected"
    PARTIALLY_FULFILLED = "partially_fulfilled"
    APPEALED = "appealed"


class DataSubjectRequest(BaseModel):
    """Model for tracking data subject rights requests."""
    
    __tablename__ = "data_subject_requests"
    
    # Core identification
    user_id = Column(String, nullable=False, index=True)
    tenant_id = Column(String, nullable=False, index=True)
    
    # Request details
    request_type = Column(String, nullable=False, index=True)
    request_description = Column(Text, nullable=True)
    request_details = Column(JSON, default={})
    
    # Status and processing
    status = Column(String, default=RequestStatus.SUBMITTED.value, index=True)
    submission_method = Column(String, nullable=True)  # web, email, phone, etc.
    
    # Identity verification
    identity_verified = Column(Boolean, default=False, index=True)
    verification_method = Column(String, nullable=True)
    verification_documents = Column(JSON, default=[])
    
    # Processing timeline
    submitted_at = Column(String, nullable=False, index=True)
    acknowledged_at = Column(String, nullable=True)
    started_processing_at = Column(String, nullable=True)
    completed_at = Column(String, nullable=True)
    
    # Deadlines and SLA
    legal_deadline = Column(String, nullable=True, index=True)
    sla_deadline = Column(String, nullable=True)
    deadline_extended = Column(Boolean, default=False)
    extension_reason = Column(Text, nullable=True)
    
    # Processing results
    processing_result = Column(JSON, default={})
    data_affected = Column(JSON, default={})
    actions_taken = Column(JSON, default=[])
    
    # Fulfillment details
    data_export_url = Column(String, nullable=True)
    data_export_format = Column(String, nullable=True)  # JSON, XML, CSV
    data_export_size_bytes = Column(Float, nullable=True)
    
    # Records affected
    records_found = Column(String, nullable=True)
    records_processed = Column(String, nullable=True)
    records_deleted = Column(String, nullable=True)
    records_anonymized = Column(String, nullable=True)
    
    # Communication
    requester_email = Column(String, nullable=True)
    requester_phone = Column(String, nullable=True)
    preferred_communication = Column(String, nullable=True)
    
    # Staff assignment
    assigned_to = Column(String, nullable=True, index=True)
    assigned_team = Column(String, nullable=True)
    escalated = Column(Boolean, default=False)
    escalation_reason = Column(Text, nullable=True)
    
    # Quality and compliance
    quality_reviewed = Column(Boolean, default=False)
    quality_reviewer = Column(String, nullable=True)
    compliance_checked = Column(Boolean, default=False)
    compliance_notes = Column(Text, nullable=True)
    
    # Appeal and dispute
    appeal_submitted = Column(Boolean, default=False)
    appeal_reason = Column(Text, nullable=True)
    appeal_decision = Column(String, nullable=True)
    appeal_decided_at = Column(String, nullable=True)
    
    # Privacy impact
    privacy_risk_assessment = Column(JSON, default={})
    third_party_notifications = Column(JSON, default=[])
    data_processor_actions = Column(JSON, default=[])
    
    # Legal and regulatory
    legal_basis_review = Column(Text, nullable=True)
    regulatory_framework = Column(String, nullable=True)  # GDPR, CCPA, etc.
    legal_exception_applied = Column(String, nullable=True)
    
    # Automation and processing
    automated_processing = Column(Boolean, default=False)
    manual_review_required = Column(Boolean, default=False)
    processing_complexity = Column(String, nullable=True)  # simple, medium, complex
    
    # Costs and resources
    processing_cost_estimate = Column(Float, nullable=True)
    processing_time_hours = Column(Float, nullable=True)
    resources_used = Column(JSON, default={})
    
    # Additional context
    similar_requests = Column(JSON, default=[])
    related_incidents = Column(JSON, default=[])
    notes = Column(Text, nullable=True)
    
    # Performance indexes
    __table_args__ = (
        Index('idx_dsr_user_tenant_type', 'user_id', 'tenant_id', 'request_type'),
        Index('idx_dsr_status_deadline', 'status', 'legal_deadline'),
        Index('idx_dsr_submitted_type', 'submitted_at', 'request_type'),
        Index('idx_dsr_assigned_status', 'assigned_to', 'status'),
        Index('idx_dsr_verification', 'identity_verified', 'verification_method'),
        Index('idx_dsr_compliance', 'compliance_checked', 'regulatory_framework'),
        Index('idx_dsr_processing_time', 'started_processing_at', 'completed_at'),
    )
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    def acknowledge_request(self, acknowledger: str):
        """Acknowledge receipt of the request."""
        from datetime import datetime
        
        self.acknowledged_at = datetime.utcnow().isoformat() + "Z"
        self.assigned_to = acknowledger
        
        if self.status == RequestStatus.SUBMITTED.value:
            self.status = RequestStatus.UNDER_REVIEW.value
    
    def start_processing(self, processor: str):
        """Start processing the request."""
        from datetime import datetime
        
        self.started_processing_at = datetime.utcnow().isoformat() + "Z"
        self.status = RequestStatus.PROCESSING.value
        self.assigned_to = processor
    
    def complete_request(self, result: dict, processor: str = None):
        """Mark request as completed."""
        from datetime import datetime
        
        self.completed_at = datetime.utcnow().isoformat() + "Z"
        self.status = RequestStatus.COMPLETED.value
        self.processing_result = result
        
        if processor:
            self.assigned_to = processor
    
    def reject_request(self, reason: str, rejector: str = None):
        """Reject the request with reason."""
        from datetime import datetime
        
        self.completed_at = datetime.utcnow().isoformat() + "Z"
        self.status = RequestStatus.REJECTED.value
        self.processing_result = {
            "rejected": True,
            "reason": reason,
            "rejected_at": datetime.utcnow().isoformat() + "Z"
        }
        
        if rejector:
            self.assigned_to = rejector
    
    def verify_identity(self, method: str, documents: list = None):
        """Mark identity as verified."""
        self.identity_verified = True
        self.verification_method = method
        if documents:
            self.verification_documents = documents
    
    def escalate_request(self, reason: str, new_assignee: str = None):
        """Escalate the request."""
        self.escalated = True
        self.escalation_reason = reason
        if new_assignee:
            self.assigned_to = new_assignee
    
    def extend_deadline(self, new_deadline: str, reason: str):
        """Extend the processing deadline."""
        self.deadline_extended = True
        self.legal_deadline = new_deadline
        self.extension_reason = reason
    
    def is_overdue(self) -> bool:
        """Check if request is overdue."""
        if not self.legal_deadline:
            return False
        
        from datetime import datetime
        deadline = datetime.fromisoformat(self.legal_deadline.replace("Z", "+00:00"))
        return datetime.utcnow().replace(tzinfo=deadline.tzinfo) > deadline
    
    def get_processing_time_days(self) -> float:
        """Get processing time in days."""
        if not self.completed_at or not self.submitted_at:
            return 0.0
        
        from datetime import datetime
        submitted = datetime.fromisoformat(self.submitted_at.replace("Z", "+00:00"))
        completed = datetime.fromisoformat(self.completed_at.replace("Z", "+00:00"))
        
        return (completed - submitted).total_seconds() / 86400
    
    def calculate_compliance_score(self) -> float:
        """Calculate compliance score for this request."""
        score = 1.0
        
        # Deadline compliance
        if self.is_overdue():
            score -= 0.3
        
        # Quality review
        if not self.quality_reviewed:
            score -= 0.2
        
        # Identity verification for sensitive requests
        if self.request_type in ["access", "portability"] and not self.identity_verified:
            score -= 0.3
        
        # Compliance check
        if not self.compliance_checked:
            score -= 0.2
        
        return max(0.0, score)
    
    def get_sla_status(self) -> dict:
        """Get SLA status information."""
        from datetime import datetime
        
        submitted = datetime.fromisoformat(self.submitted_at.replace("Z", "+00:00"))
        now = datetime.utcnow().replace(tzinfo=submitted.tzinfo)
        
        # Standard SLA: 30 days for most requests, 1 month for complex
        sla_days = 30
        if self.processing_complexity == "complex":
            sla_days = 45
        
        sla_deadline = submitted.replace(hour=23, minute=59, second=59)
        from datetime import timedelta
        sla_deadline += timedelta(days=sla_days)
        
        days_remaining = (sla_deadline - now).days
        is_at_risk = days_remaining <= 5  # At risk if less than 5 days
        
        return {
            "sla_deadline": sla_deadline.isoformat() + "Z",
            "days_remaining": days_remaining,
            "is_overdue": days_remaining < 0,
            "is_at_risk": is_at_risk,
            "sla_met": self.completed_at and not self.is_overdue()
        }
    
    def to_summary(self) -> dict:
        """Create summary for reporting."""
        return {
            "request_id": self.id,
            "request_type": self.request_type,
            "status": self.status,
            "submitted_at": self.submitted_at,
            "user_id": self.user_id,
            "tenant_id": self.tenant_id,
            "identity_verified": self.identity_verified,
            "assigned_to": self.assigned_to,
            "processing_time_days": self.get_processing_time_days(),
            "is_overdue": self.is_overdue(),
            "compliance_score": self.calculate_compliance_score(),
            "sla_status": self.get_sla_status()
        }
    
    def __repr__(self) -> str:
        return f"<DataSubjectRequest(type={self.request_type}, status={self.status}, user={self.user_id})>"