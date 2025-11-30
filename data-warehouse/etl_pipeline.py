#!/usr/bin/env python3
"""
ETL Pipeline for FAFCAB Data Warehouse
This script extracts data from various microservices, transforms it, and loads it into the data warehouse.
"""

import os
import sys
import json
import logging
import psycopg2
import requests
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv
import schedule
import time
from typing import Tuple

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("/app/logs/etl_pipeline.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class ETLPipeline:
    def __init__(self):
        # Data Warehouse connection
        self.dw_host = os.getenv('DW_POSTGRES_HOST', 'localhost')
        self.dw_port = os.getenv('DW_POSTGRES_PORT', '5433')
        self.dw_db = os.getenv('DW_POSTGRES_DB', 'fafcab_dw')
        self.dw_user = os.getenv('DW_POSTGRES_USER', 'dw_user')
        self.dw_password = os.getenv('DW_POSTGRES_PASSWORD', 'dw_password')
        
        # Source database configurations based on docker-compose.yml
        self.source_configs = {
            'main_db': {
                'host': os.getenv('SOURCE_MAIN_DB_HOST', 'postgres'),
                'port': os.getenv('SOURCE_MAIN_DB_PORT', '5432'),
                'dbname': os.getenv('POSTGRES_DB', 'fafcab'),
                'user': os.getenv('POSTGRES_USER', 'user'),
                'password': os.getenv('POSTGRES_PASSWORD', 'password')
            },
            'checkin_db': {
                'host': os.getenv('SOURCE_CHECKIN_DB_HOST', 'checkin-db'),
                'port': os.getenv('SOURCE_CHECKIN_DB_PORT', '5432'),
                'dbname': os.getenv('SOURCE_CHECKIN_DB_NAME', 'checkin_service'),
                'user': os.getenv('SOURCE_CHECKIN_DB_USER', 'checkin_user'),
                'password': os.getenv('SOURCE_CHECKIN_DB_PASSWORD', 'checkin_pass')
            },
            'db1': {
                'host': os.getenv('SOURCE_MAIN_DB_HOST', 'postgres'),
                'port': os.getenv('SOURCE_MAIN_DB_PORT', '5432'),
                'dbname': os.getenv('POSTGRES_DB_1', 'fafcab_db1'),
                'user': os.getenv('POSTGRES_USER', 'user'),
                'password': os.getenv('POSTGRES_PASSWORD', 'password')
            },
            'db2': {
                'host': os.getenv('SOURCE_MAIN_DB_HOST', 'postgres'),
                'port': os.getenv('SOURCE_MAIN_DB_PORT', '5432'),
                'dbname': os.getenv('POSTGRES_DB_2', 'fafcab_db2'),
                'user': os.getenv('POSTGRES_USER', 'user'),
                'password': os.getenv('POSTGRES_PASSWORD', 'password')
            }
        }
        
        # Initialize connections
        self.dw_conn = None
        self.source_conns = {}
        
        # Monitoring
        self.run_stats = {
            'runs': 0,
            'successful_runs': 0,
            'failed_runs': 0,
            'last_run': None,
            'last_success': None,
            'last_failure': None
        }
        
    def connect_to_data_warehouse(self):
        """Establish connection to data warehouse"""
        try:
            self.dw_conn = psycopg2.connect(
                host=self.dw_host,
                port=self.dw_port,
                database=self.dw_db,
                user=self.dw_user,
                password=self.dw_password
            )
            logger.info("Connected to data warehouse successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to data warehouse: {e}")
            return False
    
    def connect_to_sources(self):
        """Establish connections to source databases"""
        try:
            # Connect to all configured source databases
            for db_name, config in self.source_configs.items():
                try:
                    self.source_conns[db_name] = psycopg2.connect(
                        host=config['host'],
                        port=config['port'],
                        database=config['dbname'],
                        user=config['user'],
                        password=config['password']
                    )
                    logger.info(f"Connected to {db_name} database ({config['dbname']}) successfully")
                except Exception as e:
                    logger.error(f"Failed to connect to {db_name} database ({config['dbname']}): {e}")
                    # Continue with other connections even if one fails
            
            return True
        except Exception as e:
            logger.error(f"Failed to connect to source databases: {e}")
            return False
    
    def close_connections(self):
        """Close all database connections"""
        if self.dw_conn:
            self.dw_conn.close()
            
        for conn in self.source_conns.values():
            if conn:
                conn.close()
    
    def extract_users(self):
        """Extract user data from User Management Service"""
        try:
            cursor = self.source_conns['main_db'].cursor()
            
            # Get users data with roles
            cursor.execute("""
                SELECT u.id, u.username, u.email, u.joined_at as created_at, u.global_name, u.updated_at,
                       ARRAY_AGG(r.name) as roles
                FROM users u
                LEFT JOIN user_roles ur ON u.id = ur.user_id
                LEFT JOIN roles r ON ur.role_id = r.id
                GROUP BY u.id, u.username, u.email, u.joined_at, u.global_name, u.updated_at
            """)
            
            users_data = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            
            # Convert to DataFrame
            df = pd.DataFrame(users_data, columns=columns)
            
            cursor.close()
            logger.info(f"Extracted {len(df)} users from User Management Service")
            return df
            
        except psycopg2.Error as e:
            if 'does not exist' in str(e):
                logger.warning(f"Table 'users' does not exist in User Management Service database. Schema may not be initialized yet.")
            else:
                logger.error(f"Database error while extracting users: {e}")
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"Unexpected error while extracting users: {e}")
            return pd.DataFrame()
    
    def extract_budget_data(self):
        """Extract budget data from Budgeting Service"""
        try:
            cursor = self.source_conns['main_db'].cursor()
            
            # Extract budget data
            cursor.execute("""
                SELECT id, entity, affiliation, amount, created_by, inserted_at, updated_at
                FROM budget
            """)
            
            budget_data = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            
            # Convert to DataFrame
            df = pd.DataFrame(budget_data, columns=columns)
            
            # Also extract debts data
            cursor.execute("""
                SELECT id, responsable, created_by, amount, inserted_at, updated_at
                FROM debts
            """)
            
            debts_data = cursor.fetchall()
            debts_columns = [desc[0] for desc in cursor.description]
            
            # Convert to DataFrame
            debts_df = pd.DataFrame(debts_data, columns=debts_columns)
            
            cursor.close()
            logger.info(f"Extracted {len(df)} budget records and {len(debts_df)} debt records from Budgeting Service")
            return {'budget': df, 'debts': debts_df}
            
        except psycopg2.Error as e:
            if 'does not exist' in str(e):
                logger.warning(f"Table 'budget' or 'debts' does not exist in Budgeting Service database. Schema may not be initialized yet.")
            else:
                logger.error(f"Database error while extracting budget data: {e}")
            return {'budget': pd.DataFrame(), 'debts': pd.DataFrame()}
        except Exception as e:
            logger.error(f"Unexpected error while extracting budget data: {e}")
            return {'budget': pd.DataFrame(), 'debts': pd.DataFrame()}
    
    def extract_consumables_data(self):
        """Extract consumables data from Consumables Service"""
        try:
            cursor = self.source_conns['db2'].cursor()
            
            # Extract consumables data
            cursor.execute("""
                SELECT id, name, count, responsable, threshold, inserted_at, updated_at
                FROM consumables
            """)
            
            consumables_data = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            
            # Convert to DataFrame
            df = pd.DataFrame(consumables_data, columns=columns)
            
            cursor.close()
            logger.info(f"Extracted {len(df)} consumables records from Consumables Service")
            return df
            
        except psycopg2.Error as e:
            if 'does not exist' in str(e):
                logger.warning(f"Table 'consumables' does not exist in Consumables Service database. Schema may not be initialized yet.")
            else:
                logger.error(f"Database error while extracting consumables data: {e}")
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"Unexpected error while extracting consumables data: {e}")
            return pd.DataFrame()
    
    def extract_sharing_data(self):
        """Extract sharing data from Sharing Service"""
        try:
            cursor = self.source_conns['main_db'].cursor()
            
            # Extract item data
            cursor.execute("""
                SELECT id, status, name, responsable, rent_period, owner, description, state, created_at, updated_at
                FROM item
            """)
            
            sharing_data = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            
            # Convert to DataFrame
            df = pd.DataFrame(sharing_data, columns=columns)
            
            # Also extract item log data
            cursor.execute("""
                SELECT id, action, details, timestamp, item_id, created_at
                FROM item_log
            """)
            
            log_data = cursor.fetchall()
            log_columns = [desc[0] for desc in cursor.description]
            
            # Convert to DataFrame
            log_df = pd.DataFrame(log_data, columns=log_columns)
            
            cursor.close()
            logger.info(f"Extracted {len(df)} sharing records and {len(log_df)} log records from Sharing Service")
            return {'items': df, 'logs': log_df}
            
        except psycopg2.Error as e:
            if 'does not exist' in str(e):
                logger.warning(f"Table 'item' or 'item_log' does not exist in Sharing Service database. Schema may not be initialized yet.")
            else:
                logger.error(f"Database error while extracting sharing data: {e}")
            return {'items': pd.DataFrame(), 'logs': pd.DataFrame()}
        except Exception as e:
            logger.error(f"Unexpected error while extracting sharing data: {e}")
            return {'items': pd.DataFrame(), 'logs': pd.DataFrame()}
    
    def extract_communication_data(self):
        """Extract communication data from Communication Service"""
        try:
            cursor = self.source_conns['db2'].cursor()
            
            # Extract messages data
            cursor.execute("""
                SELECT m.id, m.content, m.user_id, m.channel_id, m.inserted_at as timestamp,
                       LENGTH(m.content) as message_length, c.is_private
                FROM messages m
                JOIN channels c ON m.channel_id = c.id
            """)
            
            communication_data = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            
            # Convert to DataFrame
            df = pd.DataFrame(communication_data, columns=columns)
            
            cursor.close()
            logger.info(f"Extracted {len(df)} communication records from Communication Service")
            return df
            
        except psycopg2.Error as e:
            if 'does not exist' in str(e):
                logger.warning(f"Table 'messages' or 'channels' does not exist in Communication Service database. Schema may not be initialized yet.")
            else:
                logger.error(f"Database error while extracting communication data: {e}")
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"Unexpected error while extracting communication data: {e}")
            return pd.DataFrame()
    
    def extract_booking_data(self):
        """Extract booking data from Cab Booking Service"""
        try:
            cursor = self.source_conns['db1'].cursor()
            
            # Extract booking data
            cursor.execute("""
                SELECT id, place, user_id, time_slot, description, date, status, created_at, updated_at
                FROM bookings
            """)
            
            booking_data = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            
            # Convert to DataFrame
            df = pd.DataFrame(booking_data, columns=columns)
            
            cursor.close()
            logger.info(f"Extracted {len(df)} booking records from Cab Booking Service")
            return df
            
        except psycopg2.Error as e:
            if 'does not exist' in str(e):
                logger.warning(f"Table 'bookings' does not exist in Cab Booking Service database. Schema may not be initialized yet.")
            else:
                logger.error(f"Database error while extracting booking data: {e}")
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"Unexpected error while extracting booking data: {e}")
            return pd.DataFrame()
    
    def extract_fundraising_data(self):
        """Extract fundraising data from Fundraising Service"""
        try:
            cursor = self.source_conns['main_db'].cursor()
            
            # Extract fundraising campaign data
            cursor.execute("""
                SELECT id, object, object_description, description, goal, raised_amount, 
                       deadline, distribute_to, completed, completed_at, created_at, updated_at
                FROM fundraising_campaign
            """)
            
            campaign_data = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            
            # Convert to DataFrame
            campaign_df = pd.DataFrame(campaign_data, columns=columns)
            
            # Extract donation data
            cursor.execute("""
                SELECT id, user_id, amount, donated_at, campaign_id, created_at, updated_at
                FROM donation
            """)
            
            donation_data = cursor.fetchall()
            donation_columns = [desc[0] for desc in cursor.description]
            
            # Convert to DataFrame
            donation_df = pd.DataFrame(donation_data, columns=donation_columns)
            
            cursor.close()
            logger.info(f"Extracted {len(campaign_df)} campaigns and {len(donation_df)} donations from Fundraising Service")
            
            # Return both dataframes as a dictionary
            return {'campaigns': campaign_df, 'donations': donation_df}
            
        except psycopg2.Error as e:
            if 'does not exist' in str(e):
                logger.warning(f"Table 'fundraising_campaign' or 'donation' does not exist in Fundraising Service database. Schema may not be initialized yet.")
            else:
                logger.error(f"Database error while extracting fundraising data: {e}")
            return {'campaigns': pd.DataFrame(), 'donations': pd.DataFrame()}
        except Exception as e:
            logger.error(f"Unexpected error while extracting fundraising data: {e}")
            return {'campaigns': pd.DataFrame(), 'donations': pd.DataFrame()}
    
    def extract_lostnfound_data(self):
        """Extract lost and found data from Lost-n-Found Service"""
        try:
            cursor = self.source_conns['main_db'].cursor()
            
            # Extract posts data
            cursor.execute("""
                SELECT id, user_id, status, description, inserted_at, updated_at
                FROM posts
            """)
            
            posts_data = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            
            # Convert to DataFrame
            posts_df = pd.DataFrame(posts_data, columns=columns)
            
            # Extract comments data
            cursor.execute("""
                SELECT id, user_id, content, post_id, inserted_at, updated_at
                FROM comments
            """)
            
            comments_data = cursor.fetchall()
            comments_columns = [desc[0] for desc in cursor.description]
            
            # Convert to DataFrame
            comments_df = pd.DataFrame(comments_data, columns=comments_columns)
            
            cursor.close()
            logger.info(f"Extracted {len(posts_df)} posts and {len(comments_df)} comments from Lost-n-Found Service")
            
            # Return both dataframes as a dictionary
            return {'posts': posts_df, 'comments': comments_df}
            
        except psycopg2.Error as e:
            if 'does not exist' in str(e):
                logger.warning(f"Table 'posts' or 'comments' does not exist in Lost-n-Found Service database. Schema may not be initialized yet.")
            else:
                logger.error(f"Database error while extracting lost and found data: {e}")
            return {'posts': pd.DataFrame(), 'comments': pd.DataFrame()}
        except Exception as e:
            logger.error(f"Unexpected error while extracting lost and found data: {e}")
            return {'posts': pd.DataFrame(), 'comments': pd.DataFrame()}
    
    def extract_checkin_data(self):
        """Extract check-in data from Check-in Service"""
        try:
            cursor = self.source_conns['checkin_db'].cursor()
            
            # Get check-in data with temp user info
            cursor.execute("""
                SELECT id, user_id, temp_user_name, action_type, timestamp, is_guest, registered_by, description, confidence_score, created_at
                FROM checkins
            """)
            
            checkin_data = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            
            # Convert to DataFrame
            df = pd.DataFrame(checkin_data, columns=columns)
            
            # Also extract temp guests data
            cursor.execute("""
                SELECT id, name, registered_by, time_slot, description, is_active, expires_at, checked_in, checked_in_at, created_at
                FROM temp_guests
            """)
            
            temp_guests_data = cursor.fetchall()
            temp_guests_columns = [desc[0] for desc in cursor.description]
            
            # Convert to DataFrame
            temp_guests_df = pd.DataFrame(temp_guests_data, columns=temp_guests_columns)
            
            cursor.close()
            logger.info(f"Extracted {len(df)} check-in records and {len(temp_guests_df)} temp guest records from Check-in Service")
            return {'checkins': df, 'temp_guests': temp_guests_df}
            
        except psycopg2.Error as e:
            if 'does not exist' in str(e):
                logger.warning(f"Table 'checkins' or 'temp_guests' does not exist in Check-in Service database. Schema may not be initialized yet.")
            else:
                logger.error(f"Database error while extracting check-in data: {e}")
            return {'checkins': pd.DataFrame(), 'temp_guests': pd.DataFrame()}
        except Exception as e:
            logger.error(f"Unexpected error while extracting check-in data: {e}")
            return {'checkins': pd.DataFrame(), 'temp_guests': pd.DataFrame()}
            
        except Exception as e:
            logger.error(f"Failed to extract check-in data: {e}")
            return {'checkins': pd.DataFrame(), 'temp_guests': pd.DataFrame()}
    
    def validate_users_data(self, df) -> Tuple[bool, str]:
        """Validate user data quality"""
        if df.empty:
            return True, "Empty dataframe"
            
        # Check for required columns
        required_columns = ['id', 'username', 'email']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            return False, f"Missing required columns: {missing_columns}"
            
        # Check for null values in critical fields
        null_usernames = df['username'].isnull().sum()
        null_emails = df['email'].isnull().sum()
        if null_usernames > 0 or null_emails > 0:
            return False, f"Null values found: {null_usernames} usernames, {null_emails} emails"
            
        # Check for duplicate user IDs
        duplicates = df['id'].duplicated().sum()
        if duplicates > 0:
            return False, f"Duplicate user IDs found: {duplicates}"
            
        return True, "Validation passed"
    
    def transform_users(self, df):
        """Transform user data for data warehouse"""
        if df.empty:
            return df
            
        try:
            # Validate data quality
            is_valid, message = self.validate_users_data(df)
            if not is_valid:
                logger.warning(f"User data validation failed: {message}")
                # Depending on requirements, we might want to stop here or continue with warnings
                
            # Rename columns to match data warehouse schema
            df.rename(columns={
                'id': 'user_id',
                'created_at': 'first_seen',
                'updated_at': 'last_seen'
            }, inplace=True)
            
            # Add user_type based on roles
            def determine_user_type(roles):
                if not roles or roles[0] is None:
                    return 'unknown'
                roles_list = roles[0] if isinstance(roles[0], list) else roles
                if 'admin' in roles_list:
                    return 'admin'
                elif 'FAF_NGO_Member' in roles_list:
                    return 'FAF_NGO_Member'
                else:
                    return 'student'
            
            df['user_type'] = df['roles'].apply(determine_user_type)
            
            # Ensure is_active column exists
            if 'is_active' not in df.columns:
                df['is_active'] = True
                
            logger.info(f"Transformed {len(df)} users for data warehouse")
            return df
            
        except Exception as e:
            logger.error(f"Failed to transform users: {e}")
            return pd.DataFrame()
    
    def validate_checkin_data(self, df) -> Tuple[bool, str]:
        """Validate check-in data quality"""
        if df.empty:
            return True, "Empty dataframe"
            
        # Check for required columns
        required_columns = ['id', 'user_id', 'action_type', 'timestamp']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            return False, f"Missing required columns: {missing_columns}"
            
        # Check for valid action types
        valid_actions = ['entry', 'exit']
        invalid_actions = df[~df['action_type'].isin(valid_actions)]['action_type'].unique()
        if len(invalid_actions) > 0:
            return False, f"Invalid action types found: {invalid_actions}"
            
        # Check for future timestamps
        future_timestamps = (pd.to_datetime(df['timestamp']) > datetime.now()).sum()
        if future_timestamps > 0:
            logger.warning(f"Found {future_timestamps} future timestamps in check-in data")
            
        return True, "Validation passed"
    
    def transform_checkin_data(self, df):
        """Transform check-in data for data warehouse"""
        if df.empty:
            return df
            
        try:
            # Validate data quality
            is_valid, message = self.validate_checkin_data(df)
            if not is_valid:
                logger.warning(f"Check-in data validation failed: {message}")
                # Depending on requirements, we might want to stop here or continue with warnings
                
            # Rename columns to match data warehouse schema
            df.rename(columns={
                'id': 'checkin_id',
                'timestamp': 'checkin_timestamp'
            }, inplace=True)
            
            # Handle temp users (when user_id is NULL)
            df['is_temp_user'] = df['user_id'].isnull()
            
            # Map action_type to standard values
            action_mapping = {
                'entry': 'entry',
                'exit': 'exit'
            }
            df['action_type'] = df['action_type'].map(action_mapping).fillna('unknown')
            
            logger.info(f"Transformed {len(df)} check-in records for data warehouse")
            return df
            
        except Exception as e:
            logger.error(f"Failed to transform check-in data: {e}")
            return pd.DataFrame()
    
    def validate_budget_data(self, df) -> Tuple[bool, str]:
        """Validate budget data quality"""
        if df.empty:
            return True, "Empty dataframe"
            
        # Check for required columns (adjust based on actual budget schema)
        required_columns = ['amount']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            return False, f"Missing required columns: {missing_columns}"
            
        # Check for negative amounts (might be valid for expenses)
        negative_amounts = (df['amount'] < 0).sum()
        if negative_amounts > 0:
            logger.info(f"Found {negative_amounts} negative amounts in budget data (may be valid for expenses)")
            
        return True, "Validation passed"
    
    def validate_consumables_data(self, df) -> Tuple[bool, str]:
        """Validate consumables data quality"""
        if df.empty:
            return True, "Empty dataframe"
            
        # Check for required columns
        required_columns = ['name', 'count']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            return False, f"Missing required columns: {missing_columns}"
            
        # Check for negative counts
        negative_counts = (df['count'] < 0).sum()
        if negative_counts > 0:
            return False, f"Found {negative_counts} negative counts in consumables data"
            
        return True, "Validation passed"
    
    def validate_sharing_data(self, df) -> Tuple[bool, str]:
        """Validate sharing data quality"""
        if df.empty:
            return True, "Empty dataframe"
            
        # Check for required columns
        required_columns = ['name', 'status', 'owner']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            return False, f"Missing required columns: {missing_columns}"
            
        return True, "Validation passed"
    
    def validate_communication_data(self, df) -> Tuple[bool, str]:
        """Validate communication data quality"""
        if df.empty:
            return True, "Empty dataframe"
            
        # Check for required columns
        required_columns = ['content', 'user_id', 'channel_id']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            return False, f"Missing required columns: {missing_columns}"
            
        # Check for empty content
        empty_content = (df['content'].str.len() == 0).sum()
        if empty_content > 0:
            logger.warning(f"Found {empty_content} empty messages in communication data")
            
        return True, "Validation passed"
    
    def validate_booking_data(self, df) -> Tuple[bool, str]:
        """Validate booking data quality"""
        if df.empty:
            return True, "Empty dataframe"
            
        # Check for required columns
        required_columns = ['place', 'user_id', 'time_slot', 'date']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            return False, f"Missing required columns: {missing_columns}"
            
        # Check for future dates (might be valid for future bookings)
        future_bookings = (pd.to_datetime(df['date']) > datetime.now()).sum()
        if future_bookings > 0:
            logger.info(f"Found {future_bookings} future bookings in booking data (may be valid)")
            
        return True, "Validation passed"
    
    def validate_fundraising_campaigns_data(self, df) -> Tuple[bool, str]:
        """Validate fundraising campaigns data quality"""
        if df.empty:
            return True, "Empty dataframe"
            
        # Check for required columns
        required_columns = ['object', 'goal', 'raised_amount']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            return False, f"Missing required columns: {missing_columns}"
            
        # Check for negative amounts
        negative_goals = (df['goal'] < 0).sum()
        if negative_goals > 0:
            return False, f"Found {negative_goals} negative goals in fundraising data"
            
        return True, "Validation passed"
    
    def validate_fundraising_donations_data(self, df) -> Tuple[bool, str]:
        """Validate fundraising donations data quality"""
        if df.empty:
            return True, "Empty dataframe"
            
        # Check for required columns
        required_columns = ['amount', 'user_id', 'campaign_id']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            return False, f"Missing required columns: {missing_columns}"
            
        # Check for negative amounts
        negative_amounts = (df['amount'] < 0).sum()
        if negative_amounts > 0:
            return False, f"Found {negative_amounts} negative amounts in donation data"
            
        return True, "Validation passed"
    
    def validate_lostnfound_posts_data(self, df) -> Tuple[bool, str]:
        """Validate lost and found posts data quality"""
        if df.empty:
            return True, "Empty dataframe"
            
        # Check for required columns
        required_columns = ['user_id', 'status', 'description']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            return False, f"Missing required columns: {missing_columns}"
            
        # Check for empty descriptions
        empty_descriptions = (df['description'].str.len() == 0).sum()
        if empty_descriptions > 0:
            logger.warning(f"Found {empty_descriptions} empty descriptions in lost and found posts")
            
        return True, "Validation passed"
    
    def validate_lostnfound_comments_data(self, df) -> Tuple[bool, str]:
        """Validate lost and found comments data quality"""
        if df.empty:
            return True, "Empty dataframe"
            
        # Check for required columns
        required_columns = ['user_id', 'content', 'post_id']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            return False, f"Missing required columns: {missing_columns}"
            
        # Check for empty content
        empty_content = (df['content'].str.len() == 0).sum()
        if empty_content > 0:
            logger.warning(f"Found {empty_content} empty comments in lost and found data")
            
        return True, "Validation passed"
    
    def transform_budget_data(self, df):
        """Transform budget data for data warehouse"""
        if df.empty:
            return df
            
        try:
            # Validate data quality
            is_valid, message = self.validate_budget_data(df)
            if not is_valid:
                logger.warning(f"Budget data validation failed: {message}")
                # Depending on requirements, we might want to stop here or continue with warnings
                
            # Rename columns to match data warehouse schema
            # TODO: Implement actual transformation logic based on budget service schema
            
            logger.info(f"Transformed {len(df)} budget records for data warehouse")
            return df
            
        except Exception as e:
            logger.error(f"Failed to transform budget data: {e}")
            return pd.DataFrame()
    
    def transform_consumables_data(self, df):
        """Transform consumables data for data warehouse"""
        if df.empty:
            return df
            
        try:
            # Validate data quality
            is_valid, message = self.validate_consumables_data(df)
            if not is_valid:
                logger.warning(f"Consumables data validation failed: {message}")
                
            logger.info(f"Transformed {len(df)} consumables records for data warehouse")
            return df
            
        except Exception as e:
            logger.error(f"Failed to transform consumables data: {e}")
            return pd.DataFrame()
    
    def transform_sharing_data(self, df):
        """Transform sharing data for data warehouse"""
        if df.empty:
            return df
            
        try:
            # Validate data quality
            is_valid, message = self.validate_sharing_data(df)
            if not is_valid:
                logger.warning(f"Sharing data validation failed: {message}")
                
            logger.info(f"Transformed {len(df)} sharing records for data warehouse")
            return df
            
        except Exception as e:
            logger.error(f"Failed to transform sharing data: {e}")
            return pd.DataFrame()
    
    def transform_communication_data(self, df):
        """Transform communication data for data warehouse"""
        if df.empty:
            return df
            
        try:
            # Validate data quality
            is_valid, message = self.validate_communication_data(df)
            if not is_valid:
                logger.warning(f"Communication data validation failed: {message}")
                
            logger.info(f"Transformed {len(df)} communication records for data warehouse")
            return df
            
        except Exception as e:
            logger.error(f"Failed to transform communication data: {e}")
            return pd.DataFrame()
    
    def transform_booking_data(self, df):
        """Transform booking data for data warehouse"""
        if df.empty:
            return df
            
        try:
            # Validate data quality
            is_valid, message = self.validate_booking_data(df)
            if not is_valid:
                logger.warning(f"Booking data validation failed: {message}")
                
            logger.info(f"Transformed {len(df)} booking records for data warehouse")
            return df
            
        except Exception as e:
            logger.error(f"Failed to transform booking data: {e}")
            return pd.DataFrame()
    
    def transform_fundraising_campaigns_data(self, df):
        """Transform fundraising campaigns data for data warehouse"""
        if df.empty:
            return df
            
        try:
            # Validate data quality
            is_valid, message = self.validate_fundraising_campaigns_data(df)
            if not is_valid:
                logger.warning(f"Fundraising campaigns data validation failed: {message}")
                
            logger.info(f"Transformed {len(df)} fundraising campaign records for data warehouse")
            return df
            
        except Exception as e:
            logger.error(f"Failed to transform fundraising campaigns data: {e}")
            return pd.DataFrame()
    
    def transform_fundraising_donations_data(self, df):
        """Transform fundraising donations data for data warehouse"""
        if df.empty:
            return df
            
        try:
            # Validate data quality
            is_valid, message = self.validate_fundraising_donations_data(df)
            if not is_valid:
                logger.warning(f"Fundraising donations data validation failed: {message}")
                
            logger.info(f"Transformed {len(df)} fundraising donation records for data warehouse")
            return df
            
        except Exception as e:
            logger.error(f"Failed to transform fundraising donations data: {e}")
            return pd.DataFrame()
    
    def transform_lostnfound_posts_data(self, df):
        """Transform lost and found posts data for data warehouse"""
        if df.empty:
            return df
            
        try:
            # Validate data quality
            is_valid, message = self.validate_lostnfound_posts_data(df)
            if not is_valid:
                logger.warning(f"Lost and found posts data validation failed: {message}")
                
            logger.info(f"Transformed {len(df)} lost and found post records for data warehouse")
            return df
            
        except Exception as e:
            logger.error(f"Failed to transform lost and found posts data: {e}")
            return pd.DataFrame()
    
    def transform_lostnfound_comments_data(self, df):
        """Transform lost and found comments data for data warehouse"""
        if df.empty:
            return df
            
        try:
            # Validate data quality
            is_valid, message = self.validate_lostnfound_comments_data(df)
            if not is_valid:
                logger.warning(f"Lost and found comments data validation failed: {message}")
                
            logger.info(f"Transformed {len(df)} lost and found comment records for data warehouse")
            return df
            
        except Exception as e:
            logger.error(f"Failed to transform lost and found comments data: {e}")
            return pd.DataFrame()
    
    def transform_time_dimension(self, timestamps):
        """Generate time dimension records for given timestamps"""
        # Handle empty timestamps list
        if not timestamps:
            logger.info("No timestamps provided for time dimension transformation")
            return pd.DataFrame(columns=['date', 'year', 'quarter', 'month', 'day', 'day_of_week', 'day_name', 'month_name', 'is_weekend'])
        
        time_records = []
        
        for ts in timestamps:
            if pd.isna(ts):
                continue
                
            try:
                dt = pd.to_datetime(ts).date()
                time_record = {
                    'date': dt,
                    'year': dt.year,
                    'quarter': (dt.month - 1) // 3 + 1,
                    'month': dt.month,
                    'day': dt.day,
                    'day_of_week': dt.weekday(),
                    'day_name': dt.strftime('%A'),
                    'month_name': dt.strftime('%B'),
                    'is_weekend': dt.weekday() >= 5
                }
                time_records.append(time_record)
            except Exception as e:
                logger.warning(f"Could not parse timestamp {ts}: {e}")
                continue
                
        if not time_records:
            logger.info("No valid timestamps found for time dimension transformation")
            return pd.DataFrame(columns=['date', 'year', 'quarter', 'month', 'day', 'day_of_week', 'day_name', 'month_name', 'is_weekend'])
            
        return pd.DataFrame(time_records).drop_duplicates()
    
    def load_time_dimension(self, df):
        """Load time dimension data into data warehouse"""
        if df.empty:
            return
            
        try:
            cursor = self.dw_conn.cursor()
            
            for _, row in df.iterrows():
                cursor.execute("""
                    INSERT INTO dim_time (date, year, quarter, month, day, day_of_week, day_name, month_name, is_weekend)
                    VALUES (%(date)s, %(year)s, %(quarter)s, %(month)s, %(day)s, %(day_of_week)s, %(day_name)s, %(month_name)s, %(is_weekend)s)
                    ON CONFLICT (date) DO NOTHING
                """, row.to_dict())
            
            self.dw_conn.commit()
            cursor.close()
            logger.info(f"Loaded {len(df)} time dimension records")
            
        except Exception as e:
            logger.error(f"Failed to load time dimension: {e}")
            self.dw_conn.rollback()
    
    def load_users(self, df):
        """Load user data into data warehouse"""
        if df.empty:
            return
            
        try:
            cursor = self.dw_conn.cursor()
            
            for _, row in df.iterrows():
                cursor.execute("""
                    INSERT INTO dim_users (user_id, username, email, roles, is_active, first_seen, last_seen, user_type)
                    VALUES (%(user_id)s, %(username)s, %(email)s, %(roles)s, %(is_active)s, %(first_seen)s, %(last_seen)s, %(user_type)s)
                    ON CONFLICT (user_id) 
                    DO UPDATE SET 
                        username = EXCLUDED.username,
                        email = EXCLUDED.email,
                        roles = EXCLUDED.roles,
                        is_active = EXCLUDED.is_active,
                        last_seen = EXCLUDED.last_seen,
                        user_type = EXCLUDED.user_type
                """, row.to_dict())
            
            self.dw_conn.commit()
            cursor.close()
            logger.info(f"Loaded {len(df)} users into data warehouse")
            
        except Exception as e:
            logger.error(f"Failed to load users: {e}")
            self.dw_conn.rollback()
    
    def load_checkin_data(self, df):
        """Load check-in data into data warehouse"""
        if df.empty:
            return
            
        try:
            cursor = self.dw_conn.cursor()
            
            for _, row in df.iterrows():
                cursor.execute("""
                    INSERT INTO fact_checkin_events (time_id, user_id, location_id, action_type, is_guest, confidence_score, timestamp)
                    VALUES (
                        (SELECT time_id FROM dim_time WHERE date = %(checkin_timestamp)s::date),
                        %(user_id)s,
                        (SELECT location_id FROM dim_locations WHERE location_name = 'entry_point' LIMIT 1),
                        %(action_type)s,
                        %(is_guest)s,
                        %(confidence_score)s,
                        %(checkin_timestamp)s
                    )
                    ON CONFLICT DO NOTHING
                """, row.to_dict())
            
            self.dw_conn.commit()
            cursor.close()
            logger.info(f"Loaded {len(df)} check-in records into data warehouse")
            
        except Exception as e:
            logger.error(f"Failed to load check-in data: {e}")
            self.dw_conn.rollback()
    
    def load_budget_data(self, df):
        """Load budget data into data warehouse"""
        if df.empty:
            return
            
        try:
            cursor = self.dw_conn.cursor()
            
            for _, row in df.iterrows():
                cursor.execute("""
                    INSERT INTO fact_financial_transactions (time_id, user_id, resource_id, service_id, transaction_type, amount, currency, description, transaction_status, timestamp)
                    VALUES (
                        (SELECT time_id FROM dim_time WHERE date = NOW()::date),
                        NULL,  -- Will be updated when we have user data
                        NULL,  -- Will be updated when we have resource data
                        (SELECT service_id FROM dim_services WHERE service_name = 'budgeting-service' LIMIT 1),
                        'expense',
                        %(amount)s,
                        'MDL',
                        %(description)s,
                        'completed',
                        NOW()
                    )
                    ON CONFLICT DO NOTHING
                """, row.to_dict())
            
            self.dw_conn.commit()
            cursor.close()
            logger.info(f"Loaded {len(df)} budget records into data warehouse")
            
        except Exception as e:
            logger.error(f"Failed to load budget data: {e}")
            self.dw_conn.rollback()
    
    def load_debt_data(self, df):
        """Load debt data into data warehouse"""
        if df.empty:
            return
            
        try:
            cursor = self.dw_conn.cursor()
            
            for _, row in df.iterrows():
                cursor.execute("""
                    INSERT INTO fact_financial_transactions (time_id, user_id, resource_id, service_id, transaction_type, amount, currency, description, transaction_status, timestamp)
                    VALUES (
                        (SELECT time_id FROM dim_time WHERE date = NOW()::date),
                        NULL,  -- Will be updated when we have user data
                        NULL,  -- Will be updated when we have resource data
                        (SELECT service_id FROM dim_services WHERE service_name = 'budgeting-service' LIMIT 1),
                        'debt',
                        %(amount)s,
                        'MDL',
                        'Debt record',
                        'pending',
                        NOW()
                    )
                    ON CONFLICT DO NOTHING
                """, row.to_dict())
            
            self.dw_conn.commit()
            cursor.close()
            logger.info(f"Loaded {len(df)} debt records into data warehouse")
            
        except Exception as e:
            logger.error(f"Failed to load debt data: {e}")
            self.dw_conn.rollback()
    
    def load_consumables_data(self, df):
        """Load consumables data into data warehouse"""
        if df.empty:
            return
            
        try:
            cursor = self.dw_conn.cursor()
            
            # First, ensure resources exist in dim_resources
            for _, row in df.iterrows():
                cursor.execute("""
                    INSERT INTO dim_resources (resource_name, resource_type, category, owner, status)
                    VALUES (%(name)s, 'consumable', 'consumable', %(responsable)s, 
                            CASE WHEN %(count)s <= %(threshold)s THEN 'low_stock' ELSE 'available' END)
                    ON CONFLICT (resource_name) 
                    DO UPDATE SET 
                        owner = EXCLUDED.owner,
                        status = EXCLUDED.status
                """, row.to_dict())
            
            # Then load usage data
            for _, row in df.iterrows():
                cursor.execute("""
                    INSERT INTO fact_resource_usage (time_id, user_id, resource_id, service_id, usage_type, quantity, timestamp)
                    VALUES (
                        (SELECT time_id FROM dim_time WHERE date = NOW()::date),
                        NULL,  -- Will be updated when we have user data
                        (SELECT resource_id FROM dim_resources WHERE resource_name = %(name)s LIMIT 1),
                        (SELECT service_id FROM dim_services WHERE service_name = 'consumables-service' LIMIT 1),
                        'inventory_update',
                        %(count)s,
                        NOW()
                    )
                    ON CONFLICT DO NOTHING
                """, row.to_dict())
            
            self.dw_conn.commit()
            cursor.close()
            logger.info(f"Loaded {len(df)} consumables records into data warehouse")
            
        except Exception as e:
            logger.error(f"Failed to load consumables data: {e}")
            self.dw_conn.rollback()
    
    def load_sharing_data(self, df):
        """Load sharing data into data warehouse"""
        if df.empty:
            return
            
        try:
            cursor = self.dw_conn.cursor()
            
            # First, ensure resources exist in dim_resources
            for _, row in df.iterrows():
                cursor.execute("""
                    INSERT INTO dim_resources (resource_name, resource_type, category, owner, status)
                    VALUES (%(name)s, 'shared_item', 'shared_item', %(owner)s, %(status)s)
                    ON CONFLICT (resource_name) 
                    DO UPDATE SET 
                        owner = EXCLUDED.owner,
                        status = EXCLUDED.status
                """, row.to_dict())
            
            # Then load usage data
            for _, row in df.iterrows():
                cursor.execute("""
                    INSERT INTO fact_resource_usage (time_id, user_id, resource_id, service_id, usage_type, quantity, timestamp)
                    VALUES (
                        (SELECT time_id FROM dim_time WHERE date = NOW()::date),
                        NULL,  -- Will be updated when we have user data
                        (SELECT resource_id FROM dim_resources WHERE resource_name = %(name)s LIMIT 1),
                        (SELECT service_id FROM dim_services WHERE service_name = 'sharing-service' LIMIT 1),
                        'item_status_update',
                        1,
                        NOW()
                    )
                    ON CONFLICT DO NOTHING
                """, row.to_dict())
            
            self.dw_conn.commit()
            cursor.close()
            logger.info(f"Loaded {len(df)} sharing records into data warehouse")
            
        except Exception as e:
            logger.error(f"Failed to load sharing data: {e}")
            self.dw_conn.rollback()
    
    def load_communication_data(self, df):
        """Load communication data into data warehouse"""
        if df.empty:
            return
            
        try:
            cursor = self.dw_conn.cursor()
            
            for _, row in df.iterrows():
                cursor.execute("""
                    INSERT INTO fact_communication_events (time_id, user_id, service_id, channel_id, event_type, message_length, is_private, timestamp)
                    VALUES (
                        (SELECT time_id FROM dim_time WHERE date = %(timestamp)s::date),
                        %(user_id)s,
                        (SELECT service_id FROM dim_services WHERE service_name = 'communication-service' LIMIT 1),
                        %(channel_id)s,
                        'message_sent',
                        %(message_length)s,
                        %(is_private)s,
                        %(timestamp)s
                    )
                    ON CONFLICT DO NOTHING
                """, row.to_dict())
            
            self.dw_conn.commit()
            cursor.close()
            logger.info(f"Loaded {len(df)} communication records into data warehouse")
            
        except Exception as e:
            logger.error(f"Failed to load communication data: {e}")
            self.dw_conn.rollback()
    
    def load_booking_data(self, df):
        """Load booking data into data warehouse"""
        if df.empty:
            return
            
        try:
            cursor = self.dw_conn.cursor()
            
            # First, ensure locations exist in dim_locations
            unique_places = df['place'].unique()
            for place in unique_places:
                cursor.execute("""
                    INSERT INTO dim_locations (location_name, location_description, capacity)
                    VALUES (%s, %s, 20)
                    ON CONFLICT (location_name) DO NOTHING
                """, (place.lower(), f'{place} booking area'))
            
            # Then load booking data
            for _, row in df.iterrows():
                cursor.execute("""
                    INSERT INTO fact_resource_usage (time_id, user_id, resource_id, service_id, location_id, usage_type, quantity, duration_minutes, timestamp)
                    VALUES (
                        (SELECT time_id FROM dim_time WHERE date = %(date)s::date),
                        %(user_id)s,
                        NULL,  -- No specific resource for bookings
                        (SELECT service_id FROM dim_services WHERE service_name = 'cab-booking-service' LIMIT 1),
                        (SELECT location_id FROM dim_locations WHERE location_name = LOWER(%(place)s) LIMIT 1),
                        'room_booking',
                        1,
                        NULL,  -- Duration not specified
                        %(created_at)s
                    )
                    ON CONFLICT DO NOTHING
                """, row.to_dict())
            
            self.dw_conn.commit()
            cursor.close()
            logger.info(f"Loaded {len(df)} booking records into data warehouse")
            
        except Exception as e:
            logger.error(f"Failed to load booking data: {e}")
            self.dw_conn.rollback()
    
    def load_fundraising_data(self, campaigns_df, donations_df):
        """Load fundraising data into data warehouse"""
        if campaigns_df.empty and donations_df.empty:
            return
            
        try:
            cursor = self.dw_conn.cursor()
            
            # Load campaign data as resources
            for _, row in campaigns_df.iterrows():
                cursor.execute("""
                    INSERT INTO dim_resources (resource_name, resource_type, category, owner, status)
                    VALUES (%(object)s, 'fundraising_campaign', 'fundraising', %(distribute_to)s, 
                            CASE WHEN %(completed)s THEN 'completed' ELSE 'active' END)
                    ON CONFLICT (resource_name) 
                    DO UPDATE SET 
                        owner = EXCLUDED.owner,
                        status = EXCLUDED.status
                """, row.to_dict())
            
            # Load donation data as financial transactions
            for _, row in donations_df.iterrows():
                cursor.execute("""
                    INSERT INTO fact_financial_transactions (time_id, user_id, resource_id, service_id, transaction_type, amount, currency, description, transaction_status, timestamp)
                    VALUES (
                        (SELECT time_id FROM dim_time WHERE date = %(donated_at)s::date),
                        %(user_id)s,
                        (SELECT resource_id FROM dim_resources WHERE resource_name = (SELECT object FROM fundraising_campaign WHERE id = %(campaign_id)s) LIMIT 1),
                        (SELECT service_id FROM dim_services WHERE service_name = 'fundraising-service' LIMIT 1),
                        'donation',
                        %(amount)s,
                        'MDL',
                        'Fundraising donation',
                        'completed',
                        %(donated_at)s
                    )
                    ON CONFLICT DO NOTHING
                """, row.to_dict())
            
            self.dw_conn.commit()
            cursor.close()
            logger.info(f"Loaded {len(campaigns_df)} campaigns and {len(donations_df)} donations into data warehouse")
            
        except Exception as e:
            logger.error(f"Failed to load fundraising data: {e}")
            self.dw_conn.rollback()
    
    def load_lostnfound_data(self, posts_df, comments_df):
        """Load lost and found data into data warehouse"""
        if posts_df.empty and comments_df.empty:
            return
            
        try:
            cursor = self.dw_conn.cursor()
            
            # Load posts as communication events
            for _, row in posts_df.iterrows():
                cursor.execute("""
                    INSERT INTO fact_communication_events (time_id, user_id, service_id, event_type, message_length, timestamp)
                    VALUES (
                        (SELECT time_id FROM dim_time WHERE date = %(inserted_at)s::date),
                        %(user_id)s,
                        (SELECT service_id FROM dim_services WHERE service_name = 'lostnfound-service' LIMIT 1),
                        'post_created',
                        LENGTH(%(description)s),
                        %(inserted_at)s
                    )
                    ON CONFLICT DO NOTHING
                """, row.to_dict())
            
            # Load comments as communication events
            for _, row in comments_df.iterrows():
                cursor.execute("""
                    INSERT INTO fact_communication_events (time_id, user_id, service_id, event_type, message_length, timestamp)
                    VALUES (
                        (SELECT time_id FROM dim_time WHERE date = %(inserted_at)s::date),
                        %(user_id)s,
                        (SELECT service_id FROM dim_services WHERE service_name = 'lostnfound-service' LIMIT 1),
                        'comment_added',
                        LENGTH(%(content)s),
                        %(inserted_at)s
                    )
                    ON CONFLICT DO NOTHING
                """, row.to_dict())
            
            self.dw_conn.commit()
            cursor.close()
            logger.info(f"Loaded {len(posts_df)} posts and {len(comments_df)} comments into data warehouse")
            
        except Exception as e:
            logger.error(f"Failed to load lost and found data: {e}")
            self.dw_conn.rollback()
    
    def run_full_etl(self):
        """Run the complete ETL process"""
        logger.info("Starting full ETL process")
        
        # Update run stats
        self.run_stats['runs'] += 1
        self.run_stats['last_run'] = datetime.now()
        
        # Connect to databases
        if not self.connect_to_data_warehouse():
            logger.error("Failed to connect to data warehouse. Aborting ETL.")
            self.run_stats['failed_runs'] += 1
            self.run_stats['last_failure'] = datetime.now()
            return
            
        if not self.connect_to_sources():
            logger.error("Failed to connect to source databases. Aborting ETL.")
            self.run_stats['failed_runs'] += 1
            self.run_stats['last_failure'] = datetime.now()
            return
        
        try:
            # Extract phase
            logger.info("=== EXTRACT PHASE ===")
            users_df = self.extract_users()
            budget_data = self.extract_budget_data()
            checkin_data = self.extract_checkin_data()
            consumables_df = self.extract_consumables_data()
            sharing_data = self.extract_sharing_data()
            communication_df = self.extract_communication_data()
            booking_df = self.extract_booking_data()
            fundraising_data = self.extract_fundraising_data()
            lostnfound_data = self.extract_lostnfound_data()
            
            # Generate data quality report
            data_dict = {
                'users': users_df,
                'consumables': consumables_df,
                'communication': communication_df,
                'booking': booking_df
            }
            
            # Add budget data
            if isinstance(budget_data, dict):
                data_dict['budget'] = budget_data.get('budget', pd.DataFrame())
                data_dict['debts'] = budget_data.get('debts', pd.DataFrame())
            
            # Add sharing data
            if isinstance(sharing_data, dict):
                data_dict['sharing_items'] = sharing_data.get('items', pd.DataFrame())
                data_dict['sharing_logs'] = sharing_data.get('logs', pd.DataFrame())
            
            # Add check-in data
            if isinstance(checkin_data, dict):
                data_dict['checkins'] = checkin_data.get('checkins', pd.DataFrame())
                data_dict['temp_guests'] = checkin_data.get('temp_guests', pd.DataFrame())
            
            # Add fundraising data
            if isinstance(fundraising_data, dict):
                data_dict['fundraising_campaigns'] = fundraising_data.get('campaigns', pd.DataFrame())
                data_dict['fundraising_donations'] = fundraising_data.get('donations', pd.DataFrame())
            
            # Add lost and found data
            if isinstance(lostnfound_data, dict):
                data_dict['lostnfound_posts'] = lostnfound_data.get('posts', pd.DataFrame())
                data_dict['lostnfound_comments'] = lostnfound_data.get('comments', pd.DataFrame())
            
            quality_report = self.generate_data_quality_report(data_dict)
            
            # Save quality report to file
            report_filename = f"/app/logs/quality_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            try:
                with open(report_filename, 'w') as f:
                    json.dump(quality_report, f, indent=2)
                logger.info(f"Data quality report saved to {report_filename}")
            except Exception as e:
                logger.error(f"Failed to save quality report: {e}")
            
            # Transform phase
            logger.info("=== TRANSFORM PHASE ===")
            transformed_users_df = self.transform_users(users_df)
            transformed_consumables_df = self.transform_consumables_data(consumables_df)
            transformed_communication_df = self.transform_communication_data(communication_df)
            transformed_booking_df = self.transform_booking_data(booking_df)
            
            # Transform budget data
            budget_df = budget_data.get('budget', pd.DataFrame()) if isinstance(budget_data, dict) else pd.DataFrame()
            debts_df = budget_data.get('debts', pd.DataFrame()) if isinstance(budget_data, dict) else pd.DataFrame()
            transformed_budget_df = self.transform_budget_data(budget_df)
            transformed_debts_df = self.transform_budget_data(debts_df)  # Reuse same transformation method
            
            # Transform sharing data
            sharing_items_df = sharing_data.get('items', pd.DataFrame()) if isinstance(sharing_data, dict) else pd.DataFrame()
            sharing_logs_df = sharing_data.get('logs', pd.DataFrame()) if isinstance(sharing_data, dict) else pd.DataFrame()
            transformed_sharing_items_df = self.transform_sharing_data(sharing_items_df)
            # No transformation for logs
            
            # Transform check-in data
            checkins_df = checkin_data.get('checkins', pd.DataFrame()) if isinstance(checkin_data, dict) else pd.DataFrame()
            temp_guests_df = checkin_data.get('temp_guests', pd.DataFrame()) if isinstance(checkin_data, dict) else pd.DataFrame()
            transformed_checkin_df = self.transform_checkin_data(checkins_df)
            # No transformation for temp guests
            
            # Transform fundraising data
            fundraising_campaigns_df = fundraising_data.get('campaigns', pd.DataFrame()) if isinstance(fundraising_data, dict) else pd.DataFrame()
            fundraising_donations_df = fundraising_data.get('donations', pd.DataFrame()) if isinstance(fundraising_data, dict) else pd.DataFrame()
            transformed_fundraising_campaigns_df = self.transform_fundraising_campaigns_data(fundraising_campaigns_df)
            transformed_fundraising_donations_df = self.transform_fundraising_donations_data(fundraising_donations_df)
            
            # Transform lost and found data
            lostnfound_posts_df = lostnfound_data.get('posts', pd.DataFrame()) if isinstance(lostnfound_data, dict) else pd.DataFrame()
            lostnfound_comments_df = lostnfound_data.get('comments', pd.DataFrame()) if isinstance(lostnfound_data, dict) else pd.DataFrame()
            transformed_lostnfound_posts_df = self.transform_lostnfound_posts_data(lostnfound_posts_df)
            transformed_lostnfound_comments_df = self.transform_lostnfound_comments_data(lostnfound_comments_df)
            
            # Collect all timestamps for time dimension
            all_timestamps = []
            if not users_df.empty:
                all_timestamps.extend(users_df['created_at'].tolist())
                all_timestamps.extend(users_df['updated_at'].tolist())
            if not checkins_df.empty:
                all_timestamps.extend(checkins_df['timestamp'].tolist())
                all_timestamps.extend(checkins_df['created_at'].tolist())
            if not budget_df.empty:
                all_timestamps.extend(budget_df['inserted_at'].tolist())
                all_timestamps.extend(budget_df['updated_at'].tolist())
            if not debts_df.empty:
                all_timestamps.extend(debts_df['inserted_at'].tolist())
                all_timestamps.extend(debts_df['updated_at'].tolist())
            if not consumables_df.empty:
                all_timestamps.extend(consumables_df['inserted_at'].tolist())
                all_timestamps.extend(consumables_df['updated_at'].tolist())
            if not sharing_items_df.empty:
                all_timestamps.extend(sharing_items_df['created_at'].tolist())
                all_timestamps.extend(sharing_items_df['updated_at'].tolist())
            if not communication_df.empty:
                all_timestamps.extend(communication_df['timestamp'].tolist())
            if not booking_df.empty:
                all_timestamps.extend(booking_df['created_at'].tolist())
                all_timestamps.extend(booking_df['updated_at'].tolist())
            if not fundraising_campaigns_df.empty:
                all_timestamps.extend(fundraising_campaigns_df['created_at'].tolist())
                all_timestamps.extend(fundraising_campaigns_df['updated_at'].tolist())
            if not fundraising_donations_df.empty:
                all_timestamps.extend(fundraising_donations_df['donated_at'].tolist())
                all_timestamps.extend(fundraising_donations_df['created_at'].tolist())
                all_timestamps.extend(fundraising_donations_df['updated_at'].tolist())
            if not lostnfound_posts_df.empty:
                all_timestamps.extend(lostnfound_posts_df['inserted_at'].tolist())
                all_timestamps.extend(lostnfound_posts_df['updated_at'].tolist())
            if not lostnfound_comments_df.empty:
                all_timestamps.extend(lostnfound_comments_df['inserted_at'].tolist())
                all_timestamps.extend(lostnfound_comments_df['updated_at'].tolist())
            
            time_dim_df = self.transform_time_dimension(all_timestamps)
            
            # Load phase
            logger.info("=== LOAD PHASE ===")
            self.load_time_dimension(time_dim_df)
            self.load_users(transformed_users_df)
            self.load_checkin_data(transformed_checkin_df)
            self.load_budget_data(transformed_budget_df)
            self.load_debt_data(transformed_debts_df)
            self.load_consumables_data(transformed_consumables_df)
            self.load_sharing_data(transformed_sharing_items_df)
            self.load_communication_data(transformed_communication_df)
            self.load_booking_data(transformed_booking_df)
            self.load_fundraising_data(transformed_fundraising_campaigns_df, transformed_fundraising_donations_df)
            self.load_lostnfound_data(transformed_lostnfound_posts_df, transformed_lostnfound_comments_df)
            
            logger.info("Full ETL process completed successfully")
            
            # Update success stats
            self.run_stats['successful_runs'] += 1
            self.run_stats['last_success'] = datetime.now()
            
        except Exception as e:
            logger.error(f"ETL process failed: {e}")
            self.run_stats['failed_runs'] += 1
            self.run_stats['last_failure'] = datetime.now()
            
        finally:
            # Close connections
            self.close_connections()
    
    def run_incremental_etl(self):
        """Run incremental ETL process (only new/updated data)"""
        logger.info("Starting incremental ETL process")
        # TODO: Implement incremental ETL logic
        self.run_full_etl()  # For now, run full ETL
    
    def start_scheduler(self):
        """Start the ETL scheduler"""
        interval_minutes = int(os.getenv('SCHEDULER_INTERVAL_MINUTES', '60'))
        
        # Schedule jobs
        schedule.every(interval_minutes).minutes.do(self.run_incremental_etl)
        
        logger.info(f"ETL scheduler started. Running every {interval_minutes} minutes.")
        logger.info("Running initial ETL process...")
        
        # Run initial ETL
        self.run_full_etl()
        
        # Keep the scheduler running
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    def get_run_stats(self):
        """Get ETL run statistics"""
        return self.run_stats
    
    def health_check(self):
        """Perform health check of ETL pipeline"""
        try:
            # Check data warehouse connection
            if not self.dw_conn:
                return False, "No data warehouse connection"
            
            # Check source connections
            for name, conn in self.source_conns.items():
                if not conn:
                    return False, f"No connection to {name}"
            
            return True, "All connections healthy"
        except Exception as e:
            return False, f"Health check failed: {e}"
    
    def generate_data_quality_report(self, dataframes_dict):
        """Generate a data quality report for all extracted data"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'tables': {}
        }
        
        for table_name, df in dataframes_dict.items():
            # Check if dataframe is None or not a DataFrame
            if df is None or not isinstance(df, pd.DataFrame):
                report['tables'][table_name] = {
                    'row_count': 0,
                    'column_count': 0,
                    'quality_score': 0,
                    'issues': ['Dataframe is None or invalid']
                }
                continue
                
            if df.empty:
                report['tables'][table_name] = {
                    'row_count': 0,
                    'column_count': 0,
                    'quality_score': 0,
                    'issues': ['Empty dataset - no data extracted (schema may not exist or no data present)']
                }
                continue
                
            # Basic statistics
            row_count = len(df)
            col_count = len(df.columns)
            
            # Calculate quality score (simplified)
            null_percentage = df.isnull().sum().sum() / (row_count * col_count) * 100
            quality_score = max(0, 100 - null_percentage)  # Simple scoring
            
            # Identify issues
            issues = []
            if null_percentage > 5:
                issues.append(f"High null value percentage: {null_percentage:.2f}%")
                
            # Column-specific issues
            for col in df.columns:
                if df[col].dtype in ['object', 'string']:
                    empty_strings = (df[col] == '').sum()
                    if empty_strings > 0:
                        issues.append(f"Column '{col}' has {empty_strings} empty strings")
                
            report['tables'][table_name] = {
                'row_count': row_count,
                'column_count': col_count,
                'quality_score': round(quality_score, 2),
                'null_percentage': round(null_percentage, 2),
                'issues': issues
            }
            
        return report

def main():
    """Main entry point"""
    etl = ETLPipeline()
    
    if len(sys.argv) > 1 and sys.argv[1] == '--scheduled':
        # Run in scheduled mode
        etl.start_scheduler()
    else:
        # Run once
        etl.run_full_etl()

if __name__ == "__main__":
    main()

# SERVICE EXTRACTION SUMMARY:
#
# 1. User Management Service:
#    - Extracts users with their roles from users and roles tables
#    - Uses main_db connection
#    
# 2. Budgeting Service:
#    - Extracts budget entries and debt records
#    - Uses main_db connection
#    
# 3. Check-in Service:
#    - Extracts check-in records from checkins table
#    - Uses checkin_db connection
#    
# 4. Consumables Service:
#    - Extracts consumable items with inventory counts
#    - Uses main_db connection
#    
# 5. Sharing Service:
#    - Extracts shared items with status and ownership info
#    - Uses main_db connection
#    
# 6. Communication Service:
#    - Extracts messages with user and channel information
#    - Uses main_db connection
#    
# 7. Cab Booking Service:
#    - Extracts room bookings with time slots and descriptions
#    - Uses main_db connection
#    
# 8. Fundraising Service:
#    - Extracts campaigns and donations data
#    - Uses main_db connection
#    
# 9. Lost-n-Found Service:
#    - Extracts posts and comments data
#    - Uses main_db connection
#
# Each service has specific validation and transformation methods implemented.

if __name__ == "__main__":
    main()