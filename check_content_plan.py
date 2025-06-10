#!/usr/bin/env python3
"""
Check if content_plan.json has next_post_prediction in the right place.
"""

import json
import os

def check_content_plan(filename='content_plan.json'):
    """Check content plan structure"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            content_plan = json.load(f)
            
        # Check if recommendation section exists
        if 'recommendation' not in content_plan:
            print("ERROR: 'recommendation' section missing in content_plan.json")
            return False
            
        # Check if next_post_prediction exists in recommendation
        if 'next_post_prediction' not in content_plan['recommendation']:
            print("WARNING: 'next_post_prediction' not found in content_plan['recommendation']")
            
            # Check if it exists at the top level
            if 'next_post_prediction' in content_plan:
                print("INFO: 'next_post_prediction' found at top level of content_plan.json")
                print("\nTop-level next_post_prediction content:")
                print(json.dumps(content_plan['next_post_prediction'], indent=2))
                
                # Print field counts to help diagnose
                fields = content_plan['next_post_prediction'].keys()
                print(f"\nFields: {list(fields)}")
                return True
            else:
                print("ERROR: 'next_post_prediction' not found anywhere in content_plan.json")
                return False
        else:
            # It exists in recommendation - print the content
            print("INFO: 'next_post_prediction' found in content_plan['recommendation']")
            print("\nNext post prediction content:")
            print(json.dumps(content_plan['recommendation']['next_post_prediction'], indent=2))
            
            # Print field counts to help diagnose
            fields = content_plan['recommendation']['next_post_prediction'].keys()
            print(f"\nFields: {list(fields)}")
            return True
            
    except FileNotFoundError:
        print(f"ERROR: {filename} not found")
        return False
    except json.JSONDecodeError:
        print(f"ERROR: {filename} is not valid JSON")
        return False
    except Exception as e:
        print(f"ERROR: Unexpected error: {str(e)}")
        return False
        
if __name__ == "__main__":
    check_content_plan() 