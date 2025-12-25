"""
Disable verbose logging from external libraries
"""
import logging
import warnings

# Suppress warnings
warnings.filterwarnings('ignore')

# Disable verbose logging from external libraries
logging.getLogger('sentence_transformers').setLevel(logging.ERROR)
logging.getLogger('httpx').setLevel(logging.ERROR)
logging.getLogger('urllib3').setLevel(logging.ERROR)
logging.getLogger('transformers').setLevel(logging.ERROR)

# Set our logger to WARNING level
logging.getLogger('nepali_law_bot').setLevel(logging.WARNING)
