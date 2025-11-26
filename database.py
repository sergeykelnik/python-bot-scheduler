
"""Модуль для работы с базой данных"""

import sqlite3
import json
import logging
from config import DB_PATH

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Инициализация базы данных и создание таблиц"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS schedules (
                    job_id TEXT PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    chat_id TEXT NOT NULL,
                    message TEXT NOT NULL,
                    schedule_data TEXT NOT NULL,
                    is_paused INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    language TEXT DEFAULT 'ru',
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
        
        # Run schema validation to ensure all columns exist
        self._validate_and_migrate_schema()
        logger.info("Database initialized")
    
    def _validate_and_migrate_schema(self):
        """Validate and update database schema to match current requirements.
        
        This method ensures that old databases have all necessary columns added.
        It compares the actual database schema with the expected schema and
        adds missing columns with appropriate defaults.
        """
        expected_schema = {
            'schedules': {
                'job_id': 'TEXT PRIMARY KEY',
                'user_id': 'INTEGER NOT NULL',
                'chat_id': 'TEXT NOT NULL',
                'message': 'TEXT NOT NULL',
                'schedule_data': 'TEXT NOT NULL',
                'is_paused': 'INTEGER DEFAULT 0',
                'created_at': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP'
            },
            'users': {
                'user_id': 'INTEGER PRIMARY KEY',
                'language': "TEXT DEFAULT 'ru'",
                'updated_at': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP',
                'recent_chat_ids': "TEXT DEFAULT '[]'"
            }
        }
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check and update each table
                for table_name, columns in expected_schema.items():
                    self._migrate_table_schema(cursor, table_name, columns)
                
                conn.commit()
                logger.info("Schema validation and migration completed")
        except sqlite3.OperationalError as e:
            logger.error(f"Error during schema migration: {e}")
    
    def _migrate_table_schema(self, cursor, table_name, expected_columns):
        """Migrate a single table's schema to match expected columns.
        
        Args:
            cursor: SQLite cursor object
            table_name: Name of the table to migrate
            expected_columns: Dict of column_name -> column_definition
        """
        try:
            # Get current columns
            cursor.execute(f'PRAGMA table_info({table_name})')
            existing_columns = {col[1] for col in cursor.fetchall()}
            
            # Add missing columns
            for column_name, column_def in expected_columns.items():
                if column_name not in existing_columns:
                    # Extract just the type for ALTER TABLE ADD COLUMN
                    column_type = column_def.split('PRIMARY KEY')[0].strip()
                    if 'PRIMARY KEY' in column_def:
                        # Skip primary key columns as they can't be added via ALTER
                        logger.warning(f"Cannot add primary key column {column_name} to {table_name} - skipping")
                        continue
                    
                    alter_query = f'ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}'
                    cursor.execute(alter_query)
                    logger.info(f"Added column {column_name} to table {table_name}")
        except sqlite3.OperationalError as e:
            logger.warning(f"Could not migrate table {table_name}: {e}")
    
    def _execute_query(self, query, params=None, fetch_all=False, fetch_one=False):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params or ())
            conn.commit()
            if fetch_all:
                return cursor.fetchall()
            if fetch_one:
                return cursor.fetchone()
            return None
    def save_schedule(self, job_id, user_id, chat_id, message, schedule_data, is_paused=False):
        """Сохранение расписания в базу данных"""
        self._execute_query('''
            INSERT OR REPLACE INTO schedules 
            (job_id, user_id, chat_id, message, schedule_data, is_paused)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (job_id, user_id, chat_id, message, json.dumps(schedule_data), 1 if is_paused else 0))
        logger.info(f"Schedule saved to database: {job_id}")
    
    def delete_schedule(self, job_id):
        """Удаление расписания из базы данных"""
        self._execute_query('DELETE FROM schedules WHERE job_id = ?', (job_id,))
        logger.info(f"Schedule deleted from database: {job_id}")
    
    def update_schedule_pause_status(self, job_id, is_paused):
        """Обновление статуса паузы расписания"""
        self._execute_query('''
            UPDATE schedules SET is_paused = ? WHERE job_id = ?
        ''', (1 if is_paused else 0, job_id))
        logger.info(f"Schedule {job_id} pause status updated to: {is_paused}")
    

    
    def get_schedules(self, user_id=None):
        """Получение всех расписаний из базы данных или для конкретного пользователя"""
        schedules = []
        if user_id:
            rows = self._execute_query('SELECT * FROM schedules WHERE user_id = ?', (user_id,), fetch_all=True)
        else:
            rows = self._execute_query('SELECT * FROM schedules', fetch_all=True)
            
        for row in rows:
            schedules.append({
                'job_id': row[0],
                'user_id': row[1],
                'chat_id': row[2],
                'message': row[3],
                'schedule_data': json.loads(row[4]),
                'is_paused': bool(row[5]),
                'created_at': row[6]
            })
        return schedules

    def get_user_language(self, user_id, default='ru'):
        """Get user's language preference or return default."""
        row = self._execute_query('SELECT language FROM users WHERE user_id = ?', (user_id,), fetch_one=True)
        if row and row[0]:
            return row[0]
        return default

    def set_user_language(self, user_id, language):
        """Set user's language preference."""
        # Try to insert; if user exists, update
        try:
            self._execute_query('''
                INSERT INTO users (user_id, language, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            ''', (user_id, language))
        except sqlite3.IntegrityError:
            # User already exists, update language
            self._execute_query('''
                UPDATE users SET language = ?, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
            ''', (language, user_id))

    def add_recent_chat_id(self, user_id, chat_id, max_items=5):
        """Add a chat_id to user's recent contacts list."""
        try:
            row = self._execute_query(
                'SELECT recent_chat_ids FROM users WHERE user_id = ?', 
                (user_id,), 
                fetch_one=True
            )
            if row and row[0]:
                recent_ids = json.loads(row[0])
            else:
                recent_ids = []
            
            # Remove if already exists to move it to front
            if chat_id in recent_ids:
                recent_ids.remove(chat_id)
            
            # Add to front
            recent_ids.insert(0, chat_id)
            
            # Keep only max_items
            recent_ids = recent_ids[:max_items]
            
            # Update database
            try:
                self._execute_query('''
                    INSERT INTO users (user_id, recent_chat_ids)
                    VALUES (?, ?)
                ''', (user_id, json.dumps(recent_ids)))
            except sqlite3.IntegrityError:
                self._execute_query('''
                    UPDATE users SET recent_chat_ids = ?
                    WHERE user_id = ?
                ''', (json.dumps(recent_ids), user_id))
        except Exception as e:
            logger.error(f"Error adding recent chat_id: {e}")

    def get_recent_chat_ids(self, user_id):
        """Get user's recent chat IDs."""
        try:
            row = self._execute_query(
                'SELECT recent_chat_ids FROM users WHERE user_id = ?',
                (user_id,),
                fetch_one=True
            )
            if row and row[0]:
                return json.loads(row[0])
        except Exception as e:
            logger.error(f"Error getting recent chat_ids: {e}")
        return []