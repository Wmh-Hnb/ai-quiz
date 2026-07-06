"""
数据库模块 - SQLite 题库存储
"""
import sqlite3
import json
import os
import sys
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, asdict
from datetime import datetime


def get_db_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        base_dir = Path(os.environ.get("APPDATA") or os.environ.get("LOCALAPPDATA") or Path.home())
        return base_dir / "ai-quiz"
    return Path(__file__).parent.parent


def get_settings_path() -> Path:
    base_dir = get_db_base_dir()
    settings_dir = base_dir / "data"
    settings_dir.mkdir(parents=True, exist_ok=True)
    return settings_dir / "settings.json"


# 数据库文件路径
DB_PATH = get_db_base_dir() / "data" / "quiz.db"


@dataclass
class Question:
    """题目数据结构"""
    id: Optional[int] = None
    type: str = ""  # 名词解释, 单选题, 多选题, 填空题, 简答题, 论述题, 判断题, 病例分析题
    content: str = ""  # 题目内容
    options: str = ""  # 选择题选项 (JSON 格式)
    answer: str = ""  # 标准答案
    keywords: str = ""  # 关键词 (逗号分隔)
    explanation: str = ""  # 解析
    difficulty: int = 1  # 难度 1-3
    category: str = ""  # 分类 (病理学、药理学等)
    created_at: str = ""  # 创建时间
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    def get_options_list(self) -> list:
        """获取选项列表"""
        if not self.options:
            return []
        try:
            return json.loads(self.options)
        except:
            return []


@dataclass
class ExamRecord:
    """考试记录"""
    id: Optional[int] = None
    start_time: str = ""
    end_time: str = ""
    total_questions: int = 0
    correct_count: int = 0
    score: float = 0.0
    details: str = ""  # JSON 格式的详细答题记录


def init_db():
    """初始化数据库"""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 创建题目表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL,
            content TEXT NOT NULL,
            options TEXT,
            answer TEXT NOT NULL,
            keywords TEXT,
            explanation TEXT,
            difficulty INTEGER DEFAULT 1,
            category TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 创建考试记录表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS exam_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            start_time TEXT,
            end_time TEXT,
            total_questions INTEGER,
            correct_count INTEGER,
            score REAL,
            details TEXT
        )
    ''')
    
    # 创建做题记录表 (用于统计)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS practice_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question_id INTEGER,
            user_answer TEXT,
            is_correct INTEGER,
            practice_time TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (question_id) REFERENCES questions(id)
        )
    ''')
    
    # 创建错题集表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS wrong_questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question_id INTEGER UNIQUE,
            wrong_count INTEGER DEFAULT 1,
            last_wrong_time TEXT DEFAULT CURRENT_TIMESTAMP,
            user_answer TEXT,
            is_mastered INTEGER DEFAULT 0,
            FOREIGN KEY (question_id) REFERENCES questions(id)
        )
    ''')
    
    conn.commit()
    conn.close()


def get_connection():
    """获取数据库连接"""
    init_db()
    return sqlite3.connect(DB_PATH)


# ============ 题目操作 ============

def add_question(question: Question) -> int:
    """添加题目"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO questions (type, content, options, answer, keywords, explanation, difficulty, category)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        question.type,
        question.content,
        question.options,
        question.answer,
        question.keywords,
        question.explanation,
        question.difficulty,
        question.category
    ))
    
    question_id = cursor.lastrowid or 0
    conn.commit()
    conn.close()
    return question_id


def add_questions_batch(questions: list[Question]) -> int:
    """批量添加题目"""
    conn = get_connection()
    cursor = conn.cursor()
    
    data = [
        (q.type, q.content, q.options, q.answer, q.keywords, q.explanation, q.difficulty, q.category)
        for q in questions
    ]
    
    cursor.executemany('''
        INSERT INTO questions (type, content, options, answer, keywords, explanation, difficulty, category)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', data)
    
    count = cursor.rowcount
    conn.commit()
    conn.close()
    return count


def get_all_questions() -> list[Question]:
    """获取所有题目"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM questions ORDER BY created_at DESC')
    rows = cursor.fetchall()
    conn.close()
    
    return [Question(
        id=row[0], type=row[1], content=row[2], options=row[3],
        answer=row[4], keywords=row[5], explanation=row[6],
        difficulty=row[7], category=row[8], created_at=row[9]
    ) for row in rows]


def get_questions_by_type(question_type: str) -> list[Question]:
    """按类型获取题目"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM questions WHERE type = ? ORDER BY created_at DESC', (question_type,))
    rows = cursor.fetchall()
    conn.close()
    
    return [Question(
        id=row[0], type=row[1], content=row[2], options=row[3],
        answer=row[4], keywords=row[5], explanation=row[6],
        difficulty=row[7], category=row[8], created_at=row[9]
    ) for row in rows]


def get_questions_by_category(category: str) -> list[Question]:
    """按分类获取题目"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM questions WHERE category = ? ORDER BY created_at DESC', (category,))
    rows = cursor.fetchall()
    conn.close()
    
    return [Question(
        id=row[0], type=row[1], content=row[2], options=row[3],
        answer=row[4], keywords=row[5], explanation=row[6],
        difficulty=row[7], category=row[8], created_at=row[9]
    ) for row in rows]


def search_questions(keyword: str) -> list[Question]:
    """搜索题目"""
    conn = get_connection()
    cursor = conn.cursor()
    
    search_term = f"%{keyword}%"
    cursor.execute('''
        SELECT * FROM questions 
        WHERE content LIKE ? OR keywords LIKE ? OR category LIKE ?
        ORDER BY created_at DESC
    ''', (search_term, search_term, search_term))
    rows = cursor.fetchall()
    conn.close()
    
    return [Question(
        id=row[0], type=row[1], content=row[2], options=row[3] or "",
        answer=row[4], keywords=row[5] or "", explanation=row[6] or "",
        difficulty=row[7], category=row[8] or "", created_at=row[9] or ""
    ) for row in rows]


def get_random_questions(count: int, question_type: Optional[str] = None) -> list[Question]:
    """随机获取题目"""
    conn = get_connection()
    cursor = conn.cursor()
    
    if question_type:
        cursor.execute('''
            SELECT * FROM questions WHERE type = ? ORDER BY RANDOM() LIMIT ?
        ''', (question_type, count))
    else:
        cursor.execute('SELECT * FROM questions ORDER BY RANDOM() LIMIT ?', (count,))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [Question(
        id=row[0], type=row[1], content=row[2], options=row[3],
        answer=row[4], keywords=row[5], explanation=row[6],
        difficulty=row[7], category=row[8], created_at=row[9]
    ) for row in rows]


def delete_question(question_id: int) -> bool:
    """删除题目"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM questions WHERE id = ?', (question_id,))
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    
    return affected > 0


def update_question(question: Question) -> bool:
    """更新题目"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE questions SET 
            type = ?, content = ?, options = ?, answer = ?, 
            keywords = ?, explanation = ?, difficulty = ?, category = ?
        WHERE id = ?
    ''', (
        question.type, question.content, question.options, question.answer,
        question.keywords, question.explanation, question.difficulty, 
        question.category, question.id
    ))
    
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    
    return affected > 0


def get_question_stats() -> dict:
    """获取题库统计信息"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # 总数
    cursor.execute('SELECT COUNT(*) FROM questions')
    total = cursor.fetchone()[0]
    
    # 按类型统计
    cursor.execute('SELECT type, COUNT(*) FROM questions GROUP BY type')
    by_type = dict(cursor.fetchall())
    
    # 按分类统计
    cursor.execute('SELECT category, COUNT(*) FROM questions GROUP BY category')
    by_category = dict(cursor.fetchall())
    
    # 按难度统计
    cursor.execute('SELECT difficulty, COUNT(*) FROM questions GROUP BY difficulty')
    by_difficulty = dict(cursor.fetchall())
    
    conn.close()
    
    return {
        'total': total,
        'by_type': by_type,
        'by_category': by_category,
        'by_difficulty': by_difficulty
    }


# ============ 考试记录操作 ============

def save_exam_record(record: ExamRecord) -> int:
    """保存考试记录"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO exam_records (start_time, end_time, total_questions, correct_count, score, details)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        record.start_time, record.end_time, record.total_questions,
        record.correct_count, record.score, record.details
    ))
    
    record_id = cursor.lastrowid or 0
    conn.commit()
    conn.close()
    return record_id


def get_exam_records() -> list[ExamRecord]:
    """获取所有考试记录"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM exam_records ORDER BY start_time DESC')
    rows = cursor.fetchall()
    conn.close()
    
    return [ExamRecord(
        id=row[0], start_time=row[1], end_time=row[2],
        total_questions=row[3], correct_count=row[4],
        score=row[5], details=row[6]
    ) for row in rows]


# ============ 练习记录操作 ============

def save_practice_record(question_id: int, user_answer: str, is_correct: bool):
    """保存练习记录"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO practice_records (question_id, user_answer, is_correct)
        VALUES (?, ?, ?)
    ''', (question_id, user_answer, 1 if is_correct else 0))
    
    conn.commit()
    conn.close()


def get_practice_stats(question_id: Optional[int] = None) -> dict:
    """获取练习统计"""
    conn = get_connection()
    cursor = conn.cursor()
    
    if question_id:
        cursor.execute('''
            SELECT COUNT(*), SUM(is_correct) FROM practice_records WHERE question_id = ?
        ''', (question_id,))
    else:
        cursor.execute('SELECT COUNT(*), SUM(is_correct) FROM practice_records')
    
    row = cursor.fetchone()
    conn.close()
    
    total = row[0] or 0
    correct = row[1] or 0
    
    return {
        'total': total,
        'correct': correct,
        'accuracy': correct / total if total > 0 else 0
    }


@dataclass
class WrongQuestion:
    id: Optional[int] = None
    question_id: int = 0
    wrong_count: int = 1
    last_wrong_time: str = ""
    user_answer: str = ""
    is_mastered: int = 0


def add_wrong_question(question_id: int, user_answer: str):
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT id, wrong_count FROM wrong_questions WHERE question_id = ?', (question_id,))
    existing = cursor.fetchone()
    
    if existing:
        cursor.execute('''
            UPDATE wrong_questions 
            SET wrong_count = wrong_count + 1, last_wrong_time = CURRENT_TIMESTAMP, user_answer = ?, is_mastered = 0
            WHERE question_id = ?
        ''', (user_answer, question_id))
    else:
        cursor.execute('''
            INSERT INTO wrong_questions (question_id, user_answer) VALUES (?, ?)
        ''', (question_id, user_answer))
    
    conn.commit()
    conn.close()


def get_wrong_questions(include_mastered: bool = False) -> list[dict]:
    conn = get_connection()
    cursor = conn.cursor()
    
    mastered_filter = "" if include_mastered else "WHERE w.is_mastered = 0"
    
    cursor.execute(f'''
        SELECT w.id, w.question_id, w.wrong_count, w.last_wrong_time, w.user_answer, w.is_mastered,
               q.type, q.content, q.options, q.answer, q.explanation, q.difficulty, q.category
        FROM wrong_questions w
        JOIN questions q ON w.question_id = q.id
        {mastered_filter}
        ORDER BY w.wrong_count DESC, w.last_wrong_time DESC
    ''')
    rows = cursor.fetchall()
    conn.close()
    
    return [{
        'id': row[0],
        'question_id': row[1],
        'wrong_count': row[2],
        'last_wrong_time': row[3],
        'user_answer': row[4],
        'is_mastered': row[5],
        'question': Question(
            id=row[1], type=row[6], content=row[7], options=row[8] or "",
            answer=row[9], explanation=row[10] or "", difficulty=row[11], category=row[12] or ""
        )
    } for row in rows]


def mark_question_mastered(question_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE wrong_questions SET is_mastered = 1 WHERE question_id = ?', (question_id,))
    conn.commit()
    conn.close()


def remove_from_wrong_questions(question_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM wrong_questions WHERE question_id = ?', (question_id,))
    conn.commit()
    conn.close()


def get_wrong_question_stats() -> dict:
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM wrong_questions WHERE is_mastered = 0')
    total_wrong = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM wrong_questions WHERE is_mastered = 1')
    mastered = cursor.fetchone()[0]
    
    cursor.execute('SELECT SUM(wrong_count) FROM wrong_questions')
    total_wrong_times = cursor.fetchone()[0] or 0
    
    conn.close()
    
    return {
        'total_wrong': total_wrong,
        'mastered': mastered,
        'total_wrong_times': total_wrong_times
    }


def clear_all_questions():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM questions')
    cursor.execute('DELETE FROM practice_records')
    cursor.execute('DELETE FROM exam_records')
    cursor.execute('DELETE FROM wrong_questions')
    conn.commit()
    conn.close()


def clear_wrong_questions():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM wrong_questions')
    conn.commit()
    conn.close()
