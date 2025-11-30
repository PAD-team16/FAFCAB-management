#!/usr/bin/env python3
"""
Test script to verify database connections for the ETL pipeline
"""

import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_data_warehouse_connection():
    """Test connection to data warehouse database"""
    try:
        conn = psycopg2.connect(
            host=os.getenv('DW_POSTGRES_HOST', 'localhost'),
            port=os.getenv('DW_POSTGRES_PORT', '5433'),
            database=os.getenv('DW_POSTGRES_DB', 'fafcab_dw'),
            user=os.getenv('DW_POSTGRES_USER', 'dw_user'),
            password=os.getenv('DW_POSTGRES_PASSWORD', 'dw_password')
        )
        print("✓ Connected to data warehouse database successfully")
        conn.close()
        return True
    except Exception as e:
        print(f"✗ Failed to connect to data warehouse database: {e}")
        return False

def test_source_connections():
    """Test connections to source databases"""
    connections = {}
    
    # Test main database connection
    try:
        conn = psycopg2.connect(
            host=os.getenv('SOURCE_MAIN_DB_HOST', 'postgres'),
            port=os.getenv('SOURCE_MAIN_DB_PORT', '5432'),
            database=os.getenv('POSTGRES_DB', 'fafcab'),
            user=os.getenv('POSTGRES_USER', 'user'),
            password=os.getenv('POSTGRES_PASSWORD', 'password')
        )
        print("✓ Connected to main database successfully")
        connections['main_db'] = conn
    except Exception as e:
        print(f"✗ Failed to connect to main database: {e}")
        connections['main_db'] = None
    
    # Test check-in database connection
    try:
        conn = psycopg2.connect(
            host=os.getenv('SOURCE_CHECKIN_DB_HOST', 'checkin-db'),
            port=os.getenv('SOURCE_CHECKIN_DB_PORT', '5432'),
            database=os.getenv('SOURCE_CHECKIN_DB_NAME', 'checkin_service'),
            user=os.getenv('SOURCE_CHECKIN_DB_USER', 'checkin_user'),
            password=os.getenv('SOURCE_CHECKIN_DB_PASSWORD', 'checkin_pass')
        )
        print("✓ Connected to check-in database successfully")
        connections['checkin_db'] = conn
    except Exception as e:
        print(f"✗ Failed to connect to check-in database: {e}")
        connections['checkin_db'] = None
    
    # Close connections
    for name, conn in connections.items():
        if conn:
            try:
                conn.close()
                print(f"Closed connection to {name}")
            except:
                pass
    
    return all(conn is not None for conn in connections.values())

def main():
    """Main test function"""
    print("Testing database connections for FAFCAB ETL Pipeline")
    print("=" * 50)
    
    # Test data warehouse connection
    print("\n1. Testing Data Warehouse Connection:")
    dw_success = test_data_warehouse_connection()
    
    # Test source database connections
    print("\n2. Testing Source Database Connections:")
    source_success = test_source_connections()
    
    # Summary
    print("\n" + "=" * 50)
    if dw_success and source_success:
        print("✓ All database connections are working correctly!")
        return 0
    else:
        print("✗ Some database connections failed!")
        return 1

if __name__ == "__main__":
    exit(main())