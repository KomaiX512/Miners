#!/usr/bin/env python3
"""
Verify and fix competitor fields in content_plan.json
This script focuses specifically on the 'strategies' and 'weaknesses' fields
that are causing errors in the competitor analysis process.

Usage:
  python verify_competitor_fields.py [content_plan.json]
"""

import json
import os
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('__main__')

def verify_competitor_fields(content_plan_file='content_plan.json'):
    """
    Check if all required competitor fields, especially 'strategies' and 'weaknesses',
    are present and valid in the content plan.
    """
    try:
        # Check if content plan exists
        if not os.path.exists(content_plan_file):
            logger.error(f"{content_plan_file} not found")
            return False
            
        # Load the content plan
        with open(content_plan_file, 'r') as f:
            content_plan = json.load(f)
        
        # Check if competitors exist
        if 'competitors' not in content_plan or not content_plan['competitors']:
            logger.warning("No competitors found in content plan")
            return False
            
        # Check if competitor_analysis exists
        if 'competitor_analysis' not in content_plan or not content_plan['competitor_analysis']:
            logger.warning("No competitor_analysis found in content plan")
            return False
            
        competitors = content_plan['competitors']
        competitor_analysis = content_plan['competitor_analysis']
        
        print(f"Found {len(competitors)} competitors in content plan", flush=True)
        print(f"Found {len(competitor_analysis)} competitors in analysis", flush=True)
        
        # Check for mismatches
        missing_competitors = [c for c in competitors if c not in competitor_analysis]
        extra_competitors = [c for c in competitor_analysis if c not in competitors]
        
        if missing_competitors:
            print(f"WARNING: {len(missing_competitors)} competitors missing from analysis: {', '.join(missing_competitors)}", flush=True)
        
        if extra_competitors:
            print(f"WARNING: {len(extra_competitors)} extra competitors in analysis: {', '.join(extra_competitors)}", flush=True)
        
        # Required fields to check
        required_fields = [
            "overview", 
            "strengths", 
            "vulnerabilities", 
            "weaknesses",   # Critical field causing errors
            "recommended_counter_strategies",
            "strategies"    # Critical field causing errors
        ]
        
        # Check each competitor analysis
        is_valid = True
        fixed_count = 0
        
        for competitor in competitors:
            if competitor in competitor_analysis:
                comp_data = competitor_analysis[competitor]
                print(f"\nChecking competitor: {competitor}", flush=True)
                
                # Check for required fields
                missing_fields = []
                for field in required_fields:
                    if field not in comp_data or not comp_data[field]:
                        missing_fields.append(field)
                
                if missing_fields:
                    is_valid = False
                    print(f"   - Missing fields: {', '.join(missing_fields)}", flush=True)
                
                # Check strengths
                if "strengths" in comp_data and comp_data["strengths"]:
                    num_strengths = len(comp_data["strengths"])
                    print(f"   - Strengths: {num_strengths} items", flush=True)
                    for i, strength in enumerate(comp_data["strengths"][:2], 1):
                        print(f"     {i}. {strength[:50]}...", flush=True)
                    if num_strengths > 2:
                        print(f"     ... and {num_strengths - 2} more", flush=True)
                
                # Check strategies (critical field causing errors)
                if "strategies" in comp_data and comp_data["strategies"]:
                    num_strategies = len(comp_data["strategies"])
                    print(f"   - Strategies: {num_strategies} items", flush=True)
                    for i, strategy in enumerate(comp_data["strategies"][:2], 1):
                        print(f"     {i}. {strategy[:50]}...", flush=True)
                    if num_strategies > 2:
                        print(f"     ... and {num_strategies - 2} more", flush=True)
                
                # Check weaknesses (critical field causing errors)
                if "weaknesses" in comp_data and comp_data["weaknesses"]:
                    num_weaknesses = len(comp_data["weaknesses"])
                    print(f"   - Weaknesses: {num_weaknesses} items", flush=True)
                    for i, weakness in enumerate(comp_data["weaknesses"][:2], 1):
                        print(f"     {i}. {weakness[:50]}...", flush=True)
                    if num_weaknesses > 2:
                        print(f"     ... and {num_weaknesses - 2} more", flush=True)
                
                # Attempt to fix if invalid
                if missing_fields:
                    comp_data_fixed = fix_competitor_fields(comp_data, competitor)
                    competitor_analysis[competitor] = comp_data_fixed
                    fixed_count += 1
            else:
                print(f"\nWARNING: No analysis for competitor {competitor}", flush=True)
                is_valid = False
        
        # Save if fixed
        if fixed_count > 0:
            print(f"\nFixed {fixed_count} competitor entries, saving content plan...", flush=True)
            with open(content_plan_file, 'w') as f:
                json.dump(content_plan, f, indent=2)
            print("Content plan saved successfully", flush=True)
        
        return is_valid
    except Exception as e:
        logger.error(f"Error verifying competitor fields: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def fix_competitor_fields(comp_data, competitor_name):
    """Fix missing fields in competitor data"""
    fixed_data = comp_data.copy()
    
    # Ensure basic fields exist
    if "overview" not in fixed_data or not fixed_data["overview"]:
        fixed_data["overview"] = f"Competitive analysis for {competitor_name}"
        
    if "intelligence_source" not in fixed_data or not fixed_data["intelligence_source"]:
        fixed_data["intelligence_source"] = "verified_fix" 
    
    # Fix crucial field: strategies
    if "strategies" not in fixed_data or not fixed_data["strategies"]:
        # Try to copy from recommended_counter_strategies if available
        if "recommended_counter_strategies" in fixed_data and fixed_data["recommended_counter_strategies"]:
            fixed_data["strategies"] = fixed_data["recommended_counter_strategies"].copy()
            print(f"   ✓ Fixed strategies by copying from recommended_counter_strategies", flush=True)
        else:
            fixed_data["strategies"] = [
                f"Primary competitive strategy used by {competitor_name}", 
                f"Secondary market positioning approach for {competitor_name}"
            ]
            print(f"   ✓ Fixed strategies with default values", flush=True)
    
    # Fix crucial field: weaknesses
    if "weaknesses" not in fixed_data or not fixed_data["weaknesses"]:
        # Try to copy from vulnerabilities if available
        if "vulnerabilities" in fixed_data and fixed_data["vulnerabilities"]:
            fixed_data["weaknesses"] = fixed_data["vulnerabilities"].copy()
            print(f"   ✓ Fixed weaknesses by copying from vulnerabilities", flush=True)
        else:
            fixed_data["weaknesses"] = [
                f"Primary weakness in {competitor_name}'s content strategy",
                f"Secondary operational weakness in {competitor_name}'s approach"
            ]
            print(f"   ✓ Fixed weaknesses with default values", flush=True)
    
    # Fix strengths
    if "strengths" not in fixed_data or not fixed_data["strengths"]:
        fixed_data["strengths"] = [
            f"Key market strength of {competitor_name}",
            f"Core competency of {competitor_name}"
        ]
        print(f"   ✓ Fixed strengths with default values", flush=True)
    
    # Fix vulnerabilities
    if "vulnerabilities" not in fixed_data or not fixed_data["vulnerabilities"]:
        # Try to copy from weaknesses if available
        if "weaknesses" in fixed_data and fixed_data["weaknesses"]:
            fixed_data["vulnerabilities"] = fixed_data["weaknesses"].copy()
            print(f"   ✓ Fixed vulnerabilities by copying from weaknesses", flush=True)
        else:
            fixed_data["vulnerabilities"] = [
                f"Strategic vulnerability in {competitor_name}'s market approach",
                f"Opportunity for differentiation against {competitor_name}"
            ]
            print(f"   ✓ Fixed vulnerabilities with default values", flush=True)
    
    # Fix recommended_counter_strategies
    if "recommended_counter_strategies" not in fixed_data or not fixed_data["recommended_counter_strategies"]:
        # Try to copy from strategies if available
        if "strategies" in fixed_data and fixed_data["strategies"]:
            fixed_data["recommended_counter_strategies"] = fixed_data["strategies"].copy()
            print(f"   ✓ Fixed recommended_counter_strategies by copying from strategies", flush=True)
        else:
            fixed_data["recommended_counter_strategies"] = [
                f"Primary counter-strategy against {competitor_name}",
                f"Secondary positioning tactic versus {competitor_name}"
            ]
            print(f"   ✓ Fixed recommended_counter_strategies with default values", flush=True)
    
    return fixed_data

if __name__ == "__main__":
    content_plan_file = "content_plan.json"
    if len(sys.argv) > 1:
        content_plan_file = sys.argv[1]
    
    print(f"Verifying competitor fields in {content_plan_file}...", flush=True)
    result = verify_competitor_fields(content_plan_file)
    
    if result:
        print("\n✅ All competitor fields are valid!", flush=True)
        sys.exit(0)
    else:
        print("\n⚠️ Some competitor fields were fixed or are still invalid", flush=True)
        sys.exit(1) 