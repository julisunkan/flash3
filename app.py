import os
from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename
import json
import csv
from io import StringIO
from datetime import datetime

from models import init_db, Deck, Card, StudySession, QuizResult, Badge
from ai_service import generate_summary, generate_flashcards, generate_multiple_choice
from utils import process_pdf_file, allowed_file, clean_text

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SESSION_SECRET', 'dev-secret-key-change-in-production')
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/decks', methods=['GET', 'POST'])
def handle_decks():
    if request.method == 'GET':
        decks = Deck.get_all()
        return jsonify(decks)
    
    elif request.method == 'POST':
        data = request.json
        deck_id = Deck.create(data['name'], data.get('description', ''))
        return jsonify({'id': deck_id, 'message': 'Deck created successfully'})

@app.route('/api/decks/<int:deck_id>', methods=['GET', 'DELETE'])
def handle_deck(deck_id):
    if request.method == 'GET':
        deck = Deck.get_by_id(deck_id)
        if deck:
            return jsonify(deck)
        return jsonify({'error': 'Deck not found'}), 404
    
    elif request.method == 'DELETE':
        Deck.delete(deck_id)
        return jsonify({'message': 'Deck deleted successfully'})

@app.route('/api/decks/<int:deck_id>/cards', methods=['GET', 'POST'])
def handle_cards(deck_id):
    if request.method == 'GET':
        cards = Card.get_by_deck(deck_id)
        return jsonify(cards)
    
    elif request.method == 'POST':
        data = request.json
        card_id = Card.create(
            deck_id,
            data['question'],
            data['answer'],
            data.get('choices')
        )
        return jsonify({'id': card_id, 'message': 'Card created successfully'})

@app.route('/api/cards/<int:card_id>', methods=['DELETE'])
def delete_card(card_id):
    Card.delete(card_id)
    return jsonify({'message': 'Card deleted successfully'})

@app.route('/api/process-text', methods=['POST'])
def process_text():
    data = request.json
    text = clean_text(data.get('text', ''))
    action = data.get('action', 'flashcards')
    
    if not text:
        return jsonify({'error': 'No text provided'}), 400
    
    if action == 'summary':
        result = generate_summary(text)
        return jsonify({'summary': result})
    
    elif action == 'flashcards':
        num_cards = data.get('num_cards', 10)
        flashcards = generate_flashcards(text, num_cards)
        return jsonify({'flashcards': flashcards})
    
    elif action == 'multiple_choice':
        num_questions = data.get('num_questions', 5)
        questions = generate_multiple_choice(text, num_questions)
        return jsonify({'questions': questions})
    
    return jsonify({'error': 'Invalid action'}), 400

@app.route('/api/upload-pdf', methods=['POST'])
def upload_pdf():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        try:
            text = process_pdf_file(filepath)
            
            os.remove(filepath)
            
            if text:
                return jsonify({'text': clean_text(text), 'message': 'PDF processed successfully'})
            else:
                return jsonify({'error': 'Could not extract text from PDF'}), 400
        except Exception as e:
            if os.path.exists(filepath):
                os.remove(filepath)
            return jsonify({'error': f'Error processing PDF: {str(e)}'}), 500
    
    return jsonify({'error': 'Invalid file type. Only PDF and TXT files are allowed.'}), 400

@app.route('/api/study/<int:card_id>', methods=['POST'])
def study_card(card_id):
    data = request.json
    quality = data.get('quality', 3)
    
    StudySession.update(card_id, quality)
    
    newly_earned = Badge.check_and_award()
    
    return jsonify({
        'message': 'Study session recorded',
        'badges_earned': newly_earned
    })

@app.route('/api/decks/<int:deck_id>/due-cards', methods=['GET'])
def get_due_cards(deck_id):
    cards = Card.get_due_cards(deck_id)
    return jsonify(cards)

@app.route('/api/quiz-results', methods=['POST'])
def save_quiz_result():
    data = request.json
    QuizResult.save(data['deck_id'], data['score'], data['total'])
    
    newly_earned = Badge.check_and_award()
    
    return jsonify({
        'message': 'Quiz result saved',
        'badges_earned': newly_earned
    })

@app.route('/api/decks/<int:deck_id>/quiz-results', methods=['GET'])
def get_quiz_results(deck_id):
    results = QuizResult.get_by_deck(deck_id)
    return jsonify(results)

@app.route('/api/stats', methods=['GET'])
def get_stats():
    stats = StudySession.get_stats()
    return jsonify(stats)

@app.route('/api/badges', methods=['GET'])
def get_badges():
    badges = Badge.get_all()
    return jsonify(badges)

@app.route('/api/export/<int:deck_id>/<format>', methods=['GET'])
def export_deck(deck_id, format):
    deck = Deck.get_by_id(deck_id)
    cards = Card.get_by_deck(deck_id)
    
    if not deck:
        return jsonify({'error': 'Deck not found'}), 404
    
    if format == 'json':
        data = {
            'deck': deck,
            'cards': cards
        }
        return jsonify(data)
    
    elif format == 'csv':
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['Question', 'Answer'])
        
        for card in cards:
            writer.writerow([card['question'], card['answer']])
        
        output.seek(0)
        return output.getvalue(), 200, {
            'Content-Type': 'text/csv',
            'Content-Disposition': f'attachment; filename={deck["name"]}.csv'
        }
    
    elif format == 'anki':
        output = StringIO()
        for card in cards:
            output.write(f"{card['question']}\t{card['answer']}\n")
        
        output.seek(0)
        return output.getvalue(), 200, {
            'Content-Type': 'text/plain',
            'Content-Disposition': f'attachment; filename={deck["name"]}_anki.txt'
        }
    
    return jsonify({'error': 'Invalid format'}), 400

@app.route('/deck/<int:deck_id>')
def deck_page(deck_id):
    return render_template('deck.html', deck_id=deck_id)

@app.route('/study/<int:deck_id>')
def study_page(deck_id):
    return render_template('study.html', deck_id=deck_id)

@app.route('/quiz/<int:deck_id>')
def quiz_page(deck_id):
    return render_template('quiz.html', deck_id=deck_id)

@app.route('/analytics')
def analytics_page():
    return render_template('analytics.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
