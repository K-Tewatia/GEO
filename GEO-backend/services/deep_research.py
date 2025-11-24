import os
import re
from typing import Dict, Any, List, Optional
from tavily import TavilyClient
from anthropic import Anthropic

from dotenv import load_dotenv
load_dotenv()

TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

tavily_client = TavilyClient(api_key=TAVILY_API_KEY)
anthropic_client = Anthropic(api_key=ANTHROPIC_API_KEY) if ANTHROPIC_API_KEY else None

def conduct_deep_research(brand_name: str, product_name: Optional[str] = None, 
                         website_url: Optional[str] = None, 
                         industry: Optional[str] = None) -> Dict[str, Any]:  # ✅ ADDED industry param
    """
    Conduct extensive web-based deep research using Tavily API
    
    Returns comprehensive brand information including:
    - Brand category and type
    - Market reputation and online presence
    - Product-specific insights (if provided)
    - Pricing structure (B2C/D2C brands)
    - Top 5 competitors (improved extraction with LLM validation)
    - Current trends and technologies
    """
    
    research_results = {
        'brand_category': '',
        'brand_type': '',
        'market_reputation': '',
        'online_presence': '',
        'product_insights': '',
        'pricing_structure': '',
        'competitors': [],
        'trends': '',
        'technologies': '',
        'industry': industry or '',  # ✅ Store industry in research data
        'raw_data': []
    }
    
    # Research query 1: Brand overview and category
    # ✅ ENHANCED: Include industry in query if provided
    query_1 = f"{brand_name}"
    if product_name:
        query_1 += f" {product_name}"
    if industry:
        query_1 += f" {industry}"  # ✅ Add industry context
    if website_url:
        query_1 += f" {website_url}"
    query_1 += " brand category type business model"
    
    try:
        response_1 = tavily_client.search(
            query=query_1,
            search_depth="advanced",
            max_results=5,
            include_answer=True
        )
        research_results['raw_data'].append({
            'query': query_1,
            'results': response_1.get('results', []),
            'answer': response_1.get('answer', '')
        })
        
        if response_1.get('answer'):
            research_results['brand_category'] = response_1['answer']
    except Exception as e:
        print(f"Error in brand overview research: {str(e)}")
    
    # Research query 2: Market reputation and online presence
    query_2 = f"{brand_name}"
    if industry:
        query_2 += f" {industry}"  # ✅ Add industry context
    query_2 += " market reputation reviews customer feedback online presence"
    
    try:
        response_2 = tavily_client.search(
            query=query_2,
            search_depth="advanced",
            max_results=5,
            include_answer=True
        )
        research_results['raw_data'].append({
            'query': query_2,
            'results': response_2.get('results', []),
            'answer': response_2.get('answer', '')
        })
        
        if response_2.get('answer'):
            research_results['market_reputation'] = response_2['answer']
    except Exception as e:
        print(f"Error in reputation research: {str(e)}")
    
    # Research query 3: Product-specific insights (if product provided)
    if product_name:
        query_3 = f"{brand_name} {product_name}"
        if industry:
            query_3 += f" {industry}"  # ✅ Add industry context
        query_3 += " features benefits pricing specifications"
        
        try:
            response_3 = tavily_client.search(
                query=query_3,
                search_depth="advanced",
                max_results=5,
                include_answer=True
            )
            research_results['raw_data'].append({
                'query': query_3,
                'results': response_3.get('results', []),
                'answer': response_3.get('answer', '')
            })
            
            if response_3.get('answer'):
                research_results['product_insights'] = response_3['answer']
        except Exception as e:
            print(f"Error in product research: {str(e)}")
    
    # Research query 4: Pricing structure
    query_4 = f"{brand_name}"
    if industry:
        query_4 += f" {industry}"  # ✅ Add industry context
    query_4 += " pricing cost price range B2C D2C direct to consumer"
    
    try:
        response_4 = tavily_client.search(
            query=query_4,
            search_depth="advanced",
            max_results=5,
            include_answer=True
        )
        research_results['raw_data'].append({
            'query': query_4,
            'results': response_4.get('results', []),
            'answer': response_4.get('answer', '')
        })
        
        if response_4.get('answer'):
            research_results['pricing_structure'] = response_4['answer']
    except Exception as e:
        print(f"Error in pricing research: {str(e)}")
    
    # Research query 5: Competitor Research
    competitors_data = []
    
    # ✅ ENHANCED: Use industry in competitor queries
    competitor_queries = [
        f"{brand_name} {industry if industry else ''} competitors alternatives similar companies",
        f"{brand_name} vs top {industry if industry else ''} brands comparison",
        f"companies similar to {brand_name} in {industry if industry else 'market'}",
        f"{brand_name} {industry if industry else ''} industry competitors market leaders"
    ]
    
    for query in competitor_queries:
        try:
            response = tavily_client.search(
                query=query.strip(),  # Remove extra spaces
                search_depth="advanced",
                max_results=8,
                include_answer=True
            )
            competitors_data.append({
                'query': query,
                'results': response.get('results', []),
                'answer': response.get('answer', '')
            })
            research_results['raw_data'].append({
                'query': query,
                'results': response.get('results', []),
                'answer': response.get('answer', '')
            })
        except Exception as e:
            print(f"Error in competitor research: {str(e)}")
    
    # Extract competitors using improved LLM-based method
    research_results['competitors'] = extract_competitors_with_llm(
        brand_name, 
        competitors_data,
        research_results['brand_category'],
        industry  # ✅ Pass industry to competitor extraction
    )
    
    # Research query 6: Industry trends and technologies
    # ✅ ENHANCED: Use provided industry or extract from category
    trend_industry = industry if industry else (research_results['brand_category'].split()[0] if research_results['brand_category'] else brand_name)
    query_6 = f"{trend_industry} industry trends 2025 latest technologies innovations"
    
    try:
        response_6 = tavily_client.search(
            query=query_6,
            search_depth="advanced",
            max_results=5,
            include_answer=True
        )
        research_results['raw_data'].append({
            'query': query_6,
            'results': response_6.get('results', []),
            'answer': response_6.get('answer', '')
        })
        
        if response_6.get('answer'):
            research_results['trends'] = response_6['answer']
            research_results['technologies'] = response_6['answer']
    except Exception as e:
        print(f"Error in trends research: {str(e)}")
    
    return research_results


def extract_competitors_with_llm(brand_name: str, competitors_data: List[Dict], 
                                 brand_category: str, 
                                 industry: Optional[str] = None) -> List[str]:  # ✅ ADDED industry param
    """
    Extract genuine competitors using Claude LLM for accurate identification
    """
    
    if not anthropic_client:
        print("Warning: Anthropic API not available, using fallback extraction")
        return extract_competitors_fallback(competitors_data, brand_name)
    
    # Compile all research text
    research_text = ""
    for data in competitors_data:
        if data.get('answer'):
            research_text += f"\n{data['answer']}\n"
        for result in data.get('results', [])[:3]:
            research_text += f"\n{result.get('content', '')[:500]}\n"
    
    # Limit text length to avoid token limits
    research_text = research_text[:4000]
    
    if not research_text.strip():
        print("Warning: No research text available for competitor extraction")
        return []
    
    # ✅ ENHANCED: Include industry in prompt
    industry_context = f"\nIndustry: {industry}" if industry else ""
    
    # Create LLM prompt for competitor extraction
    prompt = f"""Based on the following market research about "{brand_name}", extract EXACTLY 5 genuine competitor brand names.

Brand Category: {brand_category}{industry_context}

Research Data:
{research_text}

CRITICAL REQUIREMENTS:
1. Extract ONLY real company/brand names that are direct competitors of {brand_name}
2. DO NOT include: {brand_name} itself, generic terms, product categories, or descriptive phrases
3. Return ONLY actual competitor brand names (proper nouns)
4. Prioritize brands in the same industry/category as {brand_name}
5. If you find fewer than 5 competitors, return only the genuine ones you can identify
6. DO NOT make up brand names or include vague terms like "Other", "Energy's", "Refinery"

Format your response as a simple list, one competitor per line, with NO numbering or bullet points:
Competitor Name 1
Competitor Name 2
Competitor Name 3
etc."""

    try:
        response = anthropic_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=500,
            temperature=0.3,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        
        response_text = response.content[0].text
        
        # Extract competitor names from response
        competitors = []
        lines = response_text.strip().split('\n')
        
        for line in lines:
            # Clean the line
            line = line.strip()
            # Remove numbering if present
            line = re.sub(r'^\d+[\.\)]\s*', '', line)
            line = re.sub(r'^[-*•]\s*', '', line)
            
            # Validate it's a proper brand name
            if (line and 
                len(line) > 2 and 
                len(line) < 50 and
                brand_name.lower() not in line.lower() and
                not is_generic_term(line)):
                
                competitors.append(line)
        
        # Limit to 5 competitors
        competitors = competitors[:5]
        
        if len(competitors) > 0:
            print(f"✅ Extracted {len(competitors)} genuine competitors using LLM")
            return competitors
        else:
            print("Warning: LLM returned no valid competitors, using fallback")
            return extract_competitors_fallback(competitors_data, brand_name)
    
    except Exception as e:
        print(f"Error in LLM competitor extraction: {str(e)}")
        return extract_competitors_fallback(competitors_data, brand_name)


def is_generic_term(term: str) -> bool:
    """Check if a term is generic rather than a brand name"""
    generic_terms = [
        'other', 'refinery', 'petroleum', 'energy', 'company', 'companies',
        'brand', 'brands', 'manufacturer', 'supplier', 'provider', 'corporation',
        'industry', 'market', 'sector', 'alternative', 'competitor', 'similar',
        'various', 'many', 'several', 'numerous', 'etc', 'and more'
    ]
    
    term_lower = term.lower()
    
    # Check if it's a generic term
    if any(generic in term_lower for generic in generic_terms):
        return True
    
    # Check if it's too short or contains suspicious patterns
    if len(term) <= 2 or term.endswith("'s"):
        return True
    
    return False


def extract_competitors_fallback(competitors_data: List[Dict], exclude_brand: str) -> List[str]:
    """
    Fallback competitor extraction using heuristics
    """
    competitors = set()
    
    # Compile all text
    all_text = ""
    for data in competitors_data:
        if data.get('answer'):
            all_text += " " + data['answer']
        for result in data.get('results', [])[:3]:
            all_text += " " + result.get('content', '')[:300]
    
    # Look for capitalized phrases (potential brand names)
    # Match patterns like "Apple Inc", "Tesla Motors", "Amazon"
    brand_pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b'
    matches = re.findall(brand_pattern, all_text)
    
    for match in matches:
        # Filter out generic terms and the main brand
        if (len(match) > 2 and 
            len(match) < 50 and
            exclude_brand.lower() not in match.lower() and
            not is_generic_term(match) and
            match not in ['The', 'This', 'That', 'These', 'Those', 'India', 'China', 'USA']):
            
            competitors.add(match)
    
    # Convert to list and limit to 5
    competitors_list = list(competitors)[:5]
    
    if len(competitors_list) > 0:
        print(f"✓ Extracted {len(competitors_list)} competitors using fallback method")
    else:
        print("⚠ Warning: Could not extract any competitors from research data")
    
    return competitors_list


def get_research_summary(research_data: Dict[str, Any]) -> str:
    """Generate a concise summary of research findings"""
    summary_parts = []
    
    if research_data.get('brand_category'):
        summary_parts.append(f"**Category:** {research_data['brand_category'][:200]}")
    
    if research_data.get('market_reputation'):
        summary_parts.append(f"**Reputation:** {research_data['market_reputation'][:200]}")
    
    if research_data.get('competitors'):
        summary_parts.append(f"**Top Competitors:** {', '.join(research_data['competitors'][:5])}")
    else:
        summary_parts.append("**Top Competitors:** None identified (research in progress)")
    
    if research_data.get('pricing_structure'):
        summary_parts.append(f"**Pricing:** {research_data['pricing_structure'][:200]}")
    
    if research_data.get('trends'):
        summary_parts.append(f"**Industry Trends:** {research_data['trends'][:200]}")
    
    return "\n\n".join(summary_parts)