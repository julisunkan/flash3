import re
import os
import google.generativeai as genai

# Configure Gemini API
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    model = None

def generate_summary(text, max_words=200):
    """Generate a concise summary using Gemini API"""
    if not model:
        return "Please set GEMINI_API_KEY environment variable to use AI generation."

    try:
        prompt = f"""Please provide a concise summary of the following text in approximately {max_words} words:

{text}

Summary:"""

        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"Error generating summary: {str(e)}"

def generate_flashcards(text, num_cards=10):
    """Generate question-answer flashcards using Gemini API"""
    if not model:
        return [{
            'question': 'API Key Required',
            'answer': 'Please set GEMINI_API_KEY environment variable to use AI generation.'
        }]

    try:
        prompt = f"""Generate {num_cards} high-quality flashcards from the following text. Each flashcard should have a clear question and a concise answer.

Text:
{text}

Return the flashcards in the following JSON format:
[
  {{"question": "Question text here?", "answer": "Answer text here"}},
  {{"question": "Another question?", "answer": "Another answer"}}
]

Generate exactly {num_cards} flashcards. Make sure questions are specific and answers are informative but concise."""

        response = model.generate_content(prompt)
        result_text = response.text.strip()

        # Extract JSON from response (remove markdown code blocks if present)
        if '```json' in result_text:
            result_text = result_text.split('```json')[1].split('```')[0].strip()
        elif '```' in result_text:
            result_text = result_text.split('```')[1].split('```')[0].strip()

        import json
        flashcards = json.loads(result_text)

        # Validate structure
        if not isinstance(flashcards, list):
            raise ValueError("Invalid response format")

        for card in flashcards:
            if not isinstance(card, dict) or 'question' not in card or 'answer' not in card:
                raise ValueError("Invalid flashcard format")

        return flashcards[:num_cards]

    except Exception as e:
        return [{
            'question': 'Error generating flashcards',
            'answer': f'Please try again. Error: {str(e)}'
        }]

def generate_multiple_choice(text, num_questions=5):
    """Generate multiple choice questions using Gemini API"""
    if not model:
        return [{
            'question': 'API Key Required',
            'choices': ['Set GEMINI_API_KEY', 'In environment variables', 'To use this feature', 'Check the Secrets tool'],
            'answer': 'Set GEMINI_API_KEY'
        }]

    try:
        prompt = f"""Generate {num_questions} multiple choice questions from the following text. Each question should have 4 choices with one correct answer.

Text:
{text}

Return the questions in the following JSON format:
[
  {{
    "question": "Question text here?",
    "choices": ["Choice A", "Choice B", "Choice C", "Choice D"],
    "answer": "Choice A"
  }}
]

Generate exactly {num_questions} questions. Make sure the correct answer is one of the choices."""

        response = model.generate_content(prompt)
        result_text = response.text.strip()

        # Extract JSON from response
        if '```json' in result_text:
            result_text = result_text.split('```json')[1].split('```')[0].strip()
        elif '```' in result_text:
            result_text = result_text.split('```')[1].split('```')[0].strip()

        import json
        questions = json.loads(result_text)

        # Validate structure
        if not isinstance(questions, list):
            raise ValueError("Invalid response format")

        for q in questions:
            if not isinstance(q, dict) or 'question' not in q or 'choices' not in q or 'answer' not in q:
                raise ValueError("Invalid question format")
            if not isinstance(q['choices'], list) or len(q['choices']) < 2:
                raise ValueError("Invalid choices format")

        return questions[:num_questions]

    except Exception as e:
        return [{
            'question': 'Error generating questions',
            'choices': ['Try again', 'Check API key', 'Verify text input', 'Contact support'],
            'answer': 'Try again'
        }]