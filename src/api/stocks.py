# src/api/stocks.py
from datetime import datetime

import yfinance as yf
from firebase_admin import firestore
from flask import Blueprint, jsonify, request

from utils.validators import token_required, validate_stock_data

bp = Blueprint('stocks', __name__)
db = firestore.client()

# List of allowed technology stocks
ALLOWED_TECH_STOCKS = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'META', 'NVDA', 'TSLA', 'AMD', 'INTC', 'CRM']

def validate_stock_symbol(symbol):
    """Validate stock symbol"""
    return symbol in ALLOWED_TECH_STOCKS

@bp.route('/available', methods=['GET'])
@token_required
def get_available_stocks(current_user):
    """Get list of available technology stocks"""
    try:
        stocks_data = {}
        for symbol in ALLOWED_TECH_STOCKS:
            stock = yf.Ticker(symbol)
            info = stock.info
            stocks_data[symbol] = {
                'name': info.get('longName', symbol),
                'sector': info.get('sector', 'Technology'),
                'currency': info.get('currency', 'USD')
            }
            
        return jsonify({
            'stocks': stocks_data,
            'count': len(ALLOWED_TECH_STOCKS),
            'message': 'List of available technology stocks'
        })
    except Exception as e:
        return jsonify({'error': f'Error fetching stocks: {str(e)}'}), 500

@bp.route('/price/<symbol>', methods=['GET'])
@token_required
def get_stock_price(current_user, symbol):
    """Get real-time price for a specific stock"""
    if not validate_stock_symbol(symbol):
        return jsonify({'error': 'Invalid stock symbol'}), 400
    
    try:
        stock = yf.Ticker(symbol)
        real_time = stock.history(period='1d')
        
        if real_time.empty:
            return jsonify({'error': 'No data available for this stock'}), 404
        
        latest_price = real_time['Close'].iloc[-1]
        info = stock.info
        prev_close = info.get('previousClose', latest_price)
        price_change = ((latest_price - prev_close) / prev_close) * 100
        
        return jsonify({
            'symbol': symbol,
            'current_price': round(latest_price, 2),
            'change_percent': round(price_change, 2),
            'company_name': info.get('longName', symbol),
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': f'Error fetching stock data: {str(e)}'}), 500

@bp.route('/portfolio/add', methods=['POST'])
@token_required
def add_to_portfolio(current_user):
    """Add stock to user's portfolio"""
    try:
        data = request.get_json()
        symbol = data.get('symbol')
        quantity = data.get('quantity', 1)
        
        if not symbol:
            return jsonify({'error': 'Missing stock symbol'}), 400
            
        if not validate_stock_symbol(symbol):
            return jsonify({'error': 'Invalid stock symbol'}), 400
        
        # Validate quantity
        try:
            quantity = int(quantity)
            if quantity <= 0:
                return jsonify({'error': 'Quantity must be positive'}), 400
        except ValueError:
            return jsonify({'error': 'Invalid quantity'}), 400
            
        portfolio_ref = db.collection('portfolios').document(current_user)
        
        portfolio = portfolio_ref.get()
        if portfolio.exists:
            current_stocks = portfolio.to_dict().get('stocks', {})
            current_stocks[symbol] = current_stocks.get(symbol, 0) + quantity
            portfolio_ref.update({
                'stocks': current_stocks,
                'updated_at': firestore.SERVER_TIMESTAMP
            })
        else:
            portfolio_ref.set({
                'stocks': {symbol: quantity},
                'user_id': current_user,
                'created_at': firestore.SERVER_TIMESTAMP,
                'updated_at': firestore.SERVER_TIMESTAMP
            })
            
        return jsonify({
            'message': 'Stock added to portfolio successfully',
            'symbol': symbol,
            'quantity': quantity
        }), 201
    except Exception as e:
        return jsonify({'error': f'Error adding stock: {str(e)}'}), 500

@bp.route('/portfolio', methods=['GET'])
@token_required
def get_portfolio(current_user):
    """Get user's portfolio with current prices"""
    try:
        portfolio_ref = db.collection('portfolios').document(current_user)
        portfolio = portfolio_ref.get()
        
        if not portfolio.exists:
            return jsonify({
                'message': 'No portfolio found',
                'stocks': []
            }), 200
            
        portfolio_data = portfolio.to_dict()
        stocks = portfolio_data.get('stocks', {})
        
        detailed_portfolio = []
        total_value = 0
        
        for symbol, quantity in stocks.items():
            stock = yf.Ticker(symbol)
            current_price = stock.history(period='1d')['Close'].iloc[-1]
            stock_value = current_price * quantity
            total_value += stock_value
            
            detailed_portfolio.append({
                'symbol': symbol,
                'quantity': quantity,
                'current_price': round(current_price, 2),
                'total_value': round(stock_value, 2),
                'company_name': stock.info.get('longName', symbol)
            })
        
        return jsonify({
            'portfolio': detailed_portfolio,
            'total_value': round(total_value, 2),
            'stock_count': len(detailed_portfolio),
            'last_updated': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': f'Error fetching portfolio: {str(e)}'}), 500
