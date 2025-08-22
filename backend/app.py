# app.py
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
import logging
from datetime import datetime

# Import your actual functions (uncomment these lines and comment out the mock functions below)
from fetch_and_score import fetch_and_compute_credit_scores, get_score_breakdown_data
from unstructured import top_headlines

app = Flask(__name__)
CORS(app)  # Enable CORS for React frontend

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return jsonify({
        'error': 'Not Found',
        'message': 'The requested resource was not found',
        'status': 404
    }), 404

@app.errorhandler(400)
def bad_request_error(error):
    return jsonify({
        'error': 'Bad Request',
        'message': 'Invalid request parameters',
        'status': 400
    }), 400

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'error': 'Internal Server Error',
        'message': 'An unexpected error occurred',
        'status': 500
    }), 500

# Routes
@app.route('/')
def dashboard():
    """Serve the main dashboard page"""
    return render_template('credit_score_charts.html')

@app.route('/api/chart-data')
def chart_data():
    """API endpoint to get pie chart data"""
    try:
        data = get_score_breakdown_data()
        return jsonify(data)
    except Exception as e:
        logger.error(f"Error getting chart data: {str(e)}")
        return jsonify({'error': 'Failed to load chart data'}), 500

@app.route('/api/company-analysis/<ticker>')
def company_analysis(ticker):
    """Get complete analysis for a specific company"""
    try:
        ticker = ticker.upper()
        logger.info(f"Analyzing ticker: {ticker}")
        
        # Get credit scores for the ticker
        credit_results = fetch_and_compute_credit_scores([ticker])
        
        if ticker not in credit_results:
            return jsonify({
                'error': f'No financial data available for {ticker}. Please check the ticker symbol.'
            }), 404
        
        # Get breakdown data
        breakdown_data = get_score_breakdown_data()
        
        response_data = {
            'ticker': ticker,
            'credit_scores': credit_results[ticker],
            'breakdown': breakdown_data,
            'success': True,
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"Successfully analyzed {ticker}")
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error analyzing {ticker}: {str(e)}")
        return jsonify({
            'error': f'Failed to analyze {ticker}: {str(e)}'
        }), 500

@app.route('/api/batch-analysis', methods=['POST'])
def batch_analysis():
    """Analyze multiple companies at once"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
            
        tickers = data.get('tickers', [])
        
        if not tickers:
            return jsonify({'error': 'No tickers provided'}), 400
        
        # Limit batch size for performance
        if len(tickers) > 10:
            return jsonify({'error': 'Maximum 10 tickers per batch'}), 400
        
        # Convert to uppercase and validate
        tickers = [ticker.upper().strip() for ticker in tickers if ticker.strip()]
        
        if not tickers:
            return jsonify({'error': 'No valid tickers provided'}), 400
        
        # Get credit scores
        credit_results = fetch_and_compute_credit_scores(tickers)
        
        # Get breakdown data
        breakdown_data = get_score_breakdown_data()
        
        return jsonify({
            'results': credit_results,
            'breakdown': breakdown_data,
            'processed_count': len(credit_results),
            'requested_count': len(tickers),
            'success': True,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in batch analysis: {str(e)}")
        return jsonify({'error': 'Batch analysis failed'}), 500

@app.route('/api/news/<ticker>')
def get_news(ticker):
    """Get top news headlines with sentiment analysis for a ticker"""
    try:
        ticker = ticker.upper()
        n = request.args.get('count', default=3, type=int)
        
        # Limit to reasonable number
        n = min(max(n, 1), 10)
        
        logger.info(f"Fetching {n} headlines for {ticker}")
        
        headlines = top_headlines(ticker, n=n)
        
        return jsonify({
            'ticker': ticker,
            'headlines': headlines,
            'count': len(headlines),
            'success': True,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error fetching news for {ticker}: {str(e)}")
        return jsonify({
            'error': f'Failed to fetch news for {ticker}: {str(e)}'
        }), 500

@app.route('/api/company-analysis-full/<ticker>')
def company_analysis_full(ticker):
    """Get complete analysis including credit scores and news"""
    try:
        ticker = ticker.upper()
        logger.info(f"Full analysis for ticker: {ticker}")
        
        # Get credit scores
        credit_results = fetch_and_compute_credit_scores([ticker])
        
        if ticker not in credit_results:
            return jsonify({
                'error': f'No financial data available for {ticker}'
            }), 404
        
        # Get breakdown data
        breakdown_data = get_score_breakdown_data()
        
        # Get news headlines
        headlines = top_headlines(ticker, n=5)
        
        response_data = {
            'ticker': ticker,
            'credit_scores': credit_results[ticker],
            'breakdown': breakdown_data,
            'news': {
                'headlines': headlines,
                'count': len(headlines)
            },
            'success': True,
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error in full analysis for {ticker}: {str(e)}")
        return jsonify({
            'error': f'Failed to analyze {ticker}: {str(e)}'
        }), 500

# Health check endpoint
@app.route('/api/health')
def health_check():
    """Simple health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
