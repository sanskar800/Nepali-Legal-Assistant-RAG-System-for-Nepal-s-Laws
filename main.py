"""
Standalone entry point for running the chatbot directly
"""
import sys
import os

# Add parent directory to path so we can import from src
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.chatbot import NepaliLawBot

if __name__ == "__main__":
    bot = NepaliLawBot()
    bot.chat()
