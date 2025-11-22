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
from pdf_generator import generate_flashcards_pdf

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SESSION_SECRET', 'dev-secret-key-change-in-production')
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

init_db()

@app.after_request
def add_header(response):
    """Add headers to prevent caching"""
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    return response

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
        if not request.json:
            return jsonify({'error': 'Invalid request'}), 400
        
        data = request.json
        question = data.get('question', '').strip()
        answer = data.get('answer', '').strip()
        
        if not question or not answer:
            return jsonify({'error': 'Question and answer are required'}), 400
        
        if len(question) > 1000 or len(answer) > 2000:
            return jsonify({'error': 'Question or answer too long'}), 400
        
        try:
            card_id = Card.create(
                deck_id,
                question,
                answer,
                data.get('choices')
            )
            return jsonify({'id': card_id, 'message': 'Card created successfully'})
        except Exception as e:
            return jsonify({'error': 'Failed to create card'}), 500

@app.route('/api/cards/<int:card_id>', methods=['DELETE'])
def delete_card(card_id):
    Card.delete(card_id)
    return jsonify({'message': 'Card deleted successfully'})

@app.route('/api/process-text', methods=['POST'])
def process_text():
    if not request.json:
        return jsonify({'error': 'Invalid request'}), 400
    
    data = request.json
    text = clean_text(data.get('text', ''))
    action = data.get('action', 'flashcards')
    
    if not text:
        return jsonify({'error': 'No text provided'}), 400
    
    if len(text) < 50:
        return jsonify({'error': 'Text too short. Please provide at least 50 characters.'}), 400
    
    try:
        user_api_key = data.get('api_key')
        
        if action == 'summary':
            result = generate_summary(text, user_api_key=user_api_key)
            return jsonify({'summary': result})
        
        elif action == 'flashcards':
            num_cards = min(int(data.get('num_cards', 10)), 50)
            flashcards = generate_flashcards(text, num_cards, user_api_key=user_api_key)
            return jsonify({'flashcards': flashcards})
        
        elif action == 'multiple_choice':
            num_questions = min(int(data.get('num_questions', 5)), 25)
            questions = generate_multiple_choice(text, num_questions, user_api_key=user_api_key)
            return jsonify({'questions': questions})
        
        else:
            return jsonify({'error': 'Invalid action'}), 400
    except Exception as e:
        return jsonify({'error': 'Failed to process text'}), 500

@app.route('/api/upload-pdf', methods=['POST'])
def upload_pdf():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not file or not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type. Only PDF files are allowed.'}), 400
    
    if file.content_length and file.content_length > app.config['MAX_CONTENT_LENGTH']:
        return jsonify({'error': 'File too large. Maximum size is 16MB.'}), 400
    
    filename = secure_filename(file.filename)
    import uuid
    unique_filename = f"{uuid.uuid4()}_{filename}"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
    
    try:
        file.save(filepath)
        
        if not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
            return jsonify({'error': 'File upload failed'}), 500
        
        if os.path.getsize(filepath) > 16 * 1024 * 1024:
            os.remove(filepath)
            return jsonify({'error': 'File too large'}), 400
        
        text = process_pdf_file(filepath)
        
        os.remove(filepath)
        
        if text and len(text.strip()) > 0:
            return jsonify({'text': clean_text(text), 'message': 'PDF processed successfully'})
        else:
            return jsonify({'error': 'Could not extract text from PDF. File may be scanned or empty.'}), 400
    except Exception as e:
        if os.path.exists(filepath):
            os.remove(filepath)
        return jsonify({'error': 'Error processing PDF. Please try again.'}), 500

@app.route('/api/test-gemini', methods=['POST'])
def test_gemini():
    if not request.json:
        return jsonify({'error': 'Invalid request'}), 400
    
    api_key = request.json.get('api_key')
    
    if not api_key:
        return jsonify({'error': 'No API key provided'}), 400
    
    try:
        import google.generativeai as genai
        
        GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
        
        genai.configure(api_key=api_key)
        test_model = genai.GenerativeModel('gemini-2.0-flash')
        
        response = test_model.generate_content("Say hello")
        
        if GEMINI_API_KEY:
            genai.configure(api_key=GEMINI_API_KEY)
        
        return jsonify({'message': 'API key is valid', 'test_response': response.text})
    except Exception as e:
        GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
        if GEMINI_API_KEY:
            genai.configure(api_key=GEMINI_API_KEY)
        return jsonify({'error': f'API key test failed: {str(e)}'}), 400

@app.route('/api/study/<int:card_id>', methods=['POST'])
def study_card(card_id):
    if not request.json:
        return jsonify({'error': 'Invalid request'}), 400
    
    data = request.json
    quality = data.get('quality', 3)
    
    try:
        quality = int(quality)
        if quality < 0 or quality > 5:
            return jsonify({'error': 'Quality must be between 0 and 5'}), 400
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid quality value'}), 400
    
    try:
        StudySession.update(card_id, quality)
        newly_earned = Badge.check_and_award()
        
        return jsonify({
            'message': 'Study session recorded',
            'badges_earned': newly_earned
        })
    except Exception as e:
        return jsonify({'error': 'Failed to record study session'}), 500

@app.route('/api/decks/<int:deck_id>/due-cards', methods=['GET'])
def get_due_cards(deck_id):
    cards = Card.get_due_cards(deck_id)
    return jsonify(cards)

@app.route('/settings')
def settings_page():
    return render_template('settings.html')

@app.route('/api/quiz-results', methods=['POST'])
def save_quiz_result():
    if not request.json:
        return jsonify({'error': 'Invalid request'}), 400
    
    data = request.json
    
    try:
        deck_id = int(data.get('deck_id', 0))
        score = int(data.get('score', 0))
        total = int(data.get('total', 0))
        
        if deck_id <= 0 or score < 0 or total <= 0 or score > total:
            return jsonify({'error': 'Invalid quiz data'}), 400
        
        QuizResult.save(deck_id, score, total)
        newly_earned = Badge.check_and_award()
        
        return jsonify({
            'message': 'Quiz result saved',
            'badges_earned': newly_earned
        })
    except (ValueError, TypeError, KeyError) as e:
        return jsonify({'error': 'Invalid request data'}), 400
    except Exception as e:
        return jsonify({'error': 'Failed to save quiz result'}), 500

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
    
    # Sanitize filename
    safe_deck_name = "".join(c for c in deck['name'] if c.isalnum() or c in (' ', '-', '_')).strip()
    
    if format == 'json':
        data = {
            'deck': deck,
            'cards': cards
        }
        from flask import Response
        import json as json_lib
        
        response = Response(
            json_lib.dumps(data, indent=2),
            mimetype='application/json',
            headers={
                'Content-Disposition': f'attachment; filename={safe_deck_name or "deck"}.json'
            }
        )
        return response
    
    elif format == 'csv':
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['Question', 'Answer'])
        
        for card in cards:
            writer.writerow([card['question'], card['answer']])
        
        output.seek(0)
        return output.getvalue(), 200, {
            'Content-Type': 'text/csv',
            'Content-Disposition': f'attachment; filename={safe_deck_name or "deck"}.csv'
        }
    
    elif format == 'anki':
        output = StringIO()
        for card in cards:
            output.write(f"{card['question']}\t{card['answer']}\n")
        
        output.seek(0)
        return output.getvalue(), 200, {
            'Content-Type': 'text/plain',
            'Content-Disposition': f'attachment; filename={safe_deck_name or "deck"}_anki.txt'
        }
    
    elif format == 'pdf':
        # Convert cards to the format expected by PDF generator
        pdf_cards = []
        for card in cards:
            pdf_card = {
                'question': card['question'],
                'answer': card['answer']
            }
            if card.get('choices'):
                try:
                    pdf_card['choices'] = json.loads(card['choices'])
                except:
                    pass
            pdf_cards.append(pdf_card)
        
        try:
            pdf_buffer = generate_flashcards_pdf(pdf_cards, deck['name'])
            
            return send_file(
                pdf_buffer,
                mimetype='application/pdf',
                as_attachment=True,
                download_name=f"{safe_deck_name or 'deck'}_flashcards.pdf"
            )
        except Exception as e:
            print(f"PDF generation error: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({'error': f'Failed to generate PDF: {str(e)}'}), 500
    
    return jsonify({'error': 'Invalid format'}), 400

@app.route('/api/export-cards-pdf', methods=['POST'])
def export_cards_pdf():
    """Export generated cards to PDF"""
    if not request.json:
        return jsonify({'error': 'Invalid request'}), 400
    
    cards = request.json.get('cards', [])
    deck_name = request.json.get('deck_name', 'Flashcards')
    
    # Validate input
    if not cards or not isinstance(cards, list):
        return jsonify({'error': 'No cards provided'}), 400
    
    if len(cards) > 100:
        return jsonify({'error': 'Cannot export more than 100 cards at once'}), 400
    
    if not isinstance(deck_name, str):
        deck_name = 'Flashcards'
    
    # Validate total payload size
    total_size = len(str(cards))
    if total_size > 1_000_000:  # 1MB limit for total payload
        return jsonify({'error': 'Payload too large'}), 400
    
    # Validate each card structure
    for i, card in enumerate(cards):
        if not isinstance(card, dict):
            return jsonify({'error': f'Card {i+1} is invalid'}), 400
        
        if 'question' not in card or 'answer' not in card:
            return jsonify({'error': f'Card {i+1} is missing required fields'}), 400
        
        if not isinstance(card['question'], str) or not isinstance(card['answer'], str):
            return jsonify({'error': f'Card {i+1} has invalid field types'}), 400
        
        # Trim and validate length
        question = card['question'].strip()
        answer = card['answer'].strip()
        
        if not question or not answer:
            return jsonify({'error': f'Card {i+1} has empty question or answer'}), 400
        
        if len(question) > 10000 or len(answer) > 10000:
            return jsonify({'error': f'Card {i+1} fields are too long (max 10,000 characters)'}), 400
        
        # Update card with trimmed values
        card['question'] = question
        card['answer'] = answer
        
        # Validate choices if present
        if 'choices' in card:
            if not isinstance(card['choices'], list):
                return jsonify({'error': f'Card {i+1} has invalid choices format'}), 400
            
            if len(card['choices']) > 10:
                return jsonify({'error': f'Card {i+1} has too many choices (max 10)'}), 400
            
            trimmed_choices = []
            for choice in card['choices']:
                if not isinstance(choice, str):
                    return jsonify({'error': f'Card {i+1} has invalid choice format'}), 400
                
                trimmed_choice = choice.strip()
                if not trimmed_choice:
                    return jsonify({'error': f'Card {i+1} has empty choice'}), 400
                
                if len(trimmed_choice) > 5000:
                    return jsonify({'error': f'Card {i+1} has choice that is too long (max 5,000 characters)'}), 400
                
                trimmed_choices.append(trimmed_choice)
            
            card['choices'] = trimmed_choices
    
    try:
        pdf_buffer = generate_flashcards_pdf(cards, deck_name)
        
        # Sanitize filename
        safe_filename = "".join(c for c in deck_name if c.isalnum() or c in (' ', '-', '_')).strip()
        filename = f"{safe_filename or 'Flashcards'}_flashcards.pdf"
        
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Failed to generate PDF. Please try again.'}), 500

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

@app.route('/sw.js')
def service_worker():
    return send_file('sw.js', mimetype='application/javascript')

@app.errorhandler(404)
def not_found(error):
    # If it's an API request, return JSON
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Route not found'}), 404
    
    # For HTML requests, redirect to home page
    from flask import redirect
    return redirect('/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
