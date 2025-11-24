def build_strategist_meta_prompt(brand: str, topic: str) -> str:
    """Original function kept for backward compatibility"""
    return f"""
You are a senior brand and marketing strategist who specializes in visibility improvement through AI search engines.

Your goal is to generate 15 highly specific, user-style prompts that reflect **real and recent search queries** (as of 2025) people might ask about, especially related to **"{topic}"**. These prompts should be designed as if pulled from recent Google Trends or SEO tools from the year 2025.

It should be the top 15 searches which users in India search today (latest year), about the product category that "{brand}" belongs to. The brand is only provided for you to understand the product category, consumer intent, and competitive context — **do not mention the brand in any of the prompts**.

These prompts should include:
- Questions about features, products, or services
- Organic prompts that help check the **brand's organic visibility** in the market by revealing where it stands among top players
- Prompts like "top 5 brands in [category]" to validate visibility — e.g., if the topic is "whey protein", include prompts like "top 5 whey protein brands in India"
- Comparisons with competitors of brand 
- Product specifications, technical details, or usage instructions
- Product reputation, reviews, or recent developments as of 2025

Output Format:
Return a **numbered list of 15 unique, diverse prompts** tailored to the input brand and topic.

All prompts should relate directly to the product: "{topic}" and category of "{brand}".

FINAL FORMAT INSTRUCTIONS:
- Return exactly 15 prompts, numbered from 1 to 15
- Use this structure: `1. [prompt]`, `2. [prompt]`, ..., `15. [prompt]`
- Each prompt must be a single natural-sounding question and organic
- Do not include brand name in the prompts as the prompts must be organic 
- Keep your search area limited to India only.
- Give only First person prompts, which real users typically ask in 2025 about this category.
Begin immediately with the list of prompts and give 15 prompts.
"""


def build_strategist_meta_prompt_with_context(brand: str, topic: str, context: dict) -> str:
    """
    Enhanced version with brand context for more accurate prompt generation.
    
    Args:
        brand: Brand name
        topic: Product/service topic
        context: Dictionary containing:
            - industry: Industry/sector
            - business_type: B2B/B2C/Both
            - primary_products: List of products/services
            - target_audience: Target customer description
            - key_competitors: List of competitor names
            - unique_value_proposition: What makes them different
            - category_keywords: Additional relevant keywords
    """
    
    # Build context section
    context_section = f"""
BRAND CONTEXT FOR UNDERSTANDING (DO NOT MENTION BRAND NAME IN PROMPTS):
- Brand Name: {brand} (DO NOT use this in prompts)
- Industry/Sector: {context.get('industry', 'unknown')}
- Business Type: {context.get('business_type', 'unknown')}
- Primary Products/Services: {', '.join(context.get('primary_products', [])) if context.get('primary_products') else 'general'}
- Target Audience: {context.get('target_audience', 'general consumers')}
- Key Competitors in Market: {', '.join(context.get('key_competitors', [])[:5]) if context.get('key_competitors') else 'various market players'}
- Unique Value Proposition: {context.get('unique_value_proposition', 'quality products/services')}
"""

    # Build competitor comparison section
    competitor_section = ""
    if context.get('key_competitors'):
        competitors = context.get('key_competitors', [])[:3]
        competitor_section = f"""
IMPORTANT - Include competitor comparisons:
- Create prompts comparing different brands in the {context.get('industry', 'market')}
- Example: "which is better [competitor1] vs [competitor2] for {topic}"
- Include prompts like "top 5 {context.get('industry', 'brands')} in India"
- DO NOT mention "{brand}" directly - keep prompts organic and user-focused
"""

    # Build audience-specific section
    audience_section = ""
    if context.get('target_audience') and context.get('target_audience') != 'unknown':
        audience_section = f"""
TARGET AUDIENCE CONTEXT:
- Generate prompts that {context.get('target_audience', 'users')} would typically ask
- Consider pain points and needs of {context.get('target_audience', 'this audience')}
- Include use-case specific questions relevant to {context.get('target_audience', 'end users')}
"""

    return f"""
You are a senior brand and marketing strategist who specializes in visibility improvement through AI search engines and deep industry knowledge.

{context_section}
{competitor_section}
{audience_section}

Your goal is to generate 15 highly specific, user-style prompts that reflect **real and recent search queries** (as of 2025) that people in India might ask about products/services in the **{context.get('industry', topic)}** industry, specifically related to **"{topic}"**.

These prompts should be designed as if pulled from recent Google Trends or SEO tools from the year 2025, reflecting actual user search behavior.

PROMPT CATEGORIES TO INCLUDE:
1. **Visibility & Ranking Prompts** (3-4 prompts):
   - "top 5/10 {context.get('industry', 'brands')} in India"
   - "best {topic} companies in India 2025"
   - "leading {context.get('industry', 'providers')} in [city/region]"

2. **Comparison Prompts** (2-3 prompts):
   - Compare {', '.join(context.get('key_competitors', ['different brands'])[:2])} for {topic}
   - "[competitor] vs [competitor] which is better"
   - "difference between [option1] and [option2] for {topic}"

3. **Feature & Specification Prompts** (2-3 prompts):
   - Technical details, pricing, features
   - "how much does {topic} cost in India"
   - "what are the requirements for {topic}"

4. **User Intent & Problem-Solving Prompts** (3-4 prompts):
   - "how to choose {topic} for [specific use case]"
   - "what to look for when buying/selecting {topic}"
   - Problems that {context.get('target_audience', 'users')} face

5. **Reviews & Reputation Prompts** (2-3 prompts):
   - "{topic} reviews 2025"
   - "is {topic} worth it in India"
   - "genuine vs fake {topic} in India"

CRITICAL RULES:
- **NEVER mention the brand name "{brand}" in any prompt** - keep all prompts organic
- All prompts must sound like real user queries (conversational, sometimes imperfect grammar)
- Focus on the {context.get('industry', 'industry')} sector and {context.get('target_audience', 'user')} needs
- Include location-specific queries (India, major cities)
- Use current year 2025 where relevant
- Make prompts specific to the business type ({context.get('business_type', 'B2B/B2C')})

OUTPUT FORMAT:
Return exactly 15 prompts, numbered from 1 to 15.
Use this structure: `1. [prompt]`, `2. [prompt]`, ..., `15. [prompt]`
Each prompt must be a single natural-sounding question or search query.

Begin immediately with the list of 15 prompts:
"""