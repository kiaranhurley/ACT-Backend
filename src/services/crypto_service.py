# src/services/crypto_service.py

from datetime import datetime
from typing import Dict, List, Optional

import requests
from firebase_admin import firestore


class CryptoService:
    def __init__(self):
        self.db = firestore.client()
        self.supported_cryptos = {
            'BTC': 'Bitcoin',
            'ETH': 'Ethereum',
            'USDT': 'Tether'
        }
        
    def get_price(self, symbol: str) -> float:
        """Get current price for a cryptocurrency"""
        symbol_mapping = {'BTC': 'bitcoin', 'ETH': 'ethereum', 'USDT': 'tether'}
        coin_id = symbol_mapping.get(symbol)
        
        if not coin_id:
            raise ValueError(f"Unsupported cryptocurrency: {symbol}")
            
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd"
        response = requests.get(url)
        data = response.json()
        return data[coin_id]['usd']
        
    def get_portfolio(self, user_id: str) -> Dict:
        """Get user's cryptocurrency portfolio"""
        portfolio_ref = self.db.collection('crypto_portfolios').document(user_id)
        portfolio = portfolio_ref.get()
        
        if not portfolio.exists:
            return {
                'assets': [],
                'total_value': 0,
                'message': 'No cryptocurrency portfolio found'
            }
            
        portfolio_data = portfolio.to_dict()
        assets = portfolio_data.get('assets', {})
        current_portfolio = []
        total_value = 0
        
        for symbol, data in assets.items():
            current_price = self.get_price(symbol)
            quantity = data['quantity']
            avg_price = data['avg_price']
            current_value = quantity * current_price
            total_value += current_value
            
            current_portfolio.append({
                'symbol': symbol,
                'name': self.supported_cryptos[symbol],
                'quantity': quantity,
                'avg_price': avg_price,
                'current_price': current_price,
                'current_value': current_value,
                'profit_loss': current_value - (quantity * avg_price),
                'profit_loss_percentage': ((current_price - avg_price) / avg_price) * 100
            })
            
        return {
            'portfolio': current_portfolio,
            'total_value': total_value,
            'asset_count': len(current_portfolio),
            'last_updated': datetime.now().isoformat()
        }
        
    def add_to_portfolio(self, user_id: str, symbol: str, quantity: float) -> Dict:
        """Add cryptocurrency to user's portfolio"""
        if symbol not in self.supported_cryptos:
            raise ValueError('Unsupported cryptocurrency')
            
        if quantity <= 0:
            raise ValueError('Quantity must be positive')
            
        current_price = self.get_price(symbol)
        portfolio_ref = self.db.collection('crypto_portfolios').document(user_id)
        portfolio = portfolio_ref.get()
        
        if portfolio.exists:
            portfolio_data = portfolio.to_dict()
            assets = portfolio_data.get('assets', {})
            
            if symbol in assets:
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
            portfolio_ref.set({
                'user_id': user_id,
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
            
        return {
            'symbol': symbol,
            'quantity': quantity,
            'price_usd': current_price,
            'message': 'Cryptocurrency added to portfolio successfully'
        }