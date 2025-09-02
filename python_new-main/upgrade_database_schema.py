#!/usr/bin/env python3
"""
Database Schema Upgrade - Ensure LONGTEXT for full response storage
"""

import mysql.connector
from config import config

def upgrade_database_schema():
    """Upgrade database schema to ensure full response storage"""
    print("🔧 Upgrading Database Schema for Full Response Storage")
    print("=" * 60)
    
    try:
        # Connect to database
        conn = mysql.connector.connect(**config.get_mysql_connection_params())
        cursor = conn.cursor()
        
        print(f"✅ Connected to database: {config.MYSQL_DATABASE}")
        
        # Use the database
        cursor.execute(f"USE {config.MYSQL_DATABASE}")
        
        # Check current column types
        cursor.execute("DESCRIBE agent_interactions")
        columns = cursor.fetchall()
        
        print(f"\n📊 Current agent_interactions table structure:")
        for col in columns:
            print(f"   • {col[0]}: {col[1]}")
            if col[0] == 'response' and 'text' in col[1].lower() and 'longtext' not in col[1].lower():
                print(f"      ⚠️ Response column needs upgrade from {col[1]} to LONGTEXT")
        
        # Upgrade response column to LONGTEXT if needed
        try:
            print(f"\n🔄 Upgrading response column to LONGTEXT...")
            cursor.execute("""
                ALTER TABLE agent_interactions 
                MODIFY COLUMN response LONGTEXT NOT NULL
            """)
            print(f"✅ agent_interactions.response upgraded to LONGTEXT")
        except mysql.connector.Error as e:
            if "doesn't exist" not in str(e):
                print(f"⚠️ Response column upgrade: {e}")
        
        # Check multi_agent_orchestration table
        cursor.execute("DESCRIBE multi_agent_orchestration")
        columns = cursor.fetchall()
        
        print(f"\n📊 Current multi_agent_orchestration table structure:")
        for col in columns:
            print(f"   • {col[0]}: {col[1]}")
            if col[0] == 'agent_responses' and 'text' in col[1].lower() and 'longtext' not in col[1].lower():
                print(f"      ⚠️ Agent_responses column needs upgrade from {col[1]} to LONGTEXT")
        
        # Upgrade agent_responses column to LONGTEXT if needed
        try:
            print(f"\n🔄 Upgrading agent_responses column to LONGTEXT...")
            cursor.execute("""
                ALTER TABLE multi_agent_orchestration 
                MODIFY COLUMN agent_responses LONGTEXT NOT NULL
            """)
            print(f"✅ multi_agent_orchestration.agent_responses upgraded to LONGTEXT")
        except mysql.connector.Error as e:
            if "doesn't exist" not in str(e):
                print(f"⚠️ Agent_responses column upgrade: {e}")
        
        # Create indexes for better performance if they don't exist
        indexes_to_create = [
            ("agent_interactions", "idx_response_length", "((LENGTH(response)))"),
            ("multi_agent_orchestration", "idx_responses_length", "((LENGTH(agent_responses)))")
        ]
        
        for table, index_name, index_column in indexes_to_create:
            try:
                cursor.execute(f"CREATE INDEX {index_name} ON {table} {index_column}")
                print(f"✅ Created index {index_name} on {table}")
            except mysql.connector.Error as e:
                if "Duplicate key name" in str(e):
                    print(f"ℹ️ Index {index_name} already exists")
                else:
                    print(f"⚠️ Index creation error: {e}")
        
        cursor.close()
        conn.close()
        
        print(f"\n✅ Database schema upgrade completed successfully!")
        return True
        
    except mysql.connector.Error as e:
        print(f"❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def verify_schema_upgrade():
    """Verify that the schema upgrade was successful"""
    print(f"\n🔍 Verifying Schema Upgrade")
    print("=" * 40)
    
    try:
        conn = mysql.connector.connect(**config.get_mysql_connection_params())
        cursor = conn.cursor()
        
        cursor.execute(f"USE {config.MYSQL_DATABASE}")
        
        # Check agent_interactions response column
        cursor.execute("SHOW COLUMNS FROM agent_interactions LIKE 'response'")
        result = cursor.fetchone()
        if result and 'longtext' in result[1].lower():
            print(f"✅ agent_interactions.response is LONGTEXT")
        else:
            print(f"❌ agent_interactions.response is not LONGTEXT: {result[1] if result else 'Not found'}")
        
        # Check multi_agent_orchestration agent_responses column
        cursor.execute("SHOW COLUMNS FROM multi_agent_orchestration LIKE 'agent_responses'")
        result = cursor.fetchone()
        if result and 'longtext' in result[1].lower():
            print(f"✅ multi_agent_orchestration.agent_responses is LONGTEXT")
        else:
            print(f"❌ multi_agent_orchestration.agent_responses is not LONGTEXT: {result[1] if result else 'Not found'}")
        
        # Test storage capacity by checking maximum response lengths
        cursor.execute("""
            SELECT 
                agent_name,
                MAX(LENGTH(response)) as max_response_length,
                AVG(LENGTH(response)) as avg_response_length,
                COUNT(*) as total_responses
            FROM agent_interactions 
            GROUP BY agent_name
            ORDER BY max_response_length DESC
        """)
        
        results = cursor.fetchall()
        print(f"\n📊 Response Length Statistics by Agent:")
        for result in results:
            agent, max_len, avg_len, count = result
            print(f"   • {agent}: Max={max_len} chars, Avg={avg_len:.0f} chars, Count={count}")
        
        cursor.close()
        conn.close()
        
        print(f"\n✅ Schema verification completed!")
        
    except Exception as e:
        print(f"❌ Verification error: {e}")

if __name__ == "__main__":
    try:
        from config import config
        print(f"📋 Database Configuration:")
        print(f"   Host: {config.MYSQL_HOST}")
        print(f"   Database: {config.MYSQL_DATABASE}")
        print(f"   Max Response Length: {config.AGENT_MAX_RESPONSE_LENGTH}")
        print()
        
        if upgrade_database_schema():
            verify_schema_upgrade()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Make sure the config.py file exists and database is accessible")
