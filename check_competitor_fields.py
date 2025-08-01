#!/usr/bin/env python3
"""
Check if competitor fields are properly set in content_plan.json
"""

import json
import sys

def check_competitor_fields():
    try:
        with open('content_plan.json', 'r') as f:
            data = json.load(f)
        
        competitors = data.get('competitors', [])
        competitor_analysis = data.get('competitor_analysis', {})
        
        print(f"Found {len(competitors)} competitors in content_plan.json")
        
        for comp in competitors:
            if comp in competitor_analysis:
                has_strategies = 'strategies' in competitor_analysis[comp]
                has_weaknesses = 'weaknesses' in competitor_analysis[comp]
                
                strategies_count = len(competitor_analysis[comp].get('strategies', []))
                weaknesses_count = len(competitor_analysis[comp].get('weaknesses', []))
                
                status = "✅" if has_strategies and has_weaknesses else "❌"
                
                print(f"{status} {comp}: strategies={has_strategies} ({strategies_count} items), weaknesses={has_weaknesses} ({weaknesses_count} items)")
            else:
                print(f"❌ {comp}: Not found in competitor_analysis section")
        
        return True
    except Exception as e:
        print(f"Error checking competitor fields: {e}")
        return False

if __name__ == "__main__":
    print("Checking competitor fields in content_plan.json...")
    check_competitor_fields() 