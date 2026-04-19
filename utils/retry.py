import time
from functools import wraps
from utils.logger import get_logger

logger = get_logger("retry")

def retry(max_retries=2, delay=0.5):
    """失败自动重试装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for i in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if i == max_retries:
                        logger.error(f"最终重试失败：{e}")
                        raise
                    logger.warning(f"第{i+1}次重试：{e}")
                    time.sleep(delay)
            return None
        return wrapper
    return decorator