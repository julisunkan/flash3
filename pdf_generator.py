from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from io import BytesIO
from datetime import datetime
import html

def escape_for_pdf(text):
    """Escape HTML and special characters for safe PDF rendering"""
    if text is None:
        return ""
    # Convert to string and escape HTML entities
    text = str(text)
    text = html.escape(text)
    return text

def generate_flashcards_pdf(cards, deck_name="Flashcards"):
    """
    Generate a PDF from flashcards data
    
    Args:
        cards: List of dicts with 'question', 'answer', and optional 'choices'
        deck_name: Name of the flashcard deck
    
    Returns:
        BytesIO object containing the PDF
    
    Raises:
        ValueError: If cards data is invalid
        Exception: If PDF generation fails
    """
    if not cards or not isinstance(cards, list):
        raise ValueError("Cards must be a non-empty list")
    
    if len(cards) > 100:
        raise ValueError("Cannot export more than 100 cards at once")
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                           rightMargin=72, leftMargin=72,
                           topMargin=72, bottomMargin=18)
    
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#6366f1'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#4f46e5'),
        spaceAfter=12,
        spaceBefore=20,
        fontName='Helvetica-Bold'
    )
    
    question_style = ParagraphStyle(
        'Question',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.HexColor('#1f2937'),
        spaceAfter=8,
        leftIndent=20,
        fontName='Helvetica-Bold'
    )
    
    answer_style = ParagraphStyle(
        'Answer',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.HexColor('#374151'),
        spaceAfter=12,
        leftIndent=20,
        fontName='Helvetica'
    )
    
    choice_style = ParagraphStyle(
        'Choice',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#4b5563'),
        spaceAfter=4,
        leftIndent=30,
        fontName='Helvetica'
    )
    
    story = []
    
    # Title - escape deck name
    safe_deck_name = escape_for_pdf(deck_name)
    story.append(Paragraph(f"📚 {safe_deck_name}", title_style))
    story.append(Paragraph(f"Generated on {datetime.now().strftime('%B %d, %Y')}", styles['Normal']))
    story.append(Spacer(1, 0.3*inch))
    
    # Add cards
    valid_card_count = 0
    for i, card in enumerate(cards, 1):
        if not isinstance(card, dict):
            raise ValueError(f"Card {i} is not a valid dictionary")
        
        if 'question' not in card or 'answer' not in card:
            raise ValueError(f"Card {i} is missing required fields")
        
        valid_card_count += 1
        
        # Card number
        card_header = f"Card #{valid_card_count}"
        story.append(Paragraph(card_header, heading_style))
        
        # Question - escape user content
        question = escape_for_pdf(card.get('question', 'No question'))
        story.append(Paragraph("<b>Question:</b>", question_style))
        story.append(Paragraph(question, answer_style))
        story.append(Spacer(1, 0.1*inch))
        
        # Check if it's a multiple choice question
        if 'choices' in card and card['choices'] and isinstance(card['choices'], list):
            # Multiple choice - compare original values before escaping
            original_answer = str(card.get('answer', '')).strip()
            story.append(Paragraph("<b>Answer Choices:</b>", question_style))
            
            for j, choice in enumerate(card['choices'][:10]):  # Limit to 10 choices max
                if not choice:
                    continue
                
                # Convert choice to string for comparison
                choice_str = str(choice).strip()
                choice_letter = chr(65 + j)  # A, B, C, D
                safe_choice = escape_for_pdf(choice_str)
                # Compare original values
                is_correct = choice_str == original_answer
                
                if is_correct:
                    choice_text = f"<b>{choice_letter}. {safe_choice} ✓ (Correct)</b>"
                    choice_para = Paragraph(choice_text, choice_style)
                else:
                    choice_text = f"{choice_letter}. {safe_choice}"
                    choice_para = Paragraph(choice_text, choice_style)
                
                story.append(choice_para)
            
            story.append(Spacer(1, 0.15*inch))
        else:
            # Regular Q&A - escape user content
            answer = escape_for_pdf(card.get('answer', 'No answer'))
            story.append(Paragraph("<b>Answer:</b>", question_style))
            story.append(Paragraph(answer, answer_style))
            story.append(Spacer(1, 0.15*inch))
        
        # Add separator line except for last card
        if i < len(cards):
            story.append(Spacer(1, 0.1*inch))
            # Horizontal line
            line_table = Table([['']], colWidths=[6.5*inch])
            line_table.setStyle(TableStyle([
                ('LINEBELOW', (0, 0), (-1, -1), 1, colors.HexColor('#e5e7eb'))
            ]))
            story.append(line_table)
            story.append(Spacer(1, 0.15*inch))
    
    # Footer
    story.append(Spacer(1, 0.3*inch))
    footer_text = f"Total Cards: {len(cards)} | AI Flashcard Generator"
    story.append(Paragraph(footer_text, styles['Normal']))
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer
