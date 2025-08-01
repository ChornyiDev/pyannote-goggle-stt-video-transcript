#!/usr/bin/env python3
"""
Simple test for the transcript formatting function
"""

def format_transcript_segments(transcript_segments):
    """Format transcript segments as array of objects with speaker, time, and text"""
    formatted_segments = []
    
    for segment in transcript_segments:
        # Convert start time to HH:MM format
        start_seconds = int(segment['start'])
        hours = start_seconds // 3600
        minutes = (start_seconds % 3600) // 60
        time_formatted = f"{hours:02d}:{minutes:02d}"
        
        formatted_segments.append({
            "speaker": segment['speaker'],
            "time": time_formatted,
            "transcript": segment['text']
        })
    
    return formatted_segments

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
