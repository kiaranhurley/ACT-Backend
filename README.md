# ACT Backend

## Overview
Backend service for the ACT (Agentic Corporate Trader) project, handling authentication, stock management, and AI integration.

## Features
- User authentication with Firebase
- Stock price data retrieval
- Portfolio management
- Real-time market data
- Integration with AI trading engine (planned)

## Tech Stack
- Flask
- Firebase Admin SDK
- yfinance for stock data
- JWT for authentication
- Python 3.8+

## Setup Instructions
1. Create virtual environment:
```bash
python -m venv venv
venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configurations
```

4. Run the application:
```bash
python -m src.app
```

## Project Structure
```
act-backend/
├── src/
│   ├── api/
│   ├── models/
│   ├── services/
│   └── utils/
├── tests/
├── docs/
└── requirements.txt
```

## Development Team
- Backend Developer: Kiaran Hurley
- Collaborating with:
  - Web App: Moises Munaldi
  - AI Development: Pawel Wlodarczyk
  - Mobile App: Thomas O'Brien

## Sprint 1 Deliverables
- [x] Basic Flask application
- [x] Firebase integration
- [x] Authentication endpoints
- [x] Stock data endpoints
- [x] Development environment setup
- [x] Initial documentation