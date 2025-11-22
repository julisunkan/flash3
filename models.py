import sqlite3
from datetime import datetime
import json

DATABASE = 'flashcards.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS decks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            deck_id INTEGER NOT NULL,
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            choices TEXT,
            difficulty INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (deck_id) REFERENCES decks (id) ON DELETE CASCADE
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS study_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            card_id INTEGER NOT NULL,
            easiness_factor REAL DEFAULT 2.5,
            interval INTEGER DEFAULT 0,
            repetitions INTEGER DEFAULT 0,
            next_review TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_reviewed TIMESTAMP,
            FOREIGN KEY (card_id) REFERENCES cards (id) ON DELETE CASCADE
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS quiz_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            deck_id INTEGER NOT NULL,
            score INTEGER NOT NULL,
            total INTEGER NOT NULL,
            completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (deck_id) REFERENCES decks (id) ON DELETE CASCADE
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS badges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            icon TEXT,
            requirement INTEGER,
            earned BOOLEAN DEFAULT 0,
            earned_at TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        SELECT COUNT(*) FROM badges
    ''')
    if cursor.fetchone()[0] == 0:
        badges_data = [
            ('First Steps', 'Study your first flashcard', '🎯', 1, 0, None),
            ('Beginner', 'Study 10 flashcards', '📚', 10, 0, None),
            ('Scholar', 'Study 50 flashcards', '🎓', 50, 0, None),
            ('Expert', 'Study 100 flashcards', '👨‍🎓', 100, 0, None),
            ('Master', 'Study 500 flashcards', '🏆', 500, 0, None),
            ('Quiz Starter', 'Complete your first quiz', '✅', 1, 0, None),
            ('Perfect Score', 'Get 100% on a quiz', '💯', 1, 0, None),
            ('Consistent Learner', 'Study 7 days in a row', '🔥', 7, 0, None),
        ]
        cursor.executemany('''
            INSERT INTO badges (name, description, icon, requirement, earned, earned_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', badges_data)
    
    conn.commit()
    conn.close()

class Deck:
    @staticmethod
    def create(name, description=''):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO decks (name, description) VALUES (?, ?)', (name, description))
        deck_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return deck_id
    
    @staticmethod
    def get_all():
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT d.*, COUNT(c.id) as card_count
            FROM decks d
            LEFT JOIN cards c ON d.id = c.deck_id
            GROUP BY d.id
            ORDER BY d.created_at DESC
        ''')
        decks = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return decks
    
    @staticmethod
    def get_by_id(deck_id):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM decks WHERE id = ?', (deck_id,))
        deck = cursor.fetchone()
        conn.close()
        return dict(deck) if deck else None
    
    @staticmethod
    def delete(deck_id):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM decks WHERE id = ?', (deck_id,))
        conn.commit()
        conn.close()

class Card:
    @staticmethod
    def create(deck_id, question, answer, choices=None):
        conn = get_db()
        cursor = conn.cursor()
        choices_json = json.dumps(choices) if choices else None
        cursor.execute('''
            INSERT INTO cards (deck_id, question, answer, choices)
            VALUES (?, ?, ?, ?)
        ''', (deck_id, question, answer, choices_json))
        card_id = cursor.lastrowid
        
        cursor.execute('''
            INSERT INTO study_sessions (card_id)
            VALUES (?)
        ''', (card_id,))
        
        conn.commit()
        conn.close()
        return card_id
    
    @staticmethod
    def get_by_deck(deck_id):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT c.*, s.easiness_factor, s.interval, s.repetitions, s.next_review
            FROM cards c
            LEFT JOIN study_sessions s ON c.id = s.card_id
            WHERE c.deck_id = ?
            ORDER BY c.created_at
        ''', (deck_id,))
        cards = [dict(row) for row in cursor.fetchall()]
        for card in cards:
            if card['choices']:
                card['choices'] = json.loads(card['choices'])
        conn.close()
        return cards
    
    @staticmethod
    def get_due_cards(deck_id):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT c.*, s.easiness_factor, s.interval, s.repetitions, s.next_review
            FROM cards c
            JOIN study_sessions s ON c.id = s.card_id
            WHERE c.deck_id = ? AND s.next_review <= CURRENT_TIMESTAMP
            ORDER BY s.next_review
        ''', (deck_id,))
        cards = [dict(row) for row in cursor.fetchall()]
        for card in cards:
            if card['choices']:
                card['choices'] = json.loads(card['choices'])
        conn.close()
        return cards
    
    @staticmethod
    def delete(card_id):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM cards WHERE id = ?', (card_id,))
        conn.commit()
        conn.close()ommit()
        conn.close()

class StudySession:
    @staticmethod
    def update(card_id, quality):
        from srs_algorithm import sm2_algorithm
        
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT easiness_factor, interval, repetitions
            FROM study_sessions
            WHERE card_id = ?
        ''', (card_id,))
        session = cursor.fetchone()
        
        if session:
            ef, interval, reps = session
            new_ef, new_interval, new_reps = sm2_algorithm(quality, ef, interval, reps)
            
            cursor.execute('''
                UPDATE study_sessions
                SET easiness_factor = ?,
                    interval = ?,
                    repetitions = ?,
                    next_review = datetime('now', '+' || ? || ' days'),
                    last_reviewed = CURRENT_TIMESTAMP
                WHERE card_id = ?
            ''', (new_ef, new_interval, new_reps, new_interval, card_id))
            
            conn.commit()
        
        conn.close()
    
    @staticmethod
    def get_stats():
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM study_sessions WHERE last_reviewed IS NOT NULL')
        total_studied = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM study_sessions WHERE next_review <= CURRENT_TIMESTAMP')
        due_today = cursor.fetchone()[0]
        
        cursor.execute('SELECT AVG(easiness_factor) FROM study_sessions WHERE last_reviewed IS NOT NULL')
        avg_ef = cursor.fetchone()[0] or 0
        
        conn.close()
        
        return {
            'total_studied': total_studied,
            'due_today': due_today,
            'average_retention': round(avg_ef, 2): round(avg_ef, 2)
        }

class QuizResult:
    @staticmethod
    def save(deck_id, score, total):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO quiz_results (deck_id, score, total)
            VALUES (?, ?, ?)
        ''', (deck_id, score, total))
        conn.commit()
        conn.close()
    
    @staticmethod
    def get_by_deck(deck_id):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM quiz_results
            WHERE deck_id = ?
            ORDER BY completed_at DESC
            LIMIT 10
        ''', (deck_id,))
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results

class Badge:
    @staticmethod
    def check_and_award():
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM study_sessions WHERE last_reviewed IS NOT NULL')
        cards_studied = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM quiz_results')
        quizzes_completed = cursor.fetchone()[0]
        
        cursor.execute('SELECT * FROM badges WHERE earned = 0')
        unearned_badges = cursor.fetchall()
        
        newly_earned = []
        for badge in unearned_badges:
            badge_dict = dict(badge)
            if badge_dict['name'] in ['First Steps', 'Beginner', 'Scholar', 'Expert', 'Master']:
                if cards_studied >= badge_dict['requirement']:
                    cursor.execute('''
                        UPDATE badges
                        SET earned = 1, earned_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    ''', (badge_dict['id'],))
                    newly_earned.append(badge_dict['name'])
            
            elif badge_dict['name'] == 'Quiz Starter' and quizzes_completed >= 1:
                cursor.execute('''
                    UPDATE badges
                    SET earned = 1, earned_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (badge_dict['id'],))
                newly_earned.append(badge_dict['name'])
            
            elif badge_dict['name'] == 'Perfect Score':
                cursor.execute('SELECT * FROM quiz_results WHERE score = total LIMIT 1')
                if cursor.fetchone():
                    cursor.execute('''
                        UPDATE badges
                        SET earned = 1, earned_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    ''', (badge_dict['id'],))
                    newly_earned.append(badge_dict['name'])
        
        conn.commit()
        conn.close()
        return newly_earned
    
    @staticmethod
    def get_all():
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM badges ORDER BY requirement')
        badges = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return badges
