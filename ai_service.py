import re

def extract_keywords(text, num_keywords=10):
    """Extract important keywords from text"""
    words = re.findall(r'\b[A-Za-z]{4,}\b', text.lower())
    word_freq = {}
    for word in words:
        if word not in ['this', 'that', 'with', 'from', 'have', 'been', 'were', 'will', 'their', 'what', 'when', 'where', 'which']:
            word_freq[word] = word_freq.get(word, 0) + 1
    
    sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
    return [word for word, _ in sorted_words[:num_keywords]]

def generate_summary(text, max_words=200):
    """Generate a concise summary of the input text using extractive summarization"""
    try:
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
        
        if not sentences:
            return "Text is too short to summarize."
        
        keywords = extract_keywords(text, 15)
        
        scored_sentences = []
        for sentence in sentences[:50]:
            score = sum(1 for keyword in keywords if keyword in sentence.lower())
            if score > 0:
                scored_sentences.append((score, sentence))
        
        scored_sentences.sort(reverse=True, key=lambda x: x[0])
        
        summary_sentences = [sent for _, sent in scored_sentences[:5]]
        summary = '. '.join(summary_sentences)
        
        if len(summary) > max_words * 7:
            summary = summary[:max_words * 7] + '...'
        
        return summary if summary else sentences[0]
    except Exception as e:
        return f"Could not generate summary. Please try again."

def generate_flashcards(text, num_cards=10):
    """Generate question-answer flashcards from text using intelligent extraction"""
    try:
        return generate_simple_flashcards(text, num_cards)
    except Exception as e:
        return [{'question': 'Error generating flashcards', 'answer': 'Please try with different text.'}]

def generate_multiple_choice(text, num_questions=5):
    """Generate multiple choice questions from text"""
    try:
        return generate_simple_mcq(text, num_questions)
    except Exception as e:
        return [{'question': 'Error generating questions', 'choices': ['Option 1', 'Option 2', 'Option 3', 'Option 4'], 'answer': 'Option 1'}]

def generate_simple_flashcards(text, num_cards=10):
    """Generate high-quality flashcards from text using intelligent extraction"""
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if 30 <= len(s.strip()) <= 300]
    
    if not sentences:
        return [{'question': 'What is the main topic?', 'answer': text[:200]}]
    
    flashcards = []
    keywords = extract_keywords(text, 25)
    
    for i, sentence in enumerate(sentences[:num_cards * 3]):
        words = sentence.split()
        if len(words) < 7 or len(words) > 40:
            continue
        
        keyword_in_sentence = [k for k in keywords if k in sentence.lower()]
        if not keyword_in_sentence or len(keyword_in_sentence) < 1:
            continue
        
        main_keyword = keyword_in_sentence[0]
        
        if main_keyword.capitalize() in sentence:
            question = f"Define or explain: {main_keyword.capitalize()}"
            answer = sentence
        else:
            question_patterns = [
                f"What is {main_keyword}?",
                f"Explain {main_keyword}.",
                f"What does the text say about {main_keyword}?",
                f"Describe {main_keyword}."
            ]
            question = question_patterns[i % len(question_patterns)]
            answer = sentence
        
        if answer and len(answer) > 20:
            flashcards.append({'question': question, 'answer': answer})
        
        if len(flashcards) >= num_cards:
            break
    
    if len(flashcards) < num_cards and len(sentences) > 0:
        for sentence in sentences[:num_cards]:
            if len(flashcards) >= num_cards:
                break
            if len(sentence) > 20:
                words = sentence.split()[:7]
                question_start = ' '.join(words) + '...'
                flashcards.append({
                    'question': f'Complete: "{question_start}"',
                    'answer': sentence
                })
    
    return flashcards[:num_cards]

def generate_simple_mcq(text, num_questions=5):
    """Generate multiple choice questions from text"""
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 30]
    
    if not sentences or len(sentences) < 2:
        return [{
            'question': 'What does the text discuss?',
            'choices': ['The main topic', 'Something else', 'Nothing specific', 'Multiple topics'],
            'answer': 'The main topic'
        }]
    
    questions = []
    keywords = extract_keywords(text, 15)
    
    for i, sentence in enumerate(sentences[:num_questions]):
        words = sentence.split()
        if len(words) < 5:
            continue
        
        keyword_in_sentence = [k for k in keywords if k in sentence.lower()]
        if not keyword_in_sentence:
            keyword_in_sentence = [words[min(2, len(words)-1)]]
        
        distractors = []
        for other_sentence in sentences:
            if other_sentence != sentence and len(distractors) < 2:
                distractor_words = other_sentence.split()
                if len(distractor_words) > 3:
                    distractors.append(' '.join(distractor_words[:8]) + '...')
        
        while len(distractors) < 3:
            distractors.append(f"This is not mentioned in the text")
        
        question_text = f"What information is provided about {keyword_in_sentence[0]}?"
        choices = [sentence, distractors[0], distractors[1], distractors[2]]
        
        import random
        combined = list(zip(choices, [0, 1, 2, 3]))
        random.shuffle(combined)
        shuffled_choices, indices = zip(*combined)
        correct_answer = shuffled_choices[indices.index(0)]
        
        questions.append({
            'question': question_text,
            'choices': list(shuffled_choices),
            'answer': correct_answer
        })
    
    return questions[:num_questions]
