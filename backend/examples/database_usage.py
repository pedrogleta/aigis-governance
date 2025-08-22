#!/usr/bin/env python3
"""
Example script demonstrating how to use the database connections.
"""

import sys
from pathlib import Path
from datetime import datetime


from sqlalchemy import text
from core.database import (
    get_sqlite_session_context,
    db_manager,
)

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))


def example_sqlite_operations():
    """Example of SQLite database operations."""
    print("🔍 SQLite Database Operations Example")
    print("=" * 50)

    # Using context manager (recommended)
    with get_sqlite_session_context() as session:
        # Query all leads
        result = session.execute(
            text(
                "SELECT first_name, last_name, company, status FROM leads ORDER BY created_date DESC LIMIT 5;"
            )
        )
        leads = result.fetchall()

        print("👥 Recent leads:")
        for lead in leads:
            print(f"  • {lead[0]} {lead[1]} from {lead[2]} (Status: {lead[3]})")

        # Query sales summary
        result = session.execute(
            text("""
            SELECT 
                l.first_name || ' ' || l.last_name as customer_name,
                s.product_name,
                s.amount,
                s.sale_date,
                s.status
            FROM sales s
            JOIN leads l ON s.lead_id = l.id
            ORDER BY s.sale_date DESC
            LIMIT 5;
        """)
        )
        sales = result.fetchall()

        print("\n💰 Recent sales:")
        for sale in sales:
            print(
                f"  • {sale[0]} - {sale[1]} (${sale[2]:,.2f}) on {sale[3]} - {sale[4]}"
            )

        # Aggregate query
        result = session.execute(
            text("""
            SELECT 
                status,
                COUNT(*) as count,
                SUM(amount) as total_amount
            FROM sales 
            GROUP BY status;
        """)
        )
        status_summary = result.fetchall()

        print("\n📊 Sales by status:")
        for status in status_summary:
            print(f"  • {status[0]}: {status[1]} sales, ${status[2]:,.2f} total")


def example_postgres_operations():
    """Example of PostgreSQL database operations (configuration only)."""
    print("\n🔍 PostgreSQL Configuration Example")
    print("=" * 50)

    # Note: This is just configuration demonstration
    # Actual PostgreSQL connection would require a running PostgreSQL server

    print("📋 PostgreSQL connection details:")
    try:
        print(f"  • Engine: {db_manager.postgres_engine}")
        print(f"  • Session factory: {db_manager.postgres_session_factory}")
        print("✅ PostgreSQL configuration loaded successfully!")
    except ModuleNotFoundError as e:
        print(f"❌ PostgreSQL driver not installed: {e}")
        print("💡 To install PostgreSQL support, run: uv add psycopg2-binary")
    except Exception as e:
        print(f"❌ PostgreSQL connection error: {e}")

    print("\n💡 To use PostgreSQL, ensure:")
    print("  1. Install PostgreSQL driver: uv add psycopg2-binary")
    print("  2. PostgreSQL server is running")
    print("  3. Database 'aigis_governance' exists")
    print("  4. User 'postgres' has proper permissions")
    print("  5. Update .env file with correct credentials")


def example_session_management():
    """Example of different session management approaches."""
    print("\n🔍 Session Management Examples")
    print("=" * 50)

    # Method 1: Context manager (recommended)
    print("✅ Using context manager:")
    try:
        with get_sqlite_session_context() as session:
            result = session.execute(text("SELECT COUNT(*) FROM leads;"))
            fetched = result.fetchone()
            if fetched:
                count = fetched[0]
                print(f"  Total leads: {count}")
    except Exception as e:
        print(f"  Error: {e}")

    # Method 2: Manual session management
    print("\n✅ Manual session management:")
    session = db_manager.get_sqlite_session()
    try:
        result = session.execute(text("SELECT COUNT(*) FROM sales;"))
        fetched = result.fetchone()
        if fetched:
            count = fetched[0]
            print(f"  Total sales: {count}")
            session.commit()
    except Exception as e:
        session.rollback()
        print(f"  Error: {e}")
    finally:
        session.close()


def main():
    """Main function demonstrating database usage."""
    print("🚀 Database Usage Examples")
    print("=" * 60)

    # SQLite operations
    example_sqlite_operations()

    # PostgreSQL configuration
    example_postgres_operations()

    # Session management
    example_session_management()

    print("\n" + "=" * 60)
    print("🎉 Examples completed!")
    print("\n💡 Key takeaways:")
    print("  • Use context managers for automatic transaction management")
    print("  • SQLAlchemy text() function for raw SQL queries")
    print("  • Both PostgreSQL and SQLite connections are available")
    print("  • Session factories handle connection pooling automatically")


if __name__ == "__main__":
    main()
