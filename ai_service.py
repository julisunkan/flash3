import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def generate_summary(text, max_words=200):
    """Generate a concise summary of the input text"""
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": f"You are a helpful assistant that creates concise summaries. Limit your summary to {max_words} words."},
                {"role": "user", "content": f"Please summarize the following text:\n\n{text}"}
            ],
            max_tokens=500,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error generating summary: {str(e)}"

def generate_flashcards(text, num_cards=10):
    """Generate question-answer flashcards from text"""
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert educator that creates effective study flashcards. Generate clear, concise questions and answers."},
                {"role": "user", "content": f"Create {num_cards} flashcard question-answer pairs from this text. Format each as 'Q: [question]\\nA: [answer]\\n\\n'. Focus on key concepts and important information.\n\nText:\n{text}"}
            ],
            max_tokens=2000,
            temperature=0.8
        )
        
        content = response.choices[0].message.content.strip()
        flashcards = []
        
        pairs = content.split('\n\n')
        for pair in pairs:
            if 'Q:' in pair and 'A:' in pair:
                lines = pair.strip().split('\n')
                question = ''
                answer = ''
                
                for line in lines:
                    if line.startswith('Q:'):
                        question = line.replace('Q:', '').strip()
                    elif line.startswith('A:'):
                        answer = line.replace('A:', '').strip()
                
                if question and answer:
                    flashcards.append({
                        'question': question,
                        'answer': answer
                    })
        
        return flashcards[:num_cards]
    except Exception as e:
        return [{'question': f'Error: {str(e)}', 'answer': 'Please check your API key and try again.'}]

def generate_multiple_choice(text, num_questions=5):
    """Generate multiple choice questions from text"""
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert test creator. Generate challenging multiple choice questions with exactly 4 options each."},
                {"role": "user", "content": f"Create {num_questions} multiple choice questions from this text. Format each as:\nQ: [question]\nA) [option 1]\nB) [option 2]\nC) [option 3]\nD) [option 4]\nCorrect: [A/B/C/D]\n\nText:\n{text}"}
            ],
            max_tokens=2000,
            temperature=0.8
        )
        
        content = response.choices[0].message.content.strip()
        questions = []
        
        blocks = content.split('\n\n')
        for block in blocks:
            lines = block.strip().split('\n')
            if len(lines) >= 6:
                question = ''
                choices = []
                correct = ''
                
                for line in lines:
                    if line.startswith('Q:'):
                        question = line.replace('Q:', '').strip()
                    elif line.startswith(('A)', 'B)', 'C)', 'D)')):
                        choices.append(line[3:].strip())
                    elif line.startswith('Correct:'):
                        correct = line.replace('Correct:', '').strip()
                
                if question and len(choices) == 4 and correct:
                    correct_index = {'A': 0, 'B': 1, 'C': 2, 'D': 3}.get(correct, 0)
                    questions.append({
                        'question': question,
                        'choices': choices,
                        'answer': choices[correct_index]
                    })
        
        return questions[:num_questions]
    except Exception as e:
        return [{
            'question': f'Error: {str(e)}',
            'choices': ['Option 1', 'Option 2', 'Option 3', 'Option 4'],
            'answer': 'Please check your API key and try again.'
        }]
