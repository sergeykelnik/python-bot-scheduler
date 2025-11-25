
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
                    schedule_type TEXT NOT NULL,
                    schedule_data TEXT NOT NULL,
                    is_paused INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()
        logger.info("Database initialized")
    
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
    def save_schedule(self, job_id, user_id, chat_id, message, schedule_type, schedule_data, is_paused=False):
        """Сохранение расписания в базу данных"""
        self._execute_query('''
            INSERT OR REPLACE INTO schedules 
            (job_id, user_id, chat_id, message, schedule_type, schedule_data, is_paused)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (job_id, user_id, chat_id, message, schedule_type, json.dumps(schedule_data), 1 if is_paused else 0))
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
                'schedule_type': row[4],
                'schedule_data': json.loads(row[5]),
                'is_paused': bool(row[6]),
                'created_at': row[7]
            })
        return schedules