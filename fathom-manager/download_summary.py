#!/usr/bin/env python3
import json
import requests
import argparse
import os
import sys
from datetime import datetime, timedelta

def load_credentials():
    with open('credentials.json', 'r') as f:
        return json.load(f)

def get_meetings_by_date(date_filter, title_prefix=None):
    creds = load_credentials()
    api_key = creds['fathom_api_key']
    
    headers = {
        'X-Api-Key': api_key,
        'Content-Type': 'application/json'
    }
    
    # Calculate date range for filtering
    if date_filter == "today":
        target_date = datetime.now().date()
    elif date_filter == "yesterday":
        target_date = (datetime.now() - timedelta(days=1)).date()
    elif date_filter == "last":
        # Return the latest meeting regardless of date
        url = 'https://api.fathom.ai/external/v1/meetings'
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            meetings = data.get('items', [])
            for meeting in meetings:
                title = meeting.get('title', '')
                if not title_prefix or title_prefix.lower() in title.lower():
                    return {
                        'recording_id': meeting.get('recording_id'),
                        'title': meeting.get('title', 'No title'),
                        'created_at': meeting.get('created_at', '')
                    }
        return None
    else:
        # Parse date in dd-mm-yyyy format
        try:
            target_date = datetime.strptime(date_filter, '%d-%m-%Y').date()
        except ValueError:
            print(f"Invalid date format: {date_filter}. Use dd-mm-yyyy format.")
            return None
    
    # For date-based filtering, get meetings and filter by date and title
    url = 'https://api.fathom.ai/external/v1/meetings'
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        meetings = data.get('items', [])
        
        for meeting in meetings:
            created_at = meeting.get('created_at', '')
            title = meeting.get('title', '')
            if created_at:
                meeting_date = datetime.fromisoformat(created_at.replace('Z', '+00:00')).date()
                if meeting_date == target_date:
                    if not title_prefix or title_prefix.lower() in title.lower():
                        return {
                            'recording_id': meeting.get('recording_id'),
                            'title': meeting.get('title', 'No title'),
                            'created_at': meeting.get('created_at', '')
                        }
    
    return None

def download_summary(recording_id, output_file=None):
    creds = load_credentials()
    api_key = creds['fathom_api_key']
    
    headers = {
        'X-Api-Key': api_key,
        'Content-Type': 'application/json'
    }
    
    url = f'https://api.fathom.ai/external/v1/recordings/{recording_id}/summary'
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        summary = data.get('summary', {})
        if summary is None:
            print("No summary available for this recording")
            return
        markdown_content = summary.get('markdown_formatted', '')
        
        if output_file:
            with open(output_file, 'w') as f:
                f.write(markdown_content)
            print(f"status=summary_saved file={output_file}", file=sys.stderr)
        else:
            print(markdown_content)
    else:
        print(f"Error: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("recording_id", help="Recording ID or 'last'/'today'/'yesterday'/'dd-mm-yyyy'")
    parser.add_argument("-o", "--output", help="Output file path (default: print to stdout)")
    parser.add_argument("--output-dir", help="Output directory (default: ~/Downloads/dd-mm-yyyy/)")
    parser.add_argument("--prefix", help="Filter meetings by title prefix")
    args = parser.parse_args()
    
    if args.recording_id in ["last", "today", "yesterday"] or "-" in args.recording_id:
        meeting_info = get_meetings_by_date(args.recording_id, args.prefix)
        if not meeting_info:
            print(f"No meetings found for: {args.recording_id}" + (f" with prefix: {args.prefix}" if args.prefix else ""))
            exit(1)
        recording_id = meeting_info['recording_id']
        title = meeting_info['title']
        created_at = meeting_info['created_at']
        
        # Format date
        if created_at:
            dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            formatted_date = dt.strftime('%Y-%m-%d')
        else:
            formatted_date = 'unknown date'
        
        print(f"status=downloading_summary meeting='{title}' date={formatted_date}", file=sys.stderr)
    else:
        recording_id = int(args.recording_id)
    
    if args.output:
        output_file = args.output
    elif args.output_dir:
        os.makedirs(args.output_dir, exist_ok=True)
        output_file = os.path.join(args.output_dir, "summary.md")
    else:
        output_dir = os.path.expanduser(f"~/Downloads/{datetime.now().strftime('%d-%m-%Y')}")
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, "summary.md")
    
    download_summary(recording_id, output_file)
