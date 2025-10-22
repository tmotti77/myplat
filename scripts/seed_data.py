"""Seed the database with initial data for development and testing."""

import asyncio
import uuid
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext
import os
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from core.config import settings
from models.user import User, UserRole
from models.tenant import Tenant, TenantPlan

# Password hashing
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


async def create_seed_data():
    """Create initial seed data."""
    print("Creating seed data...")
    
    # Create database engine
    engine = create_async_engine(
        str(settings.DATABASE_URL),
        echo=True
    )
    
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        try:
            # Create default tenant
            default_tenant = Tenant(
                id=str(uuid.uuid4()),
                name="Default Organization",
                domain="default.example.com",
                plan=TenantPlan.PRO,
                is_active=True,
                settings={
                    "max_documents": 10000,
                    "max_users": 100,
                    "features": {
                        "advanced_analytics": True,
                        "real_time_updates": True,
                        "expert_system": True
                    }
                }
            )
            session.add(default_tenant)
            await session.flush()
            
            # Create demo tenant
            demo_tenant = Tenant(
                id=str(uuid.uuid4()),
                name="Demo Company",
                domain="demo.example.com",
                plan=TenantPlan.BASIC,
                is_active=True,
                settings={
                    "max_documents": 1000,
                    "max_users": 10,
                    "features": {
                        "advanced_analytics": False,
                        "real_time_updates": True,
                        "expert_system": False
                    }
                }
            )
            session.add(demo_tenant)
            await session.flush()
            
            # Create admin user for default tenant
            admin_user = User(
                id=str(uuid.uuid4()),
                email="admin@example.com",
                username="admin",
                hashed_password=pwd_context.hash("admin123!"),
                full_name="System Administrator",
                role=UserRole.ADMIN,
                is_active=True,
                is_verified=True,
                tenant_id=default_tenant.id,
                preferences={
                    "theme": "dark",
                    "language": "en",
                    "notifications": {
                        "email": True,
                        "push": True,
                        "document_processing": True,
                        "system_alerts": True
                    },
                    "dashboard": {
                        "show_recent_documents": True,
                        "show_analytics": True,
                        "default_search_type": "hybrid"
                    }
                }
            )
            session.add(admin_user)
            
            # Create regular user for default tenant
            user1 = User(
                id=str(uuid.uuid4()),
                email="user@example.com",
                username="user",
                hashed_password=pwd_context.hash("user123!"),
                full_name="John Doe",
                role=UserRole.USER,
                is_active=True,
                is_verified=True,
                tenant_id=default_tenant.id,
                preferences={
                    "theme": "light",
                    "language": "en",
                    "notifications": {
                        "email": True,
                        "push": False,
                        "document_processing": True,
                        "system_alerts": False
                    },
                    "dashboard": {
                        "show_recent_documents": True,
                        "show_analytics": False,
                        "default_search_type": "semantic"
                    }
                }
            )
            session.add(user1)
            
            # Create another regular user for default tenant
            user2 = User(
                id=str(uuid.uuid4()),
                email="jane@example.com",
                username="jane",
                hashed_password=pwd_context.hash("jane123!"),
                full_name="Jane Smith",
                role=UserRole.USER,
                is_active=True,
                is_verified=True,
                tenant_id=default_tenant.id,
                preferences={
                    "theme": "dark",
                    "language": "en",
                    "notifications": {
                        "email": True,
                        "push": True,
                        "document_processing": True,
                        "system_alerts": False
                    },
                    "dashboard": {
                        "show_recent_documents": True,
                        "show_analytics": True,
                        "default_search_type": "hybrid"
                    }
                }
            )
            session.add(user2)
            
            # Create demo user for demo tenant
            demo_user = User(
                id=str(uuid.uuid4()),
                email="demo@example.com",
                username="demo",
                hashed_password=pwd_context.hash("demo123!"),
                full_name="Demo User",
                role=UserRole.USER,
                is_active=True,
                is_verified=True,
                tenant_id=demo_tenant.id,
                preferences={
                    "theme": "light",
                    "language": "en",
                    "notifications": {
                        "email": True,
                        "push": False,
                        "document_processing": True,
                        "system_alerts": False
                    },
                    "dashboard": {
                        "show_recent_documents": True,
                        "show_analytics": False,
                        "default_search_type": "keyword"
                    }
                }
            )
            session.add(demo_user)
            
            # Create super admin (cross-tenant)
            super_admin = User(
                id=str(uuid.uuid4()),
                email="superadmin@example.com",
                username="superadmin",
                hashed_password=pwd_context.hash("superadmin123!"),
                full_name="Super Administrator",
                role=UserRole.SUPER_ADMIN,
                is_active=True,
                is_verified=True,
                tenant_id=default_tenant.id,
                preferences={
                    "theme": "dark",
                    "language": "en",
                    "notifications": {
                        "email": True,
                        "push": True,
                        "document_processing": True,
                        "system_alerts": True
                    },
                    "dashboard": {
                        "show_recent_documents": True,
                        "show_analytics": True,
                        "show_system_stats": True,
                        "default_search_type": "hybrid"
                    }
                }
            )
            session.add(super_admin)
            
            await session.commit()
            
            print("✅ Seed data created successfully!")
            print("\n📊 Created:")
            print(f"   • 2 tenants ({default_tenant.name}, {demo_tenant.name})")
            print(f"   • 5 users (admin, user, jane, demo, superadmin)")
            print("\n🔑 Login credentials:")
            print("   Admin: admin@example.com / admin123!")
            print("   User: user@example.com / user123!")
            print("   Jane: jane@example.com / jane123!")
            print("   Demo: demo@example.com / demo123!")
            print("   Super Admin: superadmin@example.com / superadmin123!")
            
        except Exception as e:
            print(f"❌ Error creating seed data: {e}")
            await session.rollback()
            raise
        finally:
            await engine.dispose()


async def create_sample_documents_metadata():
    """Create some sample document metadata for testing (without actual files)."""
    print("\nCreating sample document metadata...")
    
    engine = create_async_engine(
        str(settings.DATABASE_URL),
        echo=False
    )
    
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        try:
            # Get users
            from sqlalchemy import select
            result = await session.execute(select(User))
            users = result.scalars().all()
            
            if not users:
                print("No users found, skipping sample documents")
                return
            
            # Sample documents for different users
            from models.document import Document, DocumentStatus
            
            sample_docs = [
                {
                    "title": "Company Handbook 2024",
                    "filename": "handbook_2024.pdf",
                    "category": "HR",
                    "tags": ["handbook", "policies", "hr"],
                    "description": "Complete employee handbook with policies and procedures",
                    "file_size": 2048576,  # ~2MB
                    "language": "en",
                    "status": DocumentStatus.PROCESSED,
                    "processed_chunks": 45,
                    "total_chunks": 45
                },
                {
                    "title": "Product Specification Document",
                    "filename": "product_spec_v2.docx",
                    "category": "Product",
                    "tags": ["product", "specification", "requirements"],
                    "description": "Detailed product requirements and specifications",
                    "file_size": 1024000,  # ~1MB
                    "language": "en",
                    "status": DocumentStatus.PROCESSED,
                    "processed_chunks": 28,
                    "total_chunks": 28
                },
                {
                    "title": "Financial Report Q3 2024",
                    "filename": "q3_2024_financial.pdf",
                    "category": "Finance",
                    "tags": ["finance", "report", "quarterly"],
                    "description": "Third quarter financial performance report",
                    "file_size": 3145728,  # ~3MB
                    "language": "en",
                    "status": DocumentStatus.PROCESSED,
                    "processed_chunks": 67,
                    "total_chunks": 67
                },
                {
                    "title": "API Documentation",
                    "filename": "api_docs.md",
                    "category": "Technical",
                    "tags": ["api", "documentation", "development"],
                    "description": "Complete API documentation with examples",
                    "file_size": 512000,  # ~512KB
                    "language": "en",
                    "status": DocumentStatus.PROCESSED,
                    "processed_chunks": 15,
                    "total_chunks": 15
                },
                {
                    "title": "Marketing Strategy 2025",
                    "filename": "marketing_strategy_2025.pptx",
                    "category": "Marketing",
                    "tags": ["marketing", "strategy", "planning"],
                    "description": "Marketing strategy and campaign planning for 2025",
                    "file_size": 4194304,  # ~4MB
                    "language": "en",
                    "status": DocumentStatus.PROCESSING,
                    "processed_chunks": 12,
                    "total_chunks": 34
                }
            ]
            
            # Create documents for different users
            for i, doc_data in enumerate(sample_docs):
                user = users[i % len(users)]
                
                document = Document(
                    id=str(uuid.uuid4()),
                    title=doc_data["title"],
                    filename=doc_data["filename"],
                    file_path=f"documents/{user.tenant_id}/{uuid.uuid4()}/{doc_data['filename']}",
                    storage_url=f"https://storage.example.com/documents/{uuid.uuid4()}",
                    file_size=doc_data["file_size"],
                    file_type="application/pdf" if doc_data["filename"].endswith(".pdf") else 
                              "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    status=doc_data["status"],
                    language=doc_data["language"],
                    category=doc_data["category"],
                    tags=doc_data["tags"],
                    description=doc_data["description"],
                    processed_chunks=doc_data["processed_chunks"],
                    total_chunks=doc_data["total_chunks"],
                    tenant_id=user.tenant_id,
                    user_id=user.id,
                    processing_options={}
                )
                session.add(document)
            
            await session.commit()
            print(f"✅ Created {len(sample_docs)} sample documents")
            
        except Exception as e:
            print(f"❌ Error creating sample documents: {e}")
            await session.rollback()
            raise
        finally:
            await engine.dispose()


def print_usage():
    """Print usage instructions."""
    print("\n🚀 Hybrid RAG Platform - Database Seeder")
    print("=" * 50)
    print("\n📝 This script creates initial data for development and testing:")
    print("   • Default tenant and demo tenant")
    print("   • Admin and regular users")
    print("   • Sample document metadata")
    print("\n⚠️  Make sure to:")
    print("   1. Run database migrations first: alembic upgrade head")
    print("   2. Set up your .env file with DATABASE_URL")
    print("   3. Have PostgreSQL running with required extensions")
    print("\n🔧 Usage:")
    print("   python scripts/seed_data.py")
    print()


async def main():
    """Main function to run all seed data creation."""
    try:
        print_usage()
        
        # Check if database URL is configured
        if not settings.DATABASE_URL:
            print("❌ DATABASE_URL not configured. Please set it in your .env file.")
            return
        
        # Confirm before proceeding
        response = input("Do you want to proceed with seeding the database? (y/N): ")
        if response.lower() != 'y':
            print("Aborted.")
            return
        
        # Create seed data
        await create_seed_data()
        await create_sample_documents_metadata()
        
        print("\n🎉 Database seeding completed successfully!")
        print("\n🌐 You can now start the application and login with the created users.")
        
    except Exception as e:
        print(f"\n❌ Seeding failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())