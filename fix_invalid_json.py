
import sqlite3
import json

DATABASE = 'flashcards.db'

def fix_invalid_json():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Get all cards with choices
    cursor.execute('SELECT id, choices FROM cards WHERE choices IS NOT NULL')
    cards = cursor.fetchall()
    
    fixed_count = 0
    for card_id, choices in cards:
        if choices:
            try:
                # Try to parse as JSON
                json.loads(choices)
            except json.JSONDecodeError:
                # Invalid JSON, set to NULL
                print(f"Fixing card {card_id}: Invalid JSON detected")
                cursor.execute('UPDATE cards SET choices = NULL WHERE id = ?', (card_id,))
                fixed_count += 1
    
    conn.commit()
    conn.close()
    
    print(f"\nFixed {fixed_count} cards with invalid JSON")
    print("Database cleanup complete!")

if __name__ == '__main__':
    fix_invalid_json()
