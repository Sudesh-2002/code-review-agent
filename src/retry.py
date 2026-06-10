import time
from src.logger import get_logger

logger = get_logger("retry")

def call_with_retry(func, *args, retries=4, base_delay=5, **kwargs):
    """
    Call a function with exponential backoff retry.
    Handles Groq rate limits and network errors automatically.
    """
    for attempt in range(1, retries + 1):
        try:
            return func(*args, **kwargs)

        except Exception as e:
            error_msg = str(e).lower()

            # Rate limit hit
            if "rate limit" in error_msg or "429" in error_msg:
                wait = base_delay * (2 ** (attempt - 1))  # 5, 10, 20, 40 sec
                logger.warning(
                    f"Rate limit hit (attempt {attempt}/{retries}). "
                    f"Waiting {wait}s before retry..."
                )
                time.sleep(wait)

            # Network / timeout error
            elif "timeout" in error_msg or "connection" in error_msg:
                wait = base_delay * attempt
                logger.warning(
                    f"Network error (attempt {attempt}/{retries}). "
                    f"Waiting {wait}s before retry..."
                )
                time.sleep(wait)

            # Groq content-quality error — retrying won't help, raise immediately
            elif "looping content" in error_msg or "output is flagged" in error_msg:
                logger.error(
                    f"LLM output flagged for looping content — skipping retries. "
                    f"Function: {func.__name__}"
                )
                raise

            # Unknown error — still retry
            else:
                logger.error(
                    f"Unexpected error (attempt {attempt}/{retries}): {e}"
                )
                if attempt < retries:
                    time.sleep(base_delay)
                else:
                    raise  # All retries exhausted — raise the error

    raise RuntimeError(f"All {retries} attempts failed for {func.__name__}")