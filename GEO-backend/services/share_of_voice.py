from typing import List, Dict, Any
import statistics
from dotenv import load_dotenv
load_dotenv()

def calculate_share_of_voice(brand_results: List[Dict[str, Any]], competitors: List[str]) -> Dict[str, Any]:
    """
    Perform Share of Voice Analysis comparing brand against competitors
    
    Args:
        brand_results: Scoring results for the main brand
        competitors: List of competitor brand names
    
    Returns:
        dict: Share of Voice analysis with rankings and scores
    """
    
    # Calculate aggregated metrics for the main brand
    brand_name = brand_results[0]['brand_name'] if brand_results else "Unknown"
    brand_metrics = aggregate_brand_metrics(brand_results, brand_name)
    
    # Initialize all brands (main brand + competitors)
    all_brands = [brand_metrics]
    
    # For competitors, we need to analyze them from the same responses
    for competitor in competitors:
        competitor_metrics = analyze_competitor_from_responses(brand_results, competitor)
        all_brands.append(competitor_metrics)
    
    # Calculate normalized share percentages based on normalized_visibility
    total_normalized_visibility = sum(b['normalized_visibility'] for b in all_brands)
    
    if total_normalized_visibility > 0:
        for brand in all_brands:
            # Recalculate normalized_visibility as percentage of total
            brand['share_percentage'] = round((brand['normalized_visibility'] / total_normalized_visibility) * 100, 2)
            # Override normalized_visibility with the new percentage value
            brand['normalized_visibility'] = brand['share_percentage']
    else:
        for brand in all_brands:
            brand['share_percentage'] = 0
            brand['normalized_visibility'] = 0
    
    # Rank brands by weighted score
    ranked_brands = sorted(all_brands, key=lambda x: x['weighted_score'], reverse=True)
    
    # Add rank information
    for rank, brand in enumerate(ranked_brands, 1):
        brand['rank'] = rank
    
    return {
        'ranked_brands': ranked_brands,
        'total_brands_analyzed': len(ranked_brands),
        'main_brand': brand_name,
        'main_brand_rank': next((b['rank'] for b in ranked_brands if b['brand_name'] == brand_name), 0)
    }

def aggregate_brand_metrics(results: List[Dict[str, Any]], brand_name: str) -> Dict[str, float]:
    """
    Aggregate metrics for a single brand from all LLM responses
    
    Args:
        results: List of scoring results
        brand_name: Name of the brand
    
    Returns:
        dict: Aggregated metrics
    """
    
    if not results:
        return {
            'brand_name': brand_name,
            'normalized_visibility': 0,
            'average_positioning': 0,
            'weighted_score': 0,
            'total_mentions': 0,
            'total_prompts': 0,
            'mention_rate': 0
        }
    
    # Extract all scores
    visibility_scores = [r['scores']['normalized_visibility'] for r in results]
    positioning_scores = [r['scores']['average_positioning'] for r in results if r['scores']['average_positioning'] > 0]
    weighted_scores = [r['scores']['weighted_score'] for r in results]
    mentions = [r for r in results if r['scores']['mention_score'] > 0]
    
    return {
        'brand_name': brand_name,
        'normalized_visibility': round(statistics.mean(visibility_scores), 2) if visibility_scores else 0,
        'average_positioning': round(statistics.mean(positioning_scores), 2) if positioning_scores else 0,
        'weighted_score': round(statistics.mean(weighted_scores), 2) if weighted_scores else 0,
        'total_mentions': len(mentions),
        'total_prompts': len(results),
        'mention_rate': round((len(mentions) / len(results)) * 100, 2) if results else 0
    }

def analyze_competitor_from_responses(brand_results: List[Dict[str, Any]], competitor_name: str) -> Dict[str, float]:
    """
    Analyze competitor mentions in the same responses used for main brand
    
    Args:
        brand_results: Scoring results containing responses
        competitor_name: Name of competitor to analyze
    
    Returns:
        dict: Competitor metrics
    """
    
    import re
    from .scoring_engine import (
        calculate_mention_score, 
        calculate_position_score, 
        calculate_richness_score, 
        calculate_keyword_score,
        calculate_normalized_visibility,
        calculate_weighted_score
    )
    
    competitor_scores = []
    
    for result in brand_results:
        response_text = result['response']
        
        # Calculate scores for competitor
        mention = calculate_mention_score(response_text, competitor_name)
        position = calculate_position_score(response_text, competitor_name)
        richness = calculate_richness_score(response_text, competitor_name)
        keyword = calculate_keyword_score(response_text, competitor_name)
        
        # Calculate derived metrics
        normalized_vis = calculate_normalized_visibility(mention, position)
        weighted = calculate_weighted_score(mention, position, richness, keyword)
        
        # Get position number
        from .scoring_engine import find_brand_position
        position_info = find_brand_position(response_text, competitor_name)
        avg_pos = position_info['position'] if position_info['position'] > 0 else 0
        
        competitor_scores.append({
            'mention_score': mention,
            'position_score': position,
            'normalized_visibility': normalized_vis,
            'average_positioning': avg_pos,
            'weighted_score': weighted
        })
    
    # Aggregate competitor scores
    mentions = [s for s in competitor_scores if s['mention_score'] > 0]
    positioning_scores = [s['average_positioning'] for s in competitor_scores if s['average_positioning'] > 0]
    
    return {
        'brand_name': competitor_name,
        'normalized_visibility': round(statistics.mean([s['normalized_visibility'] for s in competitor_scores]), 2) if competitor_scores else 0,
        'average_positioning': round(statistics.mean(positioning_scores), 2) if positioning_scores else 0,
        'weighted_score': round(statistics.mean([s['weighted_score'] for s in competitor_scores]), 2) if competitor_scores else 0,
        'total_mentions': len(mentions),
        'total_prompts': len(competitor_scores),
        'mention_rate': round((len(mentions) / len(competitor_scores)) * 100, 2) if competitor_scores else 0
    }

def calculate_llm_specific_metrics(results: List[Dict[str, Any]], llm_name: str) -> Dict[str, Any]:
    """
    Calculate metrics for a specific LLM
    
    Args:
        results: All scoring results
        llm_name: Name of the LLM to analyze
    
    Returns:
        dict: LLM-specific metrics
    """
    
    llm_results = [r for r in results if r.get('llm_name') == llm_name]
    
    if not llm_results:
        return {
            'llm_name': llm_name,
            'total_prompts': 0,
            'avg_normalized_visibility': 0,
            'avg_positioning': 0,
            'avg_weighted_score': 0,
            'mention_rate': 0
        }
    
    mentions = [r for r in llm_results if r['scores']['mention_score'] > 0]
    positioning_scores = [r['scores']['average_positioning'] for r in llm_results if r['scores']['average_positioning'] > 0]
    
    return {
        'llm_name': llm_name,
        'total_prompts': len(llm_results),
        'avg_normalized_visibility': round(statistics.mean([r['scores']['normalized_visibility'] for r in llm_results]), 2),
        'avg_positioning': round(statistics.mean(positioning_scores), 2) if positioning_scores else 0,
        'avg_weighted_score': round(statistics.mean([r['scores']['weighted_score'] for r in llm_results]), 2),
        'mention_rate': round((len(mentions) / len(llm_results)) * 100, 2)
    }

def generate_sov_insights(sov_data: Dict[str, Any]) -> List[str]:
    """
    Generate actionable insights from Share of Voice analysis
    
    Args:
        sov_data: Share of Voice analysis results
    
    Returns:
        list: List of insight strings
    """
    
    insights = []
    ranked_brands = sov_data['ranked_brands']
    main_brand = sov_data['main_brand']
    main_brand_rank = sov_data['main_brand_rank']
    
    # Overall position insight
    if main_brand_rank == 1:
        insights.append(f"🏆 {main_brand} leads in share of voice across all analyzed competitors")
    elif main_brand_rank <= 3:
        insights.append(f"📈 {main_brand} ranks #{main_brand_rank} in share of voice - strong visibility position")
    else:
        insights.append(f"📊 {main_brand} ranks #{main_brand_rank} in share of voice - opportunity for improvement")
    
    # Find main brand data
    main_brand_data = next((b for b in ranked_brands if b['brand_name'] == main_brand), None)
    
    if main_brand_data:
        # Mention rate insight
        if main_brand_data['mention_rate'] > 70:
            insights.append(f"✅ Excellent organic visibility with {main_brand_data['mention_rate']:.1f}% mention rate")
        elif main_brand_data['mention_rate'] > 40:
            insights.append(f"⚠️ Moderate organic visibility with {main_brand_data['mention_rate']:.1f}% mention rate")
        else:
            insights.append(f"🔴 Low organic visibility with {main_brand_data['mention_rate']:.1f}% mention rate - needs SEO/content improvement")
        
        # Positioning insight
        if main_brand_data['average_positioning'] > 0:
            if main_brand_data['average_positioning'] <= 3:
                insights.append(f"🎯 Strong positioning - typically appears in top 3 positions (avg: {main_brand_data['average_positioning']:.1f})")
            else:
                insights.append(f"📍 Average positioning at position {main_brand_data['average_positioning']:.1f} - room for improvement")
    
    # Competitive gap insight
    if len(ranked_brands) > 1:
        top_brand = ranked_brands[0]
        if main_brand_rank > 1:
            gap = top_brand['weighted_score'] - main_brand_data['weighted_score']
            insights.append(f"🎯 Close gap with {top_brand['brand_name']} (leader) - difference of {gap:.1f} points")
    
    return insights