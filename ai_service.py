import re
import os
import google.generativeai as genai

# Configure Gemini API
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-2.0-flash')
else:
    model = None

def generate_summary(text, max_words=200, user_api_key=None):
    """Generate a concise summary using Gemini API"""
    current_model = model
    
    if user_api_key:
        try:
            genai.configure(api_key=user_api_key)
            current_model = genai.GenerativeModel('gemini-2.0-flash')
        except Exception as e:
            return f"Error with provided API key: {str(e)}"
    elif not model:
        return "Please configure your Gemini API key in Settings to use AI generation."

    try:
        prompt = f"""You are an expert content summarizer. Create a well-structured, professional summary of the following text in approximately {max_words} words.

Requirements:
- Organize the summary into clear, logical paragraphs (2-4 paragraphs recommended)
- Each paragraph should cover a distinct main idea or theme
- Use proper spacing between paragraphs (double line breaks)
- Write in clear, professional language
- Maintain proper grammar and punctuation
- Start with an overview, then cover key points in subsequent paragraphs
- Conclude with the most important takeaway if space allows

Text:
{text}

Provide a well-formatted summary with clear paragraph breaks:"""

        response = current_model.generate_content(prompt)
        
        if GEMINI_API_KEY and user_api_key:
            genai.configure(api_key=GEMINI_API_KEY)
        
        summary = response.text.strip()
        
        # Ensure proper paragraph formatting
        # Replace single newlines with double newlines for better spacing
        summary = re.sub(r'\n(?!\n)', '\n\n', summary)
        # Remove any triple or more newlines
        summary = re.sub(r'\n{3,}', '\n\n', summary)
        
        return summary
    except Exception as e:
        if GEMINI_API_KEY and user_api_key:
            genai.configure(api_key=GEMINI_API_KEY)
        return f"Error generating summary: {str(e)}"

def generate_flashcards(text, num_cards=10, user_api_key=None):
    """Generate question-answer flashcards using Gemini API"""
    current_model = model
    
    if user_api_key:
        try:
            genai.configure(api_key=user_api_key)
            current_model = genai.GenerativeModel('gemini-2.0-flash')
        except Exception as e:
            return [{
                'question': 'API Key Error',
                'answer': f'Error with provided API key: {str(e)}'
            }]
    elif not model:
        return [{
            'question': 'API Key Required',
            'answer': 'Please configure your Gemini API key in Settings to use AI generation.'
        }]

    try:
        prompt = f"""You are an expert educational content creator. Generate {num_cards} professional, high-quality flashcards from the following text.

Requirements:
- Each question should be clear, specific, and test understanding of key concepts
- Questions should be properly formatted and grammatically correct
- Answers should be concise yet comprehensive (2-4 sentences maximum)
- Focus on the most important information and concepts
- Use professional academic language
- Ensure questions and answers are clearly separated

Text:
{text}

Return the flashcards in the following JSON format:
[
  {{"question": "What is the primary function of X?", "answer": "The primary function of X is to perform Y, which enables Z."}},
  {{"question": "How does A relate to B?", "answer": "A relates to B through the process of C, resulting in D."}}
]

Generate exactly {num_cards} flashcards. Make each question thought-provoking and each answer informative."""

        response = current_model.generate_content(prompt)
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

        if GEMINI_API_KEY and user_api_key:
            genai.configure(api_key=GEMINI_API_KEY)
        
        return flashcards[:num_cards]

    except Exception as e:
        if GEMINI_API_KEY and user_api_key:
            genai.configure(api_key=GEMINI_API_KEY)
        return [{
            'question': 'Error generating flashcards',
            'answer': f'Please try again. Error: {str(e)}'
        }]

def generate_multiple_choice(text, num_questions=5, user_api_key=None):
    """Generate multiple choice questions using Gemini API"""
    current_model = model
    
    if user_api_key:
        try:
            genai.configure(api_key=user_api_key)
            current_model = genai.GenerativeModel('gemini-2.0-flash')
        except Exception as e:
            return [{
                'question': 'API Key Error',
                'choices': ['Check your API key', 'In Settings', 'Try again', 'Visit Google AI Studio'],
                'answer': 'Check your API key'
            }]
    elif not model:
        return [{
            'question': 'API Key Required',
            'choices': ['Go to Settings', 'Add your Gemini API key', 'Get free key from Google', 'Try again'],
            'answer': 'Go to Settings'
        }]

    try:
        prompt = f"""You are an expert educational assessment designer. Create {num_questions} professional, high-quality multiple choice questions from the following text.

Requirements:
- Each question should test comprehension and critical thinking
- Questions must be clear, specific, and professionally written
- Provide exactly 4 answer choices for each question (A, B, C, D)
- The correct answer should be accurate and clearly supported by the text
- Incorrect choices (distractors) should be plausible but clearly wrong
- Avoid obvious patterns or giveaways
- Use professional academic language
- Ensure proper grammar and formatting

Text:
{text}

Return the questions in the following JSON format:
[
  {{
    "question": "What is the primary mechanism by which X achieves Y?",
    "choices": [
      "Through process A which involves detailed mechanism",
      "By utilizing method B in a specific way",
      "Via pathway C that connects to system D",
      "Using technique E combined with factor F"
    ],
    "answer": "Through process A which involves detailed mechanism"
  }}
]

Generate exactly {num_questions} questions. Ensure all choices are substantive and the correct answer is one of the four choices provided."""

        response = current_model.generate_content(prompt)
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

        if GEMINI_API_KEY and user_api_key:
            genai.configure(api_key=GEMINI_API_KEY)
        
        return questions[:num_questions]

    except Exception as e:
        if GEMINI_API_KEY and user_api_key:
            genai.configure(api_key=GEMINI_API_KEY)
        return [{
            'question': 'Error generating questions',
            'choices': ['Try again', 'Check API key', 'Verify text input', 'Visit Settings'],
            'answer': 'Try again'
        }]