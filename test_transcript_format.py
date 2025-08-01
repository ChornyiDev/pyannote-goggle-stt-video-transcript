#!/usr/bin/env python3
"""
Test script for the new transcript format functionality
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.core.media_processor import format_transcript_segments

def test_format_transcript_segments():
    """Test the format_transcript_segments function"""
    
    # Test data simulating transcript segments
    test_segments = [
        {
            'speaker': 'SPEAKER_00',
            'start': 0.0,
            'text': 'Hello, how are you today?'
        },
        {
            'speaker': 'SPEAKER_01', 
            'start': 15.5,
            'text': 'I am doing great, thank you for asking!'
        },
        {
            'speaker': 'SPEAKER_00',
            'start': 30.2,
            'text': 'That is wonderful to hear.'
        },
        {
            'speaker': 'SPEAKER_01',
            'start': 95.8,  # 1 minute 35 seconds
            'text': 'Yes, it has been a good day so far.'
        },
        {
            'speaker': 'SPEAKER_00',
            'start': 3665.0,  # 1 hour 1 minute 5 seconds 
            'text': 'Well, I think we should wrap up our conversation.'
        }
    ]
    
    # Format the segments
    formatted = format_transcript_segments(test_segments)
    
    # Print results
    print("Formatted transcript segments:")
    print("=" * 50)
    
    for segment in formatted:
        print(f"Speaker: {segment['speaker']}")
        print(f"Time: {segment['time']}")
        print(f"Transcript: {segment['transcript']}")
        print("-" * 30)
    
    # Also print as JSON-like structure
    print("\nAs JSON structure:")
    import json
    print(json.dumps(formatted, indent=2, ensure_ascii=False))
    
    return formatted

if __name__ == "__main__":
    test_format_transcript_segments()
