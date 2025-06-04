#!/usr/bin/env python3
"""
Test script to verify that competitor extraction works correctly with the strategies field.
"""

import json
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('test_extraction')

def test_extraction():
    """Test that competitor extraction works correctly."""
    try:
        # Load the content plan
        with open('content_plan.json', 'r') as f:
            content_plan = json.load(f)
            
        # Get competitors
        competitors = content_plan.get('competitors', [])
        if not competitors:
            logger.error("No competitors found in content plan")
            return False
            
        logger.info(f"Found {len(competitors)} competitors in content plan")
        
        # Get competitor analysis
        competitor_analysis = content_plan.get('competitor_analysis', {})
        if not competitor_analysis:
            logger.error("No competitor analysis found in content plan")
            return False
            
        # For each competitor, attempt to extract fields that previously caused errors
        success = True
        for competitor in competitors:
            logger.info(f"Testing extraction for competitor: {competitor}")
            
            try:
                # Get competitor data
                comp_data = competitor_analysis.get(competitor, {})
                
                # Attempt to access the strategies field (this was causing errors)
                strategies = comp_data.get('strategies', [])
                if not strategies:
                    logger.warning(f"No strategies found for {competitor}, but field exists")
                else:
                    logger.info(f"Successfully extracted {len(strategies)} strategies for {competitor}")
                    for i, strategy in enumerate(strategies[:2], 1):
                        logger.info(f"  {i}. {strategy[:50]}{'...' if len(strategy) > 50 else ''}")
                
                # Also test the weaknesses field
                weaknesses = comp_data.get('weaknesses', [])
                if not weaknesses:
                    logger.warning(f"No weaknesses found for {competitor}, but field exists")
                else:
                    logger.info(f"Successfully extracted {len(weaknesses)} weaknesses for {competitor}")
                    for i, weakness in enumerate(weaknesses[:2], 1):
                        logger.info(f"  {i}. {weakness[:50]}{'...' if len(weakness) > 50 else ''}")
                
            except KeyError as e:
                logger.error(f"KeyError for {competitor}: {e}")
                success = False
            except Exception as e:
                logger.error(f"Error extracting data for {competitor}: {e}")
                success = False
        
        if success:
            logger.info("✅ Successfully extracted all required fields from all competitors")
            return True
        else:
            logger.error("❌ Failed to extract all required fields")
            return False
            
    except Exception as e:
        logger.error(f"Error in test: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def simulate_extraction_function():
    """Simulate the extraction function that was failing before."""
    try:
        # Load the content plan
        with open('content_plan.json', 'r') as f:
            content_plan = json.load(f)
            
        # Get competitors
        competitors = content_plan.get('competitors', [])
        
        # Get competitor analysis
        competitor_analysis = content_plan.get('competitor_analysis', {})
        
        # This simulates the code that was failing in the original implementation
        logger.info("Simulating the extraction function that was failing before...")
        
        for competitor in competitors:
            try:
                logger.info(f"Extracting detailed insights for {competitor}")
                comp_data = competitor_analysis.get(competitor, {})
                
                # This would fail if 'strategies' is missing
                strategies = comp_data['strategies']
                logger.info(f"✅ Successfully extracted strategies for {competitor}: {len(strategies)} items")
                
                # This would fail if 'weaknesses' is missing
                weaknesses = comp_data['weaknesses']
                logger.info(f"✅ Successfully extracted weaknesses for {competitor}: {len(weaknesses)} items")
                
            except KeyError as e:
                # This is the error that would occur
                logger.error(f"Error extracting detailed insights for {competitor}: {str(e)}")
                return False
                
        logger.info("✅ All extractions successful")
        return True
        
    except Exception as e:
        logger.error(f"Error in simulation: {e}")
        return False

if __name__ == "__main__":
    logger.info("Starting extraction test...")
    
    # Run basic extraction test
    test_result = test_extraction()
    
    # Run simulation of the original failing code
    simulation_result = simulate_extraction_function()
    
    if test_result and simulation_result:
        logger.info("✅✅ All tests passed successfully")
        sys.exit(0)
    else:
        logger.error("❌❌ Some tests failed")
        sys.exit(1) 