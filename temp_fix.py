def _extract_rag_competitor_insights(self, rag_content, competitor_name):
    """Extract specific competitor insights from RAG content."""
    try:
        # Simple extraction logic for competitor-specific insights
        competitor_insights = {
            "overview": f"RAG analysis of {competitor_name}",
            "strengths": [],
            "vulnerabilities": [],
            "recommended_counter_strategies": [],
            "themes": [],
            "positioning": f"Strategic positioning vs {competitor_name}",
            "differentiation": f"Differentiation strategy from {competitor_name}",
            "opportunity": f"Market opportunity vs {competitor_name}"
        }
        
        # Look for competitor-specific mentions in RAG content
        lines = rag_content.split('\n')
        
        # Create a version of content with sentences for easier parsing
        import re
        sentences = re.split(r'[.!?]', rag_content)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        # Find a good overview sentence that mentions the competitor
        for sentence in sentences:
            if competitor_name.lower() in sentence.lower() and len(sentence) > 30:
                competitor_insights["overview"] = sentence.strip()[:200]
                break
        
        # Extract specific insights from each line and sentence
        for text in lines + sentences:
            text_lower = text.lower()
            if competitor_name.lower() in text_lower:
                # Extract strengths
                if any(term in text_lower for term in ['strength', 'advantage', 'strong', 'excel', 'good at', 'better', 'best', 'success']):
                    competitor_insights["strengths"].append(text.strip()[:150])
                
                # Extract vulnerabilities  
                elif any(term in text_lower for term in ['vulnerab', 'weakness', 'weak', 'gap', 'opportunit', 'lack', 'limit', 'fail', 'poor']):
                    competitor_insights["vulnerabilities"].append(text.strip()[:150])
                
                # Extract counter strategies
                elif any(term in text_lower for term in ['counter', 'strategy', 'position', 'against', 'vs', 'versus', 'compare', 'outperform', 'beat', 'compete', 'focus on', 'differentiat']):
                    competitor_insights["recommended_counter_strategies"].append(text.strip()[:150])
                
                # Extract themes
                elif '#' in text:
                    themes = re.findall(r'#\w+', text)
                    competitor_insights["themes"].extend(themes[:3])
        
        # If we didn't find specific sections, look for keyword patterns
        keyword_patterns = {
            "strengths": ["strength", "advantage", "excel", "good at", "succeed", "success"],
            "vulnerabilities": ["vulnerability", "weakness", "gap", "opportunity", "lack", "limited"],
            "recommended_counter_strategies": ["counter strategy", "position against", "differentiate from", "outperform", "against"]
        }
        
        # Check each category and search for relevant keywords
        for category, keywords in keyword_patterns.items():
            if not competitor_insights[category]:  # Only if we haven't found anything yet
                for keyword in keywords:
                    pattern = rf'{re.escape(keyword)}[^.!?]*?{re.escape(competitor_name)}|{re.escape(competitor_name)}[^.!?]*?{re.escape(keyword)}'
                    matches = re.findall(pattern, rag_content, re.IGNORECASE)
                    for match in matches:
                        competitor_insights[category].append(match.strip()[:150])
                        
        # Ensure we have at least some minimal content for each section
        if not competitor_insights["strengths"]:
            competitor_insights["strengths"].append(f"Analysis of {competitor_name}'s strengths required")
            
        if not competitor_insights["vulnerabilities"]:
            competitor_insights["vulnerabilities"].append(f"Strategic vulnerability assessment for {competitor_name}")
            
        if not competitor_insights["recommended_counter_strategies"]:
            competitor_insights["recommended_counter_strategies"].append(f"Strategic positioning against {competitor_name}")
        
        return competitor_insights
        
    except Exception as e:
        logger.error(f"Error extracting RAG insights for {competitor_name}: {str(e)}")
        return {
            "overview": f"RAG extraction failed for {competitor_name}",
            "strengths": [],
            "vulnerabilities": [],
            "recommended_counter_strategies": [],
            "themes": [],
            "positioning": f"RAG positioning analysis needed for {competitor_name}",
            "differentiation": f"RAG differentiation analysis needed for {competitor_name}",
            "opportunity": f"RAG opportunity analysis needed for {competitor_name}"
        } 
