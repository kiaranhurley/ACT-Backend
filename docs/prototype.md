# ACT Backend Prototype

## Available Endpoints

### Authentication
- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/users/<user_id>`

### Stocks
- `GET /api/stocks/available`
- `GET /api/stocks/price/<symbol>`
- `GET /api/stocks/portfolio`
- `POST /api/stocks/portfolio/add`
- `POST /api/stocks/portfolio/remove`

## Testing Instructions

1. Start the server:
```bash
python -m src.app
```

2. Test authentication:
```bash
# Register new user
curl -X POST http://127.0.0.1:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"test@example.com\", \"password\":\"testpass123\"}"

# Login
curl -X POST http://127.0.0.1:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"test@example.com\", \"password\":\"testpass123\"}"
```

3. Test stock operations:
```bash
# Get available stocks
curl http://127.0.0.1:5000/api/stocks/available

# Get stock price
curl http://127.0.0.1:5000/api/stocks/price/AAPL

# Add stock to portfolio
curl -X POST http://127.0.0.1:5000/api/stocks/portfolio/add \
  -H "Content-Type: application/json" \
  -d "{\"user_id\":\"test_user\", \"symbol\":\"AAPL\", \"quantity\":5}"
```

## Current Features
- Firebase Authentication
- Real-time stock data fetching
- Basic portfolio management
- Error handling
- CORS support

## Next Steps
1. Implement JWT authentication
2. Add transaction history
3. Integrate with AI engine
4. Add price alerts
5. Implement crypto assets support