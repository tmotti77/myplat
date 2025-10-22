"""Initial migration - Create all base tables

Revision ID: 001
Revises: 
Create Date: 2024-10-13 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid


# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create initial database schema."""
    
    # Create UUID extension
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "vector"')
    
    # Create enums
    op.execute("""
        CREATE TYPE userrole AS ENUM ('USER', 'ADMIN', 'SUPER_ADMIN')
    """)
    
    op.execute("""
        CREATE TYPE tenantplan AS ENUM ('BASIC', 'PRO', 'ENTERPRISE')
    """)
    
    op.execute("""
        CREATE TYPE documentstatus AS ENUM ('UPLOADING', 'PROCESSING', 'PROCESSED', 'FAILED', 'ARCHIVED')
    """)
    
    op.execute("""
        CREATE TYPE conversationstatus AS ENUM ('ACTIVE', 'ARCHIVED', 'DELETED')
    """)
    
    op.execute("""
        CREATE TYPE messagerole AS ENUM ('USER', 'ASSISTANT', 'SYSTEM')
    """)
    
    op.execute("""
        CREATE TYPE messagetype AS ENUM ('TEXT', 'IMAGE', 'FILE', 'SYSTEM')
    """)
    
    op.execute("""
        CREATE TYPE auditaction AS ENUM (
            'CREATE', 'READ', 'UPDATE', 'DELETE', 
            'LOGIN', 'LOGOUT', 'PASSWORD_CHANGE', 
            'DOCUMENT_UPLOAD', 'DOCUMENT_DELETE', 
            'SEARCH_QUERY', 'CHAT_MESSAGE'
        )
    """)
    
    # Create tenants table
    op.create_table(
        'tenants',
        sa.Column('id', sa.String(36), primary_key=True, default=lambda: str(uuid.uuid4())),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('domain', sa.String(100), nullable=False, unique=True),
        sa.Column('plan', postgresql.ENUM('BASIC', 'PRO', 'ENTERPRISE', name='tenantplan'), 
                  nullable=False, default='BASIC'),
        sa.Column('is_active', sa.Boolean, nullable=False, default=True),
        sa.Column('settings', sa.JSON, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), 
                  onupdate=sa.func.now())
    )
    
    op.create_index('ix_tenants_name', 'tenants', ['name'])
    op.create_index('ix_tenants_domain', 'tenants', ['domain'])
    op.create_index('ix_tenants_is_active', 'tenants', ['is_active'])
    
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.String(36), primary_key=True, default=lambda: str(uuid.uuid4())),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('username', sa.String(50), nullable=False),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(100), nullable=False),
        sa.Column('role', postgresql.ENUM('USER', 'ADMIN', 'SUPER_ADMIN', name='userrole'), 
                  nullable=False, default='USER'),
        sa.Column('is_active', sa.Boolean, nullable=False, default=True),
        sa.Column('is_verified', sa.Boolean, nullable=False, default=False),
        sa.Column('tenant_id', sa.String(36), sa.ForeignKey('tenants.id', ondelete='CASCADE'), 
                  nullable=False),
        sa.Column('preferences', sa.JSON, nullable=True),
        sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), 
                  onupdate=sa.func.now())
    )
    
    op.create_index('ix_users_email', 'users', ['email'])
    op.create_index('ix_users_username', 'users', ['username'])
    op.create_index('ix_users_tenant_id', 'users', ['tenant_id'])
    op.create_index('ix_users_role', 'users', ['role'])
    op.create_index('ix_users_is_active', 'users', ['is_active'])
    op.create_unique_constraint('uq_users_email_tenant', 'users', ['email', 'tenant_id'])
    op.create_unique_constraint('uq_users_username_tenant', 'users', ['username', 'tenant_id'])
    
    # Create documents table
    op.create_table(
        'documents',
        sa.Column('id', sa.String(36), primary_key=True, default=lambda: str(uuid.uuid4())),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('filename', sa.String(255), nullable=False),
        sa.Column('file_path', sa.String(500), nullable=False),
        sa.Column('storage_url', sa.String(500), nullable=True),
        sa.Column('file_size', sa.BigInteger, nullable=False),
        sa.Column('file_type', sa.String(100), nullable=True),
        sa.Column('status', postgresql.ENUM(
            'UPLOADING', 'PROCESSING', 'PROCESSED', 'FAILED', 'ARCHIVED', 
            name='documentstatus'
        ), nullable=False, default='UPLOADING'),
        sa.Column('language', sa.String(10), nullable=False, default='en'),
        sa.Column('category', sa.String(100), nullable=True),
        sa.Column('tags', sa.JSON, nullable=True),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('processed_chunks', sa.Integer, nullable=False, default=0),
        sa.Column('total_chunks', sa.Integer, nullable=False, default=0),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('processing_options', sa.JSON, nullable=True),
        sa.Column('tenant_id', sa.String(36), sa.ForeignKey('tenants.id', ondelete='CASCADE'), 
                  nullable=False),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), 
                  nullable=False),
        sa.Column('upload_date', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('last_updated', sa.DateTime(timezone=True), server_default=sa.func.now(), 
                  onupdate=sa.func.now())
    )
    
    op.create_index('ix_documents_title', 'documents', ['title'])
    op.create_index('ix_documents_status', 'documents', ['status'])
    op.create_index('ix_documents_tenant_id', 'documents', ['tenant_id'])
    op.create_index('ix_documents_user_id', 'documents', ['user_id'])
    op.create_index('ix_documents_category', 'documents', ['category'])
    op.create_index('ix_documents_language', 'documents', ['language'])
    op.create_index('ix_documents_upload_date', 'documents', ['upload_date'])
    
    # Create chunks table
    op.create_table(
        'chunks',
        sa.Column('id', sa.String(36), primary_key=True, default=lambda: str(uuid.uuid4())),
        sa.Column('document_id', sa.String(36), sa.ForeignKey('documents.id', ondelete='CASCADE'), 
                  nullable=False),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('chunk_index', sa.Integer, nullable=False),
        sa.Column('start_offset', sa.Integer, nullable=True),
        sa.Column('end_offset', sa.Integer, nullable=True),
        sa.Column('metadata', sa.JSON, nullable=True),
        sa.Column('embedding_id', sa.String(36), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now())
    )
    
    op.create_index('ix_chunks_document_id', 'chunks', ['document_id'])
    op.create_index('ix_chunks_chunk_index', 'chunks', ['chunk_index'])
    op.create_index('ix_chunks_embedding_id', 'chunks', ['embedding_id'])
    op.create_unique_constraint('uq_chunks_document_chunk', 'chunks', ['document_id', 'chunk_index'])
    
    # Create embeddings table
    op.create_table(
        'embeddings',
        sa.Column('id', sa.String(36), primary_key=True, default=lambda: str(uuid.uuid4())),
        sa.Column('chunk_id', sa.String(36), sa.ForeignKey('chunks.id', ondelete='CASCADE'), 
                  nullable=False, unique=True),
        sa.Column('model_name', sa.String(100), nullable=False),
        sa.Column('vector', postgresql.ARRAY(sa.Float), nullable=False),
        sa.Column('dimensions', sa.Integer, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now())
    )
    
    op.create_index('ix_embeddings_chunk_id', 'embeddings', ['chunk_id'])
    op.create_index('ix_embeddings_model_name', 'embeddings', ['model_name'])
    
    # Create conversations table
    op.create_table(
        'conversations',
        sa.Column('id', sa.String(36), primary_key=True, default=lambda: str(uuid.uuid4())),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('status', postgresql.ENUM('ACTIVE', 'ARCHIVED', 'DELETED', name='conversationstatus'), 
                  nullable=False, default='ACTIVE'),
        sa.Column('message_count', sa.Integer, nullable=False, default=0),
        sa.Column('context', sa.JSON, nullable=True),
        sa.Column('tenant_id', sa.String(36), sa.ForeignKey('tenants.id', ondelete='CASCADE'), 
                  nullable=False),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), 
                  nullable=False),
        sa.Column('last_message_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), 
                  onupdate=sa.func.now())
    )
    
    op.create_index('ix_conversations_tenant_id', 'conversations', ['tenant_id'])
    op.create_index('ix_conversations_user_id', 'conversations', ['user_id'])
    op.create_index('ix_conversations_status', 'conversations', ['status'])
    op.create_index('ix_conversations_updated_at', 'conversations', ['updated_at'])
    
    # Create messages table
    op.create_table(
        'messages',
        sa.Column('id', sa.String(36), primary_key=True, default=lambda: str(uuid.uuid4())),
        sa.Column('conversation_id', sa.String(36), sa.ForeignKey('conversations.id', ondelete='CASCADE'), 
                  nullable=False),
        sa.Column('role', postgresql.ENUM('USER', 'ASSISTANT', 'SYSTEM', name='messagerole'), 
                  nullable=False),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('message_type', postgresql.ENUM('TEXT', 'IMAGE', 'FILE', 'SYSTEM', name='messagetype'), 
                  nullable=False, default='TEXT'),
        sa.Column('context', sa.JSON, nullable=True),
        sa.Column('sources', sa.JSON, nullable=True),
        sa.Column('token_usage', sa.JSON, nullable=True),
        sa.Column('processing_time_ms', sa.Integer, nullable=True),
        sa.Column('tenant_id', sa.String(36), sa.ForeignKey('tenants.id', ondelete='CASCADE'), 
                  nullable=False),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), 
                  nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.func.now())
    )
    
    op.create_index('ix_messages_conversation_id', 'messages', ['conversation_id'])
    op.create_index('ix_messages_role', 'messages', ['role'])
    op.create_index('ix_messages_tenant_id', 'messages', ['tenant_id'])
    op.create_index('ix_messages_user_id', 'messages', ['user_id'])
    op.create_index('ix_messages_timestamp', 'messages', ['timestamp'])
    
    # Create audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.String(36), primary_key=True, default=lambda: str(uuid.uuid4())),
        sa.Column('action', postgresql.ENUM(
            'CREATE', 'READ', 'UPDATE', 'DELETE', 
            'LOGIN', 'LOGOUT', 'PASSWORD_CHANGE', 
            'DOCUMENT_UPLOAD', 'DOCUMENT_DELETE', 
            'SEARCH_QUERY', 'CHAT_MESSAGE',
            name='auditaction'
        ), nullable=False),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='SET NULL'), 
                  nullable=True),
        sa.Column('tenant_id', sa.String(36), sa.ForeignKey('tenants.id', ondelete='CASCADE'), 
                  nullable=True),
        sa.Column('resource_type', sa.String(50), nullable=True),
        sa.Column('resource_id', sa.String(36), nullable=True),
        sa.Column('details', sa.JSON, nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.Text, nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.func.now())
    )
    
    op.create_index('ix_audit_logs_action', 'audit_logs', ['action'])
    op.create_index('ix_audit_logs_user_id', 'audit_logs', ['user_id'])
    op.create_index('ix_audit_logs_tenant_id', 'audit_logs', ['tenant_id'])
    op.create_index('ix_audit_logs_timestamp', 'audit_logs', ['timestamp'])
    op.create_index('ix_audit_logs_resource', 'audit_logs', ['resource_type', 'resource_id'])
    
    # Create document_metadata table
    op.create_table(
        'document_metadata',
        sa.Column('id', sa.String(36), primary_key=True, default=lambda: str(uuid.uuid4())),
        sa.Column('document_id', sa.String(36), sa.ForeignKey('documents.id', ondelete='CASCADE'), 
                  nullable=False, unique=True),
        sa.Column('extracted_text_length', sa.Integer, nullable=True),
        sa.Column('page_count', sa.Integer, nullable=True),
        sa.Column('word_count', sa.Integer, nullable=True),
        sa.Column('character_count', sa.Integer, nullable=True),
        sa.Column('language_detected', sa.String(10), nullable=True),
        sa.Column('mime_type', sa.String(100), nullable=True),
        sa.Column('file_hash', sa.String(64), nullable=True),
        sa.Column('extraction_method', sa.String(50), nullable=True),
        sa.Column('processing_duration_ms', sa.Integer, nullable=True),
        sa.Column('custom_metadata', sa.JSON, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), 
                  onupdate=sa.func.now())
    )
    
    op.create_index('ix_document_metadata_document_id', 'document_metadata', ['document_id'])
    op.create_index('ix_document_metadata_file_hash', 'document_metadata', ['file_hash'])


def downgrade() -> None:
    """Drop all tables and extensions."""
    
    # Drop tables in reverse order
    op.drop_table('document_metadata')
    op.drop_table('audit_logs')
    op.drop_table('messages')
    op.drop_table('conversations')
    op.drop_table('embeddings')
    op.drop_table('chunks')
    op.drop_table('documents')
    op.drop_table('users')
    op.drop_table('tenants')
    
    # Drop enums
    op.execute("DROP TYPE IF EXISTS auditaction")
    op.execute("DROP TYPE IF EXISTS messagetype")
    op.execute("DROP TYPE IF EXISTS messagerole")
    op.execute("DROP TYPE IF EXISTS conversationstatus")
    op.execute("DROP TYPE IF EXISTS documentstatus")
    op.execute("DROP TYPE IF EXISTS tenantplan")
    op.execute("DROP TYPE IF EXISTS userrole")
    
    # Drop extensions (optional, may be used by other apps)
    # op.execute('DROP EXTENSION IF EXISTS "vector"')
    # op.execute('DROP EXTENSION IF EXISTS "uuid-ossp"')