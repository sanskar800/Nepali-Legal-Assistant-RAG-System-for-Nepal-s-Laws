"""
Example script for querying the Nepali Law Bot
"""
import sys
import os

# Add parent directory to path so we can import from src
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.chatbot import NepaliLawBot
from src.utils import print_colored


def main():
    """Run example queries"""
    
    # Initialize bot
    print_colored("\n🏛️  Initializing Nepali Law Bot...", "cyan")
    bot = NepaliLawBot()
    print_colored("✓ Bot initialized successfully!\n", "green")
    
    # Example queries
    example_queries = [
        "How can I get a divorce in Nepal?",
        "Can a foreigner own land in Nepalj?",
        "नेपालमा सम्पत्ति कसरी बाँड्ने?",
    ]
    
    print_colored("=" * 80, "cyan")
    print_colored("EXAMPLE QUERIES", "cyan")
    print_colored("=" * 80, "cyan")
    
    for i, query in enumerate(example_queries, 1):
        print_colored(f"\n\n{'='*80}", "yellow")
        print_colored(f"EXAMPLE {i}: {query}", "yellow")
        print_colored(f"{'='*80}\n", "yellow")
        
        # Process query
        response = bot.query(query)
        
        # Display response
        print(response.format_for_display())
        
        # Wait for user
        if i < len(example_queries):
            input("\n\nPress Enter to continue to next example...")
    
    print_colored("\n\n" + "=" * 80, "cyan")
    print_colored("INTERACTIVE MODE", "cyan")
    print_colored("=" * 80, "cyan")
    print_colored("\nYou can now ask your own questions!", "green")
    
    # Start interactive chat
    bot.chat()


if __name__ == "__main__":
    main()
