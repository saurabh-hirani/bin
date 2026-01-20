#!/usr/bin/env python3
import json
import requests
import argparse
from datetime import datetime

def load_credentials():
    with open('credentials.json', 'r') as f:
        return json.load(f)

def list_meetings(limit=5, output_json=False):
    creds = load_credentials()
    api_key = creds['fathom_api_key']
    
    headers = {
        'X-Api-Key': api_key,
        'Content-Type': 'application/json'
    }
    
    url = 'https://api.fathom.ai/external/v1/meetings'
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        meetings = data.get('items', [])[:limit]
        
        if output_json:
            print(json.dumps(meetings, indent=2))
        else:
            print(f"Latest {len(meetings)} meetings:\n")
            
            for i, meeting in enumerate(meetings, 1):
                title = meeting.get('title', 'No title')
                meeting_title = meeting.get('meeting_title', '')
                created_at = meeting.get('created_at', '')
                meeting_url = meeting.get('url', '')
                recording_id = meeting.get('recording_id', '')
                recorded_by = meeting.get('recorded_by', {}).get('name', 'Unknown')
                
                # Format date
                if created_at:
                    dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    formatted_date = dt.strftime('%Y-%m-%d %H:%M:%S')
                else:
                    formatted_date = 'Unknown date'
                
                print(f"{i}. {title}")
                if meeting_title and meeting_title != title:
                    print(f"   Meeting: {meeting_title}")
                print(f"   date: {formatted_date}")
                print(f"   recorded_by: {recorded_by}")
                print(f"   meeting_url: {meeting_url}")
                print(f"   recording_id: {recording_id}")
                print()
    else:
        print(f"Error: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--last", type=int, default=5, help="Number of meetings to list")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()
    
    list_meetings(args.last, args.json)
