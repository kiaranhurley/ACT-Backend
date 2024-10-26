# src/api/crypto.py

from datetime import datetime

import requests
from firebase_admin import firestore
from flask import Blueprint, jsonify, request

from utils.validators import token_required

bp = Blueprint('crypto', __name__)
db = firestore.client()

# Supported cryptocurrencies - limited to 3 as per requirements
SUPPORTED_CRYPTOS = {
    'BTC': 'Bitcoin',
    'ETH': 'Ethereum',
    'USDT': 'Tether'
}

def get_crypto_price(symbol: str) -> float:
    """
    Get current price for a cryptocurrency using CoinGecko API
    """
    try:
        # Using CoinGecko's free API
        symbol_mapping = {'BTC': 'bitcoin', 'ETH': 'ethereum', 'USDT': 'tether'}
        coin_id = symbol_mapping.get(symbol)
        if not coin_id:
            raise ValueError(f"Unsupported cryptocurrency: {symbol}")
            
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd"
        response = requests.get(url)
        data = response.json()
        return data[coin_id]['usd']
    except Exception as e:
        raise Exception(f"Error fetching crypto price: {str(e)}")

@bp.route('/crypto/available', methods=['GET'])
@token_required
def get_available_crypto(current_user):
    """Get list of supported cryptocurrencies"""
    return jsonify({
        'cryptos': [
            {'symbol': symbol, 'name': name}
            for symbol, name in SUPPORTED_CRYPTOS.items()
        ],
        'message': 'List of supported cryptocurrencies'
    })

@bp.route('/crypto/price/<symbol>', methods=['GET'])
@token_required
def get_crypto_current_price(current_user, symbol):
    """Get current price for a specific cryptocurrency"""
    if symbol not in SUPPORTED_CRYPTOS:
        return jsonify({'error': 'Unsupported cryptocurrency'}), 400
        
    try:
        price = get_crypto_price(symbol)
        return jsonify({
            'symbol': symbol,
            'name': SUPPORTED_CRYPTOS[symbol],
            'price_usd': price,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/crypto/portfolio/add', methods=['POST'])
@token_required
def add_to_crypto_portfolio(current_user):
    """Add cryptocurrency to user's portfolio"""
    try:
        data = request.get_json()
        symbol = data.get('symbol')
        quantity = float(data.get('quantity', 0))
        
        if not symbol or not quantity:
            return jsonify({'error': 'Missing symbol or quantity'}), 400
            
        if symbol not in SUPPORTED_CRYPTOS:
            return jsonify({'error': 'Unsupported cryptocurrency'}), 400
            
        if quantity <= 0:
            return jsonify({'error': 'Quantity must be positive'}), 400
            
        # Get current price for calculation
        current_price = get_crypto_price(symbol)
        
        portfolio_ref = db.collection('crypto_portfolios').document(current_user)
        portfolio = portfolio_ref.get()
        
        if portfolio.exists:
            portfolio_data = portfolio.to_dict()
            assets = portfolio_data.get('assets', {})
            
            if symbol in assets:
                # Update existing position
                old_quantity = assets[symbol]['quantity']
                old_value = assets[symbol]['avg_price'] * old_quantity
                new_value = current_price * quantity
                total_quantity = old_quantity + quantity
                avg_price = (old_value + new_value) / total_quantity
                
                assets[symbol] = {
                    'quantity': total_quantity,
                    'avg_price': avg_price,
                    'last_updated': datetime.now().isoformat()
                }
            else:
                # Add new position
                assets[symbol] = {
                    'quantity': quantity,
                    'avg_price': current_price,
                    'last_updated': datetime.now().isoformat()
                }
            
            portfolio_ref.update({
                'assets': assets,
                'updated_at': firestore.SERVER_TIMESTAMP
            })
        else:
            # Create new portfolio
            portfolio_ref.set({
                'user_id': current_user,
                'assets': {
                    symbol: {
                        'quantity': quantity,
                        'avg_price': current_price,
                        'last_updated': datetime.now().isoformat()
                    }
                },
                'created_at': firestore.SERVER_TIMESTAMP,
                'updated_at': firestore.SERVER_TIMESTAMP
            })
            
        return jsonify({
            'message': 'Cryptocurrency added to portfolio successfully',
            'symbol': symbol,
            'quantity': quantity,
            'price_usd': current_price
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/crypto/portfolio', methods=['GET'])
@token_required
def get_crypto_portfolio(current_user):
    """Get user's cryptocurrency portfolio with current values"""
    try:
        portfolio_ref = db.collection('crypto_portfolios').document(current_user)
        portfolio = portfolio_ref.get()
        
        if not portfolio.exists:
            return jsonify({
                'message': 'No cryptocurrency portfolio found',
                'assets': [],
                'total_value': 0
            })
            
        portfolio_data = portfolio.to_dict()
        assets = portfolio_data.get('assets', {})
        
        current_portfolio = []
        total_value = 0
        
        for symbol, data in assets.items():
            current_price = get_crypto_price(symbol)
            quantity = data['quantity']
            avg_price = data['avg_price']
            current_value = quantity * current_price
            total_value += current_value
            
            current_portfolio.append({
                'symbol': symbol,
                'name': SUPPORTED_CRYPTOS[symbol],
                'quantity': quantity,
                'avg_price': avg_price,
                'current_price': current_price,
                'current_value': current_value,
                'profit_loss': current_value - (quantity * avg_price),
                'profit_loss_percentage': ((current_price - avg_price) / avg_price) * 100
            })
        
        return jsonify({
            'portfolio': current_portfolio,
            'total_value': total_value,
            'asset_count': len(current_portfolio),
            'last_updated': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500