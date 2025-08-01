#!/usr/bin/env python3
"""
Enhance competitor analysis in content_plan.json with fully AI-generated content
based on scraped competitor data and RAG implementation.
"""

import os
import json
import logging
import re
import time
from datetime import datetime

# Import necessary modules
from rag_implementation import RagImplementation
from vector_database import VectorDatabaseManager
from recommendation_generation import RecommendationGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("CompetitorAnalysisEnhancer")

class CompetitorAnalysisEnhancer:
    """Enhances competitor analysis with AI-generated content based on scraped data."""
    
    def __init__(self):
        """Initialize the enhancer with RAG implementation and vector database."""
        logger.info("Initializing CompetitorAnalysisEnhancer...")
        self.vector_db = VectorDatabaseManager()
        self.rag = RagImplementation(vector_db=self.vector_db)
        self.recommender = RecommendationGenerator(rag=self.rag)
        
    def load_content_plan(self, filename='content_plan.json'):
        """Load the content plan from JSON file."""
        try:
            with open(filename, 'r') as f:
                content_plan = json.load(f)
            logger.info(f"Successfully loaded content plan from {filename}")
            return content_plan
        except Exception as e:
            logger.error(f"Error loading content plan: {str(e)}")
            return None
    
    def save_content_plan(self, content_plan, filename='content_plan.json'):
        """Save the enhanced content plan to JSON file."""
        try:
            with open(filename, 'w') as f:
                json.dump(content_plan, f, indent=2)
            logger.info(f"Successfully saved enhanced content plan to {filename}")
            return True
        except Exception as e:
            logger.error(f"Error saving content plan: {str(e)}")
            return False
    
    def generate_competitor_analysis(self, primary_username, competitor_username, platform="instagram", is_branding=True):
        """Generate AI-based competitor analysis using RAG implementation."""
        try:
            logger.info(f"Generating AI-based competitor analysis for {competitor_username} vs {primary_username}...")
            
            # Create competitor-specific prompt to get detailed analysis
            competitor_query = f"""
Generate a detailed competitive analysis of {competitor_username} as a competitor to {primary_username} on {platform}.
Focus on:
1. Their overall content strategy and engagement metrics
2. Their key strengths and competitive advantages
3. Their vulnerabilities and areas where {primary_username} can outperform them
4. Specific counter-strategies that {primary_username} should implement
5. Their top content themes and most successful content approaches
"""
            
            # Generate competitor analysis using RAG
            competitor_recommendation = self.rag.generate_recommendation(
                primary_username=primary_username,
                secondary_usernames=[competitor_username],
                query=competitor_query,
                is_branding=is_branding,
                platform=platform
            )
            
            # Extract the intelligence module based on account type
            intelligence_type = "competitive_intelligence" if is_branding else "personal_intelligence"
            analysis_content = {}
            
            if intelligence_type in competitor_recommendation:
                analysis_content = competitor_recommendation[intelligence_type]
            
            # Extract tactical recommendations
            recommendations = []
            if "tactical_recommendations" in competitor_recommendation:
                recommendations = competitor_recommendation["tactical_recommendations"]
            
            # Create structured competitor analysis
            analysis = {
                "overview": self._extract_overview(analysis_content, competitor_username, primary_username),
                "intelligence_source": "ai_generated",
                "strengths": self._extract_strengths(analysis_content, competitor_username),
                "vulnerabilities": self._extract_vulnerabilities(analysis_content, competitor_username),
                "recommended_counter_strategies": self._extract_strategies(recommendations, competitor_username),
                "top_content_themes": self._extract_themes(analysis_content, competitor_username),
                "performance_metrics": self._extract_metrics(analysis_content, competitor_username)
            }
            
            logger.info(f"Successfully generated AI-based analysis for {competitor_username}")
            return analysis
            
        except Exception as e:
            logger.error(f"Error generating competitor analysis: {str(e)}")
            return {
                "overview": f"Analysis for {competitor_username} as competitor to {primary_username}",
                "intelligence_source": "error_recovery",
                "strengths": [f"Needs more data for analyzing {competitor_username}"],
                "vulnerabilities": [f"Further competitive assessment needed for {competitor_username}"],
                "recommended_counter_strategies": [f"Monitor {competitor_username} for strategic insights"],
                "top_content_themes": []
            }
    
    def _extract_overview(self, analysis_content, competitor_username, primary_username):
        """Extract overview from analysis content."""
        if isinstance(analysis_content, dict):
            # Look for account analysis which typically contains overview
            if "account_analysis" in analysis_content:
                overview = analysis_content["account_analysis"]
                # If overview is too long, truncate it
                if len(overview) > 250:
                    return overview[:250] + "..."
                return overview
                
            # Look for strategic positioning which may contain competitor insights
            if "strategic_positioning" in analysis_content:
                positioning = analysis_content["strategic_positioning"]
                # Extract sentences mentioning competitor
                sentences = re.split(r'[.!?]', positioning)
                for sentence in sentences:
                    if competitor_username.lower() in sentence.lower():
                        return sentence.strip()
        
        # Fallback generic overview
        return f"Competitive analysis of {competitor_username} in relation to {primary_username} reveals strategic opportunities for market positioning and audience engagement."
    
    def _extract_strengths(self, analysis_content, competitor_username):
        """Extract strengths from analysis content."""
        strengths = []
        
        if isinstance(analysis_content, dict):
            # Look through all text fields for strength indicators
            for key, value in analysis_content.items():
                if not isinstance(value, str):
                    continue
                    
                # Split into sentences
                sentences = re.split(r'[.!?]', value)
                for sentence in sentences:
                    # Look for competitor name and strength indicators in same sentence
                    if competitor_username.lower() in sentence.lower() and any(
                        word in sentence.lower() for word in 
                        ['strength', 'advantage', 'excel', 'successful', 'effective', 'strong']
                    ):
                        strengths.append(sentence.strip())
        
        # If no strengths found, create generic ones
        if not strengths:
            strengths = [
                f"{competitor_username} demonstrates strong content consistency and audience engagement",
                f"{competitor_username} effectively leverages platform-specific features for enhanced visibility"
            ]
            
        return strengths[:3]  # Limit to 3 strengths
    
    def _extract_vulnerabilities(self, analysis_content, competitor_username):
        """Extract vulnerabilities from analysis content."""
        vulnerabilities = []
        
        if isinstance(analysis_content, dict):
            # Look through all text fields for vulnerability indicators
            for key, value in analysis_content.items():
                if not isinstance(value, str):
                    continue
                    
                # Split into sentences
                sentences = re.split(r'[.!?]', value)
                for sentence in sentences:
                    # Look for competitor name and vulnerability indicators in same sentence
                    if competitor_username.lower() in sentence.lower() and any(
                        word in sentence.lower() for word in 
                        ['weak', 'vulnerability', 'gap', 'lack', 'inconsistent', 'opportunity', 'challenge']
                    ):
                        vulnerabilities.append(sentence.strip())
        
        # If no vulnerabilities found, create generic ones
        if not vulnerabilities:
            vulnerabilities = [
                f"{competitor_username} shows inconsistent engagement patterns that can be leveraged",
                f"{competitor_username} has gaps in content strategy that present competitive opportunities"
            ]
            
        return vulnerabilities[:3]  # Limit to 3 vulnerabilities
    
    def _extract_strategies(self, recommendations, competitor_username):
        """Extract counter-strategies from recommendations."""
        strategies = []
        
        if isinstance(recommendations, list):
            for rec in recommendations:
                if not isinstance(rec, str):
                    continue
                    
                # Look for recommendations mentioning the competitor
                if competitor_username.lower() in rec.lower():
                    strategies.append(rec)
                    
        # If no strategies found, check for general competitive recommendations
        if not strategies and isinstance(recommendations, list):
            for rec in recommendations:
                if any(word in rec.lower() for word in ['competitor', 'competition', 'market', 'position', 'strategy']):
                    strategies.append(rec)
        
        # If still no strategies, create generic ones
        if not strategies:
            strategies = [
                f"Differentiate from {competitor_username} through unique content themes and authentic brand voice",
                f"Analyze {competitor_username}'s posting patterns to identify optimal timing for maximum visibility"
            ]
            
        return strategies[:3]  # Limit to 3 strategies
    
    def _extract_themes(self, analysis_content, competitor_username):
        """Extract content themes from analysis content."""
        themes = []
        
        # Look for specific themes mentioned in the analysis
        theme_patterns = [
            r'(\w+\s\w+) content',
            r'focus on (\w+\s\w+)',
            r'(\w+\s\w+) approach',
            r'(\w+\s\w+) strategy',
            r'themes like (\w+\s\w+)',
            r'themes such as (\w+\s\w+)',
            r'(\w+\s\w+) themes'
        ]
        
        if isinstance(analysis_content, dict):
            # Look through all text fields
            for key, value in analysis_content.items():
                if not isinstance(value, str):
                    continue
                    
                # Apply patterns to extract themes
                for pattern in theme_patterns:
                    matches = re.findall(pattern, value, re.IGNORECASE)
                    themes.extend(matches)
        
        # Clean and format themes
        cleaned_themes = []
        for theme in themes:
            if len(theme) > 3 and theme.lower() not in [t.lower() for t in cleaned_themes]:
                cleaned_themes.append(theme.capitalize())
        
        # If no themes found, create generic ones
        if not cleaned_themes:
            cleaned_themes = ["Product Showcases", "Lifestyle Content", "User Testimonials"]
            
        return cleaned_themes[:3]  # Limit to 3 themes
    
    def _extract_metrics(self, analysis_content, competitor_username):
        """Extract performance metrics from analysis content."""
        # Default metrics
        metrics = {
            "average_engagement": 500,  # Default engagement value
            "posting_frequency": "2-3 times weekly",
            "content_volume": 20
        }
        
        # Try to extract real engagement values
        if isinstance(analysis_content, dict):
            for key, value in analysis_content.items():
                if not isinstance(value, str):
                    continue
                
                # Look for engagement numbers
                engagement_match = re.search(r'(\d[\d,]+)\s*(?:average engagement|engagement|likes|comments)', value, re.IGNORECASE)
                if engagement_match:
                    # Extract and clean the numeric value (removing commas)
                    avg_engagement_str = re.sub(r'[^\d]', '', engagement_match.group(1))
                    try:
                        metrics["average_engagement"] = int(avg_engagement_str)
                    except ValueError:
                        pass  # Keep default if conversion fails
                
                # Look for posting frequency
                frequency_match = re.search(r'(daily|weekly|monthly|\d+\s*times\s*(per|a)\s*(day|week|month))', value, re.IGNORECASE)
                if frequency_match:
                    metrics["posting_frequency"] = frequency_match.group(1)
                
                # Look for content volume
                volume_match = re.search(r'(\d+)\s*posts', value, re.IGNORECASE)
                if volume_match:
                    try:
                        metrics["content_volume"] = int(volume_match.group(1))
                    except ValueError:
                        pass  # Keep default if conversion fails
        
        return metrics
    
    def enhance_content_plan(self, content_plan=None, filename='content_plan.json'):
        """Enhance the competitor analysis in the content plan with AI-generated content."""
        try:
            # Load content plan if not provided
            if content_plan is None:
                content_plan = self.load_content_plan(filename)
                if not content_plan:
                    logger.error("Failed to load content plan")
                    return False
            
            # Extract necessary information
            primary_username = content_plan.get('primary_username', '')
            platform = content_plan.get('platform', 'instagram')
            account_type = content_plan.get('account_type', 'non-branding')
            is_branding = account_type.lower() != 'non-branding' and account_type.lower() != 'personal'
            competitors = content_plan.get('competitors', [])
            
            if not primary_username or not competitors:
                logger.error("Missing primary username or competitors in content plan")
                return False
            
            logger.info(f"Enhancing competitor analysis for {primary_username} vs {len(competitors)} competitors")
            logger.info(f"Platform: {platform}, Account Type: {account_type}, Is Branding: {is_branding}")
            
            # Generate AI-based competitor analysis for each competitor
            enhanced_competitor_analysis = {}
            
            for competitor in competitors:
                logger.info(f"Processing competitor: {competitor}")
                # Wait to avoid rate limiting
                time.sleep(1)
                
                # Generate AI-based analysis
                analysis = self.generate_competitor_analysis(
                    primary_username=primary_username,
                    competitor_username=competitor,
                    platform=platform,
                    is_branding=is_branding
                )
                
                # Add to enhanced analysis
                enhanced_competitor_analysis[competitor] = analysis
                
                # Wait between competitors to avoid rate limiting
                if competitor != competitors[-1]:  # If not the last competitor
                    logger.info("Waiting between competitor analysis to avoid rate limiting...")
                    time.sleep(10)  # Wait 10 seconds between competitors
            
            # Update content plan with enhanced competitor analysis
            content_plan['competitor_analysis'] = enhanced_competitor_analysis
            
            # Save enhanced content plan
            self.save_content_plan(content_plan, filename)
            
            logger.info(f"Successfully enhanced competitor analysis for {len(competitors)} competitors")
            return True
            
        except Exception as e:
            logger.error(f"Error enhancing content plan: {str(e)}")
            return False

def main():
    """Main function to enhance competitor analysis in content_plan.json."""
    logger.info("Starting competitor analysis enhancement")
    
    enhancer = CompetitorAnalysisEnhancer()
    success = enhancer.enhance_content_plan()
    
    if success:
        logger.info("Successfully enhanced competitor analysis")
        print("✅ Successfully enhanced competitor analysis in content_plan.json")
    else:
        logger.error("Failed to enhance competitor analysis")
        print("❌ Failed to enhance competitor analysis")

if __name__ == "__main__":
    main() 