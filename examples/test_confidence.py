"""
Test script for confidence scoring mechanism
"""
import sys
import os

# Add parent directory to path so we can import from src
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.chatbot import NepaliLawBot
from src.utils import print_colored, format_confidence


def test_confidence_scoring():
    """Test confidence scoring with various queries"""
    
    print_colored("\n" + "=" * 80, "cyan")
    print_colored("CONFIDENCE SCORING TEST", "cyan")
    print_colored("=" * 80 + "\n", "cyan")
    
    # Initialize bot
    print_colored("Initializing bot...", "yellow")
    bot = NepaliLawBot()
    print_colored("✓ Bot initialized\n", "green")
    
    # Test cases with expected confidence levels
    test_cases = [
        {
            "query": "What are the grounds for divorce in Nepal?",
            "expected": "high",
            "description": "Specific legal query - should have HIGH confidence"
        },
        {
            "query": "How to register a company in Nepal?",
            "expected": "medium-high",
            "description": "Legal query - should have MEDIUM-HIGH confidence"
        },
        {
            "query": "What is the weather in Kathmandu?",
            "expected": "low",
            "description": "Non-legal query - should have LOW confidence"
        },
        {
            "query": "Tell me about quantum physics",
            "expected": "low",
            "description": "Completely irrelevant - should have LOW confidence"
        }
    ]
    
    results = []
    
    for i, test in enumerate(test_cases, 1):
        print_colored(f"\n{'='*80}", "yellow")
        print_colored(f"TEST CASE {i}/{len(test_cases)}", "yellow")
        print_colored(f"{'='*80}", "yellow")
        
        print(f"\nQuery: {test['query']}")
        print(f"Expected: {test['expected'].upper()} confidence")
        print(f"Description: {test['description']}\n")
        
        # Process query
        print_colored("Processing...", "cyan")
        response = bot.query(test['query'])
        
        # Display confidence
        print(f"\nActual Confidence: {format_confidence(response.confidence_score)}")
        
        # Show warning if present
        if response.warning:
            print_colored(f"\n⚠️  Warning: {response.warning}", "red")
        
        # Show number of sources
        print(f"\nSources Retrieved: {len(response.sources)}")
        
        # Categorize result
        score = response.confidence_score
        if score >= 0.7:
            category = "HIGH"
            color = "green"
        elif score >= 0.5:
            category = "MEDIUM"
            color = "yellow"
        else:
            category = "LOW"
            color = "red"
        
        print_colored(f"\nCategory: {category}", color)
        
        # Store result
        results.append({
            "query": test['query'],
            "expected": test['expected'],
            "actual_score": score,
            "category": category,
            "sources": len(response.sources)
        })
        
        # Brief answer preview
        print(f"\nAnswer Preview: {response.answer[:200]}...")
        
        if i < len(test_cases):
            input("\n\nPress Enter for next test case...")
    
    # Summary
    print_colored("\n\n" + "=" * 80, "cyan")
    print_colored("TEST SUMMARY", "cyan")
    print_colored("=" * 80 + "\n", "cyan")
    
    for i, result in enumerate(results, 1):
        print(f"{i}. {result['query'][:50]}...")
        print(f"   Expected: {result['expected'].upper()}")
        print(f"   Actual: {result['category']} ({result['actual_score']:.2%})")
        print(f"   Sources: {result['sources']}")
        print()
    
    print_colored("=" * 80, "cyan")
    print_colored("\n✓ Confidence scoring test completed!", "green")
    print_colored("\nObservations:", "yellow")
    print("- Legal queries should have higher confidence scores")
    print("- Non-legal queries should trigger low confidence warnings")
    print("- More relevant sources = higher confidence")
    print()


if __name__ == "__main__":
    test_confidence_scoring()
