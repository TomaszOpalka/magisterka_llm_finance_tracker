import asyncio
import yfinance as yf
import logging

logger = logging.getLogger("finance_track")

def _fetch_price_sync(ticker: str) -> float | None:
    """
    Synchronous helper function to fetch stock data.
    Separated from the async layer to keep the thread execution clean.
    """
    try:
        stock = yf.Ticker(ticker)
        # Using fast_info to get the real-time or last closing price quickly
        price = stock.fast_info.last_price
        
        if price is None:
            logger.warning(f"Received None price for ticker: {ticker}")
            return None
            
        return float(price)
    except Exception as e:
        logger.error(f"Error fetching data from yfinance for {ticker}: {e}")
        return None

async def get_stock_price(ticker: str) -> float | None:
    """
    Asynchronously fetches the latest stock price for a given ticker.
    Crucially, it uses asyncio.to_thread to prevent the synchronous
    yfinance library from blocking the FastAPI event loop.
    """
    return await asyncio.to_thread(_fetch_price_sync, ticker)