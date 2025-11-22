
import re
import random

def extract_keywords(text, num_keywords=10):
    """Extract important keywords from text"""
    words = re.findall(r'\b[A-Za-z]{4,}\b', text.lower())
    word_freq = {}
    
    stopwords = {'this', 'that', 'with', 'from', 'have', 'been', 'were', 'will', 
                 'their', 'what', 'when', 'where', 'which', 'would', 'could', 
                 'should', 'about', 'there', 'these', 'those', 'being', 'then'}
    
    for word in words:
        if word not in stopwords and len(word) > 3:
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
        # Clean and prepare text
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if 20 <= len(s.strip()) <= 500]
        
        if len(sentences) < 2:
            return [{
                'question': 'What is the main topic of this text?',
                'answer': text[:300] if len(text) > 300 else text
            }]
        
        flashcards = []
        keywords = extract_keywords(text, 30)
        
        # Method 1: Create definition-style cards from sentences with keywords
        for sentence in sentences:
            if len(flashcards) >= num_cards:
                break
                
            sentence_words = sentence.lower().split()
            matching_keywords = [k for k in keywords if k in sentence.lower()]
            
            if matching_keywords and len(sentence_words) > 5:
                keyword = matching_keywords[0]
                
                # Create various question types
                question_types = [
                    f"What does the text say about {keyword}?",
                    f"According to the text, what is {keyword}?",
                    f"Define or explain {keyword} based on the text.",
                    f"What information is provided about {keyword}?"
                ]
                
                flashcards.append({
                    'question': random.choice(question_types),
                    'answer': sentence
                })
        
        # Method 2: Fill-in-the-blank style cards
        if len(flashcards) < num_cards:
            for sentence in sentences:
                if len(flashcards) >= num_cards:
                    break
                
                if sentence in [c['answer'] for c in flashcards]:
                    continue
                    
                words = sentence.split()
                if 8 <= len(words) <= 30:
                    # Take first part as question
                    split_point = len(words) // 2
                    question_part = ' '.join(words[:split_point]) + '...'
                    
                    flashcards.append({
                        'question': f'Complete this statement: "{question_part}"',
                        'answer': sentence
                    })
        
        # Method 3: Key concept extraction
        if len(flashcards) < num_cards:
            for keyword in keywords:
                if len(flashcards) >= num_cards:
                    break
                
                # Find sentences mentioning this keyword
                relevant_sentences = [s for s in sentences if keyword in s.lower()]
                if relevant_sentences:
                    answer = relevant_sentences[0]
                    if answer not in [c['answer'] for c in flashcards]:
                        flashcards.append({
                            'question': f"What key concept relates to '{keyword}'?",
                            'answer': answer
                        })
        
        # Ensure we have at least some cards
        if len(flashcards) == 0:
            for i, sentence in enumerate(sentences[:num_cards]):
                flashcards.append({
                    'question': f'Question {i+1}: What does this part of the text describe?',
                    'answer': sentence
                })
        
        return flashcards[:num_cards]
        
    except Exception as e:
        return [{'question': 'Error generating flashcards', 'answer': 'Please try with different text.'}]

def generate_multiple_choice(text, num_questions=5):
    """Generate multiple choice questions from text"""
    try:
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if 30 <= len(s.strip()) <= 400]
        
        if len(sentences) < 2:
            return [{
                'question': 'What does the text discuss?',
                'choices': ['The main topic', 'Something else', 'Nothing specific', 'Multiple topics'],
                'answer': 'The main topic'
            }]
        
        questions = []
        keywords = extract_keywords(text, 20)
        
        # Create diverse question types
        for i, sentence in enumerate(sentences[:num_questions * 2]):
            if len(questions) >= num_questions:
                break
            
            words = sentence.split()
            if len(words) < 6:
                continue
            
            # Get relevant keyword from sentence
            sentence_keywords = [k for k in keywords if k in sentence.lower()]
            if not sentence_keywords:
                sentence_keywords = [words[min(3, len(words)-1)]]
            
            main_keyword = sentence_keywords[0]
            
            # Create distractors from other sentences
            distractors = []
            for other_sentence in sentences:
                if other_sentence != sentence and len(distractors) < 3:
                    if len(other_sentence.split()) >= 5:
                        distractors.append(other_sentence)
            
            # Generate plausible but incorrect distractors
            while len(distractors) < 3:
                distractor_templates = [
                    "This information is not mentioned in the text",
                    f"The text focuses on a different aspect of {main_keyword}",
                    "This is an incorrect interpretation of the content"
                ]
                if distractor_templates:
                    distractors.append(distractor_templates[len(distractors) % len(distractor_templates)])
            
            # Create question
            question_templates = [
                f"What does the text state about {main_keyword}?",
                f"According to the passage, which statement about {main_keyword} is correct?",
                f"What information is provided regarding {main_keyword}?",
                "Which of the following statements is accurate based on the text?"
            ]
            
            question_text = question_templates[i % len(question_templates)]
            choices = [sentence] + distractors[:3]
            
            # Shuffle choices
            combined = list(zip(choices, range(len(choices))))
            random.shuffle(combined)
            shuffled_choices, indices = zip(*combined)
            correct_answer = shuffled_choices[indices.index(0)]
            
            questions.append({
                'question': question_text,
                'choices': list(shuffled_choices),
                'answer': correct_answer
            })
        
        return questions[:num_questions] if questions else [{
            'question': 'What is the main topic of this text?',
            'choices': [
                'The primary subject discussed',
                'Something not mentioned',
                'An unrelated topic',
                'Multiple unrelated subjects'
            ],
            'answer': 'The primary subject discussed'
        }]
        
    except Exception as e:
        return [{'question': 'Error generating questions', 'choices': ['Option 1', 'Option 2', 'Option 3', 'Option 4'], 'answer': 'Option 1'}]
