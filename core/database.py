import json
import os
from typing import Optional

# 환경변수로 DB 타입 선택 (기본값: sqlite)
DB_TYPE = os.getenv("DB_TYPE", "sqlite").lower()
DATABASE_URL = os.getenv("DATABASE_URL")  # PostgreSQL URL

if DB_TYPE == "postgresql" or DATABASE_URL:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    DB_TYPE = "postgresql"
else:
    import sqlite3

DB_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'nutritionist.db')

class DatabaseManager:
    def __init__(self, db_url: Optional[str] = None):
        """
        데이터베이스 관리자 초기화
        :param db_url: PostgreSQL URL (옵션) 또는 환경변수 DATABASE_URL 사용
        """
        if DB_TYPE == "postgresql":
            # PostgreSQL 연결
            self.db_type = "postgresql"
            conn_url = db_url or DATABASE_URL
            if not conn_url:
                raise ValueError("PostgreSQL을 사용하려면 DATABASE_URL 환경변수를 설정해주세요.")
            self.conn = psycopg2.connect(conn_url)
            self.conn.autocommit = False  # 명시적 트랜잭션 관리
        else:
            # SQLite 연결
            self.db_type = "sqlite"
            self.conn = sqlite3.connect(DB_FILE)

        self.create_tables()

    def create_tables(self):
        """
        필요한 모든 테이블을 생성합니다.
        """
        cursor = self.conn.cursor()

        if self.db_type == "postgresql":
            # PostgreSQL용 테이블 생성
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_preferences (
                    user_id TEXT PRIMARY KEY,
                    allergies TEXT,
                    preferences TEXT,
                    dietary_goals TEXT
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS inventory (
                    item_name TEXT PRIMARY KEY,
                    quantity TEXT,
                    added_date TEXT,
                    expiry_date TEXT
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS meal_history (
                    meal_id SERIAL PRIMARY KEY,
                    meal_date TEXT,
                    recipe_id TEXT,
                    recipe_title TEXT,
                    ingredients TEXT
                )
            """)
        else:
            # SQLite용 테이블 생성
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_preferences (
                    user_id TEXT PRIMARY KEY,
                    allergies TEXT,
                    preferences TEXT,
                    dietary_goals TEXT
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS inventory (
                    item_name TEXT PRIMARY KEY,
                    quantity TEXT,
                    added_date TEXT,
                    expiry_date TEXT
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS meal_history (
                    meal_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    meal_date TEXT,
                    recipe_id TEXT,
                    recipe_title TEXT,
                    ingredients TEXT
                )
            """)

        self.conn.commit()
        cursor.close()

    def get_inventory(self) -> dict:
        """
        데이터베이스에서 현재 모든 재고를 조회하여 반환합니다.
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT item_name, quantity, added_date, expiry_date FROM inventory")
        inventory = {}
        for row in cursor.fetchall():
            item_name, quantity, added_date, expiry_date = row
            inventory[item_name] = {
                "quantity": quantity,
                "added_date": added_date,
                "expiry_date": expiry_date
            }
        cursor.close()
        return inventory

    def upsert_inventory_item(self, item_name: str, quantity: str, added_date: str, expiry_date: str):
        """
        재고 아이템을 추가하거나 이미 존재하면 업데이트합니다. (Upsert)
        """
        cursor = self.conn.cursor()

        if self.db_type == "postgresql":
            cursor.execute("""
                INSERT INTO inventory (item_name, quantity, added_date, expiry_date)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT(item_name) DO UPDATE SET
                    quantity = EXCLUDED.quantity,
                    added_date = EXCLUDED.added_date,
                    expiry_date = EXCLUDED.expiry_date
            """, (item_name, quantity, added_date, expiry_date))
        else:
            cursor.execute("""
                INSERT INTO inventory (item_name, quantity, added_date, expiry_date)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(item_name) DO UPDATE SET
                    quantity = excluded.quantity,
                    added_date = excluded.added_date,
                    expiry_date = excluded.expiry_date
            """, (item_name, quantity, added_date, expiry_date))

        self.conn.commit()
        cursor.close()

    def get_user_preferences(self, user_id: str = "default_user") -> dict:
        """
        특정 사용자의 환경설정을 조회합니다.
        """
        cursor = self.conn.cursor()

        if self.db_type == "postgresql":
            cursor.execute(
                "SELECT allergies, preferences, dietary_goals FROM user_preferences WHERE user_id = %s",
                (user_id,)
            )
        else:
            cursor.execute(
                "SELECT allergies, preferences, dietary_goals FROM user_preferences WHERE user_id = ?",
                (user_id,)
            )

        row = cursor.fetchone()
        cursor.close()

        if row:
            allergies, preferences, dietary_goals = row
            return {
                "user_id": user_id,
                "allergies": json.loads(allergies) if allergies else [],
                "preferences": json.loads(preferences) if preferences else {},
                "dietary_goals": dietary_goals
            }
        return {}

    def update_user_preferences(self, user_id: str = "default_user", allergies: list = None, preferences: dict = None, dietary_goals: str = None):
        """
        사용자 환경설정을 업데이트하거나 추가합니다.
        """
        cursor = self.conn.cursor()

        # JSON 직렬화
        allergies_json = json.dumps(allergies) if allergies is not None else None
        preferences_json = json.dumps(preferences) if preferences is not None else None

        if self.db_type == "postgresql":
            cursor.execute("""
                INSERT INTO user_preferences (user_id, allergies, preferences, dietary_goals)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT(user_id) DO UPDATE SET
                    allergies = COALESCE(EXCLUDED.allergies, user_preferences.allergies),
                    preferences = COALESCE(EXCLUDED.preferences, user_preferences.preferences),
                    dietary_goals = COALESCE(EXCLUDED.dietary_goals, user_preferences.dietary_goals)
            """, (user_id, allergies_json, preferences_json, dietary_goals))
        else:
            cursor.execute("""
                INSERT INTO user_preferences (user_id, allergies, preferences, dietary_goals)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    allergies = COALESCE(excluded.allergies, allergies),
                    preferences = COALESCE(excluded.preferences, preferences),
                    dietary_goals = COALESCE(excluded.dietary_goals, dietary_goals)
            """, (user_id, allergies_json, preferences_json, dietary_goals))

        self.conn.commit()
        cursor.close()

    def add_meal_to_history(self, meal_date: str, recipe_id: str, recipe_title: str, ingredients: list):
        """
        식사 기록을 추가합니다.
        """
        cursor = self.conn.cursor()

        # 동일한 날짜와 recipe_id를 가진 기록이 이미 있는지 확인
        if self.db_type == "postgresql":
            cursor.execute(
                "SELECT COUNT(*) FROM meal_history WHERE meal_date = %s AND recipe_id = %s",
                (meal_date, recipe_id)
            )
        else:
            cursor.execute(
                "SELECT COUNT(*) FROM meal_history WHERE meal_date = ? AND recipe_id = ?",
                (meal_date, recipe_id)
            )

        if cursor.fetchone()[0] > 0:
            print(f"경고: {meal_date}에 이미 레시피 '{recipe_title}' ({recipe_id}) 기록이 존재합니다. 중복 기록을 건너뜁니다.")
            cursor.close()
            return

        if self.db_type == "postgresql":
            cursor.execute("""
                INSERT INTO meal_history (meal_date, recipe_id, recipe_title, ingredients)
                VALUES (%s, %s, %s, %s)
            """, (meal_date, recipe_id, recipe_title, json.dumps(ingredients, ensure_ascii=False)))
        else:
            cursor.execute("""
                INSERT INTO meal_history (meal_date, recipe_id, recipe_title, ingredients)
                VALUES (?, ?, ?, ?)
            """, (meal_date, recipe_id, recipe_title, json.dumps(ingredients, ensure_ascii=False)))

        self.conn.commit()
        cursor.close()

    def close(self):
        """
        데이터베이스 연결을 닫습니다.
        """
        self.conn.close()

if __name__ == '__main__':
    # 데이터베이스 및 테이블 생성 확인
    db_manager = DatabaseManager()
    print(f"Database type: {db_manager.db_type}")
    print("Database and tables created successfully.")

    db_manager.close()
