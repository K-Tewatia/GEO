import re
from typing import Dict, List, Any

from dotenv import load_dotenv
load_dotenv()
def calculate_scores(responses, brand_name, keywords=None):
    """
    Calculate visibility scores for each response
    
    Args:
        responses (list): List of response dictionaries
        brand_name (str): The brand name to analyze
        keywords (list): Optional list of SEO keywords for enhanced scoring
    
    Returns:
        list: List of scored results
    """
    
    scored_results = []
    
    for response_data in responses:
        if response_data.get('error'):
            # Skip error responses
            continue
        
        prompt = response_data['prompt']
        response_text = response_data['response']
        prompt_index = response_data.get('prompt_index', 0)
        llm_name = response_data.get('llm_name', 'Claude')
        
        # Calculate individual score components
        mention_score =  calculate_mention_score(response_text, brand_name)
        position_score = calculate_position_score(response_text, brand_name)
        richness_score = calculate_richness_score(response_text, brand_name)
        keyword_score = calculate_keyword_score(response_text, brand_name, keywords)
        
        # Calculate total visibility score
        total_score = mention_score + position_score + richness_score + keyword_score
        
        # Prepare detailed analysis
        analysis = analyze_brand_context(response_text, brand_name)
        
        # Calculate new metrics
        normalized_visibility = calculate_normalized_visibility(mention_score, position_score)
        average_positioning = analysis['position'] if analysis['position'] > 0 else 0
        weighted_score = calculate_weighted_score(mention_score, position_score, richness_score, keyword_score)
        
        scored_result = {
            'prompt': prompt,
            'response': response_text,
            'brand_name': brand_name,
            'llm_name': llm_name,
            'scores': {
                'mention_score': mention_score,
                'position_score': position_score,
                'richness_score': richness_score,
                'keyword_score': keyword_score,
                'total_score': min(100, total_score),
                'normalized_visibility': normalized_visibility,
                'average_positioning': average_positioning,
                'weighted_score': weighted_score
            },
            'analysis': analysis,
            'prompt_index': prompt_index
        }
        
        scored_results.append(scored_result)
    
    return scored_results

def calculate_normalized_visibility(mention_score, position_score):
    """
    Calculate normalized brand visibility score (0-100)
    Formula: (mention_score / 20 * 50) + (position_score / 30 * 50)
    """
    mention_component = (mention_score / 20) * 50 if mention_score > 0 else 0
    position_component = (position_score / 30) * 50 if position_score > 0 else 0
    return round(mention_component + position_component, 2)

def calculate_weighted_score(mention_score, position_score, richness_score, keyword_score):
    """
    Calculate weighted score with emphasis on position and mentions
    Formula: (mention * 0.3) + (position * 0.4) + (richness * 0.2) + (keyword * 0.1)
    """
    weighted = (mention_score * 0.3) + (position_score * 0.4) + (richness_score * 0.2) + (keyword_score * 0.1)
    return round(weighted, 2)

def calculate_mention_score(response_text, brand_name):
    """
    Calculate mention score (20 points max)
    
    Args:
        response_text (str): The response text
        brand_name (str): The brand name to look for
    
    Returns:
        int: Mention score (0 or 20)
    """
    
    # Case-insensitive search for brand name
    pattern = re.compile(re.escape(brand_name), re.IGNORECASE)
    
    if pattern.search(response_text):
        return 20
    else:
        return 0

def calculate_position_score(response_text, brand_name):
    """
    Calculate position score (30 points max)
    
    Args:
        response_text (str): The response text
        brand_name (str): The brand name to look for
    
    Returns:
        float: Position score (0-30)
    """
    
    # First check if brand is mentioned
    if not re.search(re.escape(brand_name), response_text, re.IGNORECASE):
        return 0
    
    # Find the position of the brand in any list
    position_info = find_brand_position(response_text, brand_name)
    
    if position_info['position'] == -1:
        return 0  # Brand mentioned but not in a list
    
    position = position_info['position']
    total_items = position_info['total_items']
    
    if total_items <= 1:
        return 30  # Only item in list gets full score
    
    # Calculate normalized position score
    # Position Score = 1 - ((N - 1) / (T - 1)) * 30
    # where N is position (1-based) and T is total items
    position_score = (1 - ((position - 1) / (total_items - 1))) * 30
    
    return round(position_score, 1)

def calculate_richness_score(response_text, brand_name):
    """
    Calculate description richness score (30 points max)
    
    Args:
        response_text (str): The response text
        brand_name (str): The brand name to look for
    
    Returns:
        int: Richness score (0-30)
    """
    
    # Find brand mentions and their context
    brand_contexts = extract_brand_context(response_text, brand_name)
    
    if not brand_contexts:
        return 0
    
    # Analyze the richness of the description
    total_words = 0
    has_benefits = False
    has_details = False
    
    for context in brand_contexts:
        words = len(context.split())
        total_words += words
        
        # Check for benefit-related keywords
        benefit_keywords = ['benefit', 'advantage', 'helps', 'improves', 'provides', 'offers', 'features', 'known for']
        if any(keyword in context.lower() for keyword in benefit_keywords):
            has_benefits = True
        
        # Check for detailed information
        detail_keywords = ['product', 'ingredient', 'certified', 'organic', 'natural', 'formula', 'supplement', 'vitamin']
        if any(keyword in context.lower() for keyword in detail_keywords):
            has_details = True
    
    # Score based on description richness
    if total_words <= 10:
        base_score = 5  # Short, one-line mention
    elif total_words <= 30:
        base_score = 15  # Medium description
    else:
        base_score = 25  # Rich description
    
    # Bonus points for benefits and details
    if has_benefits:
        base_score += 3
    if has_details:
        base_score += 2
    
    return min(30, base_score)

def calculate_keyword_score(response_text, brand_name, keywords=None):
    """
    Calculate keyword strength score (20 points max)
    
    Args:
        response_text (str): The response text
        brand_name (str): The brand name to look for
        keywords (list): Optional list of SEO keywords
    
    Returns:
        int: Keyword score (0-20)
    """
    
    # Find brand mentions and their context
    brand_contexts = extract_brand_context(response_text, brand_name)
    
    if not brand_contexts:
        return 0
    
    # Strong keywords that indicate positive positioning
    strong_keywords = [
        'top', 'leading', 'best', 'premium', 'excellent', 'outstanding',
        'certified', 'innovative', 'award-winning', 'trusted', 'reputable',
        'popular', 'renowned', 'established', 'quality', 'superior',
        'recommended', 'preferred', 'favorite', 'market leader', 'industry leader',
        'first', 'pioneer', 'cutting-edge', 'advanced', 'professional',
        'authentic', 'genuine', 'pure', 'natural', 'organic'
    ]
    
    # Add SEO keywords if provided
    if keywords:
        # Extract individual words from keywords
        for keyword in keywords[:15]:  # Limit to top 15
            words = keyword.lower().split()
            strong_keywords.extend(words)
    
    score = 0
    found_keywords = set()
    
    for context in brand_contexts:
        context_lower = context.lower()
        for keyword in strong_keywords:
            if keyword in context_lower and keyword not in found_keywords:
                found_keywords.add(keyword)
                # Different keywords have different weights
                if keyword in ['top', 'leading', 'best', 'market leader', 'industry leader']:
                    score += 5
                elif keyword in ['premium', 'excellent', 'outstanding', 'award-winning']:
                    score += 4
                elif keyword in ['certified', 'innovative', 'trusted', 'reputable']:
                    score += 3
                else:
                    score += 2
    
    return min(20, score)

def find_brand_position(response_text, brand_name):
    """
    Find the position of the brand in any list structure
    
    Args:
        response_text (str): The response text
        brand_name (str): The brand name to look for
    
    Returns:
        dict: Position information
    """
    
    lines = response_text.split('\n')
    position = -1
    total_items = 0
    
    # Look for numbered lists
    numbered_items = []
    for i, line in enumerate(lines):
        if re.match(r'^\d+\.', line.strip()):
            numbered_items.append((i, line))
    
    if numbered_items:
        total_items = len(numbered_items)
        for i, (line_num, line) in enumerate(numbered_items):
            if re.search(re.escape(brand_name), line, re.IGNORECASE):
                position = i + 1
                break
    
    # If no numbered list, look for bullet points
    if position == -1:
        bullet_items = []
        for i, line in enumerate(lines):
            if re.match(r'^[-•*]\s', line.strip()):
                bullet_items.append((i, line))
        
        if bullet_items:
            total_items = len(bullet_items)
            for i, (line_num, line) in enumerate(bullet_items):
                if re.search(re.escape(brand_name), line, re.IGNORECASE):
                    position = i + 1
                    break
    
    # If still no position, look for ordinal indicators
    if position == -1:
        ordinal_pattern = r'\b(first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth)\b'
        ordinal_matches = re.finditer(ordinal_pattern, response_text, re.IGNORECASE)
        
        ordinal_map = {
            'first': 1, 'second': 2, 'third': 3, 'fourth': 4, 'fifth': 5,
            'sixth': 6, 'seventh': 7, 'eighth': 8, 'ninth': 9, 'tenth': 10
        }
        
        for match in ordinal_matches:
            sentence = get_sentence_containing_position(response_text, match.start())
            if re.search(re.escape(brand_name), sentence, re.IGNORECASE):
                position = ordinal_map[match.group().lower()]
                total_items = max(total_items, position)
                break
    
    return {
        'position': position,
        'total_items': total_items
    }

def extract_brand_context(response_text, brand_name):
    """
    Extract sentences or contexts where the brand is mentioned
    
    Args:
        response_text (str): The response text
        brand_name (str): The brand name to look for
    
    Returns:
        list: List of contexts mentioning the brand
    """
    
    sentences = re.split(r'[.!?]+', response_text)
    brand_contexts = []
    
    for sentence in sentences:
        if re.search(re.escape(brand_name), sentence, re.IGNORECASE):
            brand_contexts.append(sentence.strip())
    
    return brand_contexts

def get_sentence_containing_position(text, position):
    """
    Get the sentence containing a specific character position
    
    Args:
        text (str): The text to search
        position (int): Character position
    
    Returns:
        str: The sentence containing the position
    """
    
    sentences = re.split(r'[.!?]+', text)
    current_pos = 0
    
    for sentence in sentences:
        if current_pos <= position <= current_pos + len(sentence):
            return sentence.strip()
        current_pos += len(sentence) + 1
    
    return ""

def analyze_brand_context(response_text, brand_name):
    """
    Provide detailed analysis of how the brand is presented
    
    Args:
        response_text (str): The response text
        brand_name (str): The brand name to analyze
    
    Returns:
        dict: Detailed analysis
    """
    
    contexts = extract_brand_context(response_text, brand_name)
    position_info = find_brand_position(response_text, brand_name)
    
    analysis = {
        'is_mentioned': len(contexts) > 0,
        'mention_count': len(contexts),
        'contexts': contexts,
        'position': position_info['position'],
        'total_items_in_list': position_info['total_items'],
        'is_in_list': position_info['position'] > 0,
        'sentiment': analyze_sentiment(contexts),
        'key_attributes': extract_key_attributes(contexts, brand_name)
    }
    
    return analysis

def analyze_sentiment(contexts):
    """
    Analyze the sentiment of brand mentions
    
    Args:
        contexts (list): List of contexts mentioning the brand
    
    Returns:
        str: Sentiment analysis result
    """
    
    if not contexts:
        return "neutral"
    
    positive_words = ['good', 'great', 'excellent', 'best', 'top', 'leading', 'quality', 'trusted', 'premium', 'innovative']
    negative_words = ['bad', 'poor', 'worst', 'low', 'cheap', 'unreliable', 'questionable']
    
    positive_count = 0
    negative_count = 0
    
    for context in contexts:
        context_lower = context.lower()
        for word in positive_words:
            if word in context_lower:
                positive_count += 1
        for word in negative_words:
            if word in context_lower:
                negative_count += 1
    
    if positive_count > negative_count:
        return "positive"
    elif negative_count > positive_count:
        return "negative"
    else:
        return "neutral"

def extract_key_attributes(contexts, brand_name):
    """
    Extract key attributes mentioned about the brand
    
    Args:
        contexts (list): List of contexts mentioning the brand
        brand_name (str): The brand name
    
    Returns:
        list: List of key attributes
    """
    
    attributes = []
    
    attribute_patterns = [
        r'(organic|natural|pure|clean|premium|quality|certified|trusted|innovative|award-winning|established|reputable)',
        r'(supplements?|nutrition|vitamins?|minerals?|herbs?|botanicals?|probiotics?|protein)',
        r'(manufacturing|products?|ingredients?|formula|blend|range|line)'
    ]
    
    for context in contexts:
        for pattern in attribute_patterns:
            matches = re.findall(pattern, context, re.IGNORECASE)
            for match in matches:
                if match.lower() not in [attr.lower() for attr in attributes]:
                    attributes.append(match)
    
    return attributes[:5]  # Return top 5 attributes

def aggregate_results(scored_results):
    """
    Aggregate the results to provide summary statistics
    
    Args:
        scored_results (list): List of scored results
    
    Returns:
        dict: Aggregated summary
    """
    
    if not scored_results:
        return {
            'total_prompts': 0,
            'total_mentions': 0,
            'mention_rate': 0,
            'avg_position': 0,
            'avg_visibility_score': 0,
            'score_distribution': {},
            'top_performing_prompts': [],
            'position_distribution': {}
        }
    
    total_prompts = len(scored_results)
    mentioned_results = [r for r in scored_results if r['scores']['mention_score'] > 0]
    total_mentions = len(mentioned_results)
    
    # Calculate averages
    avg_visibility_score = sum(r['scores']['total_score'] for r in scored_results) / total_prompts
    
    # Calculate average position (only for mentioned results)
    positioned_results = [r for r in mentioned_results if r['analysis']['position'] > 0]
    avg_position = sum(r['analysis']['position'] for r in positioned_results) / len(positioned_results) if positioned_results else 0
    
    # Score distribution
    score_ranges = {'0-20': 0, '21-40': 0, '41-60': 0, '61-80': 0, '81-100': 0}
    for result in scored_results:
        score = result['scores']['total_score']
        if score <= 20:
            score_ranges['0-20'] += 1
        elif score <= 40:
            score_ranges['21-40'] += 1
        elif score <= 60:
            score_ranges['41-60'] += 1
        elif score <= 80:
            score_ranges['61-80'] += 1
        else:
            score_ranges['81-100'] += 1
    
    # Position distribution
    position_dist = {}
    for result in positioned_results:
        pos = result['analysis']['position']
        position_dist[pos] = position_dist.get(pos, 0) + 1
    
    # Top performing prompts
    top_prompts = sorted(scored_results, key=lambda x: x['scores']['total_score'], reverse=True)[:3]
    
    return {
        'total_prompts': total_prompts,
        'total_mentions': total_mentions,
        'mention_rate': (total_mentions / total_prompts) * 100,
        'avg_position': round(avg_position, 1),
        'avg_visibility_score': round(avg_visibility_score, 1),
        'score_distribution': score_ranges,
        'top_performing_prompts': [{'prompt': p['prompt'], 'score': p['scores']['total_score']} for p in top_prompts],
        'position_distribution': position_dist
    }
