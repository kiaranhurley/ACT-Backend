# src/services/stocks_service.py
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Union

from firebase_admin import firestore
from flask import current_app, jsonify


class StocksService:
    """Service for handling stock-related operations"""
    
    def __init__(self, firebase_service=None):
        """Initialize stocks service"""
        self.firebase_service = firebase_service
        self.db = firebase_service.db if firebase_service else None
        
    def get_all_stocks(self) -> Tuple[Dict, int]:
        """
        Get all stocks from the database
        Returns: Tuple of (response_dict, status_code)
        """
        try:
            if not self.db:
                current_app.logger.error("Database connection not initialized")
                return {
                    'message': 'Database connection error',
                    'status': 'error'
                }, 500
            
            stocks_ref = self.db.collection('stocks')
            stocks = []
            
            for doc in stocks_ref.stream():
                stock_data = doc.to_dict()
                stock_data['id'] = doc.id
                stocks.append(stock_data)
            
            return {
                'stocks': stocks,
                'count': len(stocks),
                'status': 'success'
            }, 200
            
        except Exception as e:
            current_app.logger.error(f"Error fetching stocks: {str(e)}")
            return {
                'message': f"Error fetching stocks: {str(e)}",
                'status': 'error'
            }, 500
    
    def get_stock_by_symbol(self, symbol: str) -> Tuple[Dict, int]:
        """
        Get stock by symbol
        Args:
            symbol: Stock symbol
        Returns: Tuple of (response_dict, status_code)
        """
        try:
            if not self.db:
                current_app.logger.error("Database connection not initialized")
                return {
                    'message': 'Database connection error',
                    'status': 'error'
                }, 500
            
            stock_ref = self.db.collection('stocks').document(symbol)
            stock = stock_ref.get()
            
            if not stock.exists:
                return {
                    'message': f'Stock with symbol {symbol} not found',
                    'status': 'error'
                }, 404
            
            stock_data = stock.to_dict()
            stock_data['id'] = stock.id
            
            return {
                'stock': stock_data,
                'status': 'success'
            }, 200
            
        except Exception as e:
            current_app.logger.error(f"Error fetching stock {symbol}: {str(e)}")
            return {
                'message': f"Error fetching stock: {str(e)}",
                'status': 'error'
            }, 500
    
    def add_stock(self, data: Dict) -> Tuple[Dict, int]:
        """
        Add new stock to database
        Args:
            data: Stock data dictionary
        Returns: Tuple of (response_dict, status_code)
        """
        try:
            if not self.db:
                current_app.logger.error("Database connection not initialized")
                return {
                    'message': 'Database connection error',
                    'status': 'error'
                }, 500
            
            required_fields = ['symbol', 'name', 'price']
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                return {
                    'message': f'Missing required fields: {", ".join(missing_fields)}',
                    'status': 'error'
                }, 400
            
            # Check if stock already exists
            stock_ref = self.db.collection('stocks').document(data['symbol'])
            if stock_ref.get().exists:
                return {
                    'message': f'Stock with symbol {data["symbol"]} already exists',
                    'status': 'error'
                }, 409
            
            # Add timestamp
            data['created_at'] = datetime.utcnow()
            data['updated_at'] = datetime.utcnow()
            
            # Add stock to database
            stock_ref.set(data)
            
            return {
                'message': f'Stock {data["symbol"]} added successfully',
                'stock': data,
                'status': 'success'
            }, 201
            
        except Exception as e:
            current_app.logger.error(f"Error adding stock: {str(e)}")
            return {
                'message': f"Error adding stock: {str(e)}",
                'status': 'error'
            }, 500
    
    def update_stock(self, symbol: str, data: Dict) -> Tuple[Dict, int]:
        """
        Update existing stock
        Args:
            symbol: Stock symbol
            data: Updated stock data
        Returns: Tuple of (response_dict, status_code)
        """
        try:
            if not self.db:
                current_app.logger.error("Database connection not initialized")
                return {
                    'message': 'Database connection error',
                    'status': 'error'
                }, 500
            
            stock_ref = self.db.collection('stocks').document(symbol)
            if not stock_ref.get().exists:
                return {
                    'message': f'Stock with symbol {symbol} not found',
                    'status': 'error'
                }, 404
            
            # Update timestamp
            data['updated_at'] = datetime.utcnow()
            
            # Update stock
            stock_ref.update(data)
            
            # Get updated stock data
            updated_stock = stock_ref.get().to_dict()
            updated_stock['id'] = symbol
            
            return {
                'message': f'Stock {symbol} updated successfully',
                'stock': updated_stock,
                'status': 'success'
            }, 200
            
        except Exception as e:
            current_app.logger.error(f"Error updating stock {symbol}: {str(e)}")
            return {
                'message': f"Error updating stock: {str(e)}",
                'status': 'error'
            }, 500
    
    def delete_stock(self, symbol: str) -> Tuple[Dict, int]:
        """
        Delete stock from database
        Args:
            symbol: Stock symbol
        Returns: Tuple of (response_dict, status_code)
        """
        try:
            if not self.db:
                current_app.logger.error("Database connection not initialized")
                return {
                    'message': 'Database connection error',
                    'status': 'error'
                }, 500
            
            stock_ref = self.db.collection('stocks').document(symbol)
            if not stock_ref.get().exists:
                return {
                    'message': f'Stock with symbol {symbol} not found',
                    'status': 'error'
                }, 404
            
            # Delete stock
            stock_ref.delete()
            
            return {
                'message': f'Stock {symbol} deleted successfully',
                'status': 'success'
            }, 200
            
        except Exception as e:
            current_app.logger.error(f"Error deleting stock {symbol}: {str(e)}")
            return {
                'message': f"Error deleting stock: {str(e)}",
                'status': 'error'
            }, 500
    
    def get_stock_price_history(self, symbol: str) -> Tuple[Dict, int]:
        """
        Get price history for a stock
        Args:
            symbol: Stock symbol
        Returns: Tuple of (response_dict, status_code)
        """
        try:
            if not self.db:
                current_app.logger.error("Database connection not initialized")
                return {
                    'message': 'Database connection error',
                    'status': 'error'
                }, 500
            
            # Get stock document
            stock_ref = self.db.collection('stocks').document(symbol)
            stock = stock_ref.get()
            
            if not stock.exists:
                return {
                    'message': f'Stock with symbol {symbol} not found',
                    'status': 'error'
                }, 404
            
            # Get price history subcollection
            history_ref = stock_ref.collection('price_history')
            history = []
            
            for doc in history_ref.order_by('timestamp', direction=firestore.Query.DESCENDING).stream():
                history_data = doc.to_dict()
                history_data['id'] = doc.id
                history.append(history_data)
            
            return {
                'symbol': symbol,
                'price_history': history,
                'status': 'success'
            }, 200
            
        except Exception as e:
            current_app.logger.error(f"Error fetching price history for stock {symbol}: {str(e)}")
            return {
                'message': f"Error fetching price history: {str(e)}",
                'status': 'error'
            }, 500