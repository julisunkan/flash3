# AI Flashcard Generator

## Overview
A production-ready Progressive Web App (PWA) that generates interactive flashcards from text or PDF files using AI. Built with Flask (Python), SQLite, and vanilla JavaScript.

## Features
- **AI-Powered Generation**: Uses OpenAI API to create summaries, Q&A pairs, and multiple-choice questions
- **PDF Support**: Extract text from PDFs using PyPDF2 and pdfplumber
- **OCR Capabilities**: Scan text from images in PDFs using Tesseract OCR
- **Spaced Repetition**: SM-2 algorithm for optimized learning intervals
- **Study Modes**: Interactive card flipping, quiz mode with instant feedback
- **Voice Features**: Text-to-Speech (TTS) and voice-based answering
- **Analytics**: Track progress, retention rates, and performance metrics
- **Gamification**: Badge and achievement system
- **Export**: JSON, CSV, and Anki-compatible formats
- **PWA**: Offline functionality with service worker caching
- **Responsive**: Optimized for mobile and desktop

## Project Architecture
```
/
├── app.py                  # Flask application entry point
├── models.py               # Database models and schema
├── ai_service.py           # OpenAI integration for content generation
├── srs_algorithm.py        # SM-2 spaced repetition implementation
├── utils.py                # Helper functions (PDF/OCR processing)
├── requirements.txt        # Python dependencies
├── flashcards.db          # SQLite database (auto-created)
├── static/
│   ├── css/
│   │   └── style.css      # Main stylesheet
│   ├── js/
│   │   ├── app.js         # Main application logic
│   │   ├── study.js       # Study mode functionality
│   │   └── quiz.js        # Quiz mode functionality
│   ├── icons/             # PWA icons
│   └── manifest.json      # PWA manifest
├── templates/
│   ├── index.html         # Home page / upload interface
│   ├── deck.html          # Flashcard deck view
│   ├── study.html         # Study mode
│   ├── quiz.html          # Quiz mode
│   └── analytics.html     # Analytics dashboard
└── sw.js                  # Service worker for offline support
```

## Technology Stack
- **Backend**: Flask (Python 3.11)
- **Database**: SQLite3
- **AI**: OpenAI API
- **PDF Processing**: PyPDF2, pdfplumber
- **OCR**: Tesseract, pytesseract
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **PWA**: Service Worker, Cache API, IndexedDB

## Database Schema
- **decks**: Flashcard sets (id, name, description, created_at)
- **cards**: Individual flashcards (id, deck_id, question, answer, difficulty, created_at)
- **study_sessions**: Learning progress (id, card_id, easiness_factor, interval, repetitions, next_review)
- **quiz_results**: Quiz performance tracking
- **badges**: Achievement system

## Recent Changes
- [2025-11-22] Initial project setup
- [2025-11-22] Added complete feature set with AI, OCR, SRS, PWA capabilities

## User Preferences
None yet.

## Configuration
- Port: 5000 (Flask development server bound to 0.0.0.0)
- OpenAI API key required (stored as secret)
- Tesseract OCR system dependency required
