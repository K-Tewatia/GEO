import os
import json
import time
import math
import random
import logging
from datetime import datetime
from urllib.parse import urlparse
from typing import List, Dict, Iterable, Set, Optional, Any, Tuple
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import pandas as pd

# Google search library
from googlesearch import search

# --- Your existing project imports ---
from prompt_engine.strategist_prompt import build_strategist_meta_prompt
from prompt_engine.llm_query import query_gpt  # kept for compatibility
from response_engine.google_response_analyzer import analyze_google_result
from utils.file_writer import save_json

import re
import csv

# ----------------------------------------------------------------------
# 🔧 Config
# ----------------------------------------------------------------------
load_dotenv()
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY", "")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-20250514")
MAX_SUMMARY_CHARS = int(os.getenv("MAX_SUMMARY_CHARS", "12000"))
CONTENT_FETCH_TIMEOUT = int(os.getenv("CONTENT_FETCH_TIMEOUT", "20"))
MAX_FETCH_BYTES = int(os.getenv("MAX_FETCH_BYTES", str(1_000_000)))

logger = logging.getLogger("brand-pipeline")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

# ----------------------------------------------------------------------
# 🆕 NEW: Brand Context Enrichment Function
# ----------------------------------------------------------------------
def enrich_brand_context(brand: str, topic: str) -> Dict[str, str]:
    """
    Gather comprehensive brand context using web search and Claude analysis.
    Returns enriched context including industry, products, competitors, and target audience.
    """
    print(f"\n🔍 Gathering context for brand: {brand}")
    
    # Search for brand information
    search_queries = [
        f"{brand} company products services",
        f"{brand} what does it do",
        f"{brand} industry category"
    ]
    
    brand_info = []
    for query in search_queries:
        try:
            print(f"   🌐 Searching: {query}")
            urls = extract_google_ai_urls_serpapi(query, num_results=3)
            for url in urls[:2]:  # Limit to 2 URLs per query
                content = fetch_url_content(url, timeout=10, max_bytes=500000)
                if content:
                    brand_info.append(content[:3000])  # Limit each content chunk
        except Exception as e:
            print(f"   ⚠️ Search failed for '{query}': {e}")
    
    # Use Claude to analyze and extract brand context
    if brand_info:
        combined_text = "\n\n".join(brand_info)
        context_prompt = f"""Based on the following information about "{brand}", provide a structured analysis:

INFORMATION:
{combined_text[:8000]}

Please provide a JSON response with the following structure:
{{
    "industry": "specific industry/sector",
    "business_type": "B2B/B2C/Both",
    "primary_products": ["product1", "product2", ...],
    "target_audience": "description of target customers",
    "key_competitors": ["competitor1", "competitor2", ...],
    "unique_value_proposition": "what makes them different",
    "category_keywords": ["keyword1", "keyword2", ...]
}}

If information is not available for any field, use "unknown" or empty list."""

        try:
            messages = [
                {"role": "system", "content": "You are a brand analyst. Extract structured business information and return only valid JSON."},
                {"role": "user", "content": context_prompt}
            ]
            print("   🤖 Analyzing brand with Claude...")
            response = call_claude_direct(messages, model=CLAUDE_MODEL, max_tokens=800)
            
            # Parse JSON response
            context_data = parse_claude_json_context(response)
            print(f"   ✅ Brand context enriched: {context_data.get('industry', 'unknown')}")
            return context_data
            
        except Exception as e:
            print(f"   ⚠️ Claude analysis failed: {e}")
    
    # Fallback: Ask user for manual input
    print("\n⚠️ Could not automatically gather brand context. Please provide manually:")
    manual_context = {
        "industry": input("   Industry/Sector (e.g., logistics, technology, healthcare): ").strip() or "unknown",
        "business_type": input("   Business Type (B2B/B2C/Both): ").strip() or "unknown",
        "primary_products": input("   Primary Products/Services (comma-separated): ").strip().split(",") if input else [],
        "target_audience": input("   Target Audience: ").strip() or "unknown",
        "key_competitors": input("   Key Competitors (comma-separated): ").strip().split(",") if input else [],
        "unique_value_proposition": input("   Unique Value Proposition: ").strip() or "unknown",
        "category_keywords": []
    }
    return manual_context


def parse_claude_json_context(raw: str) -> Dict[str, Any]:
    """Parse JSON context response from Claude"""
    txt = raw.strip()
    if txt.startswith("```"):
        txt = txt.strip("`")
        if txt.lower().startswith("json"):
            txt = txt[4:].strip()
    if "{" in txt and txt.rfind("}") != -1:
        start = txt.find("{")
        end = txt.rfind("}") + 1
        txt = txt[start:end]
    
    try:
        data = json.loads(txt)
        return {
            "industry": data.get("industry", "unknown"),
            "business_type": data.get("business_type", "unknown"),
            "primary_products": data.get("primary_products", []),
            "target_audience": data.get("target_audience", "unknown"),
            "key_competitors": data.get("key_competitors", []),
            "unique_value_proposition": data.get("unique_value_proposition", "unknown"),
            "category_keywords": data.get("category_keywords", [])
        }
    except Exception as e:
        print(f"   ⚠️ JSON parsing failed: {e}")
        return {
            "industry": "unknown",
            "business_type": "unknown",
            "primary_products": [],
            "target_audience": "unknown",
            "key_competitors": [],
            "unique_value_proposition": "unknown",
            "category_keywords": []
        }


def build_enhanced_strategist_prompt(brand: str, topic: str, context: Dict[str, Any]) -> str:
    """Enhanced version of strategist prompt with brand context"""
    
    context_section = f"""
BRAND CONTEXT:
- Brand: {brand}
- Industry: {context.get('industry', 'unknown')}
- Business Type: {context.get('business_type', 'unknown')}
- Primary Products/Services: {', '.join(context.get('primary_products', [])) if context.get('primary_products') else 'unknown'}
- Target Audience: {context.get('target_audience', 'unknown')}
- Key Competitors: {', '.join(context.get('key_competitors', [])) if context.get('key_competitors') else 'unknown'}
- Unique Value: {context.get('unique_value_proposition', 'unknown')}
"""

    return f"""
You are a senior brand and marketing strategist who specializes in visibility improvement through AI search engines.

{context_section}

Your goal is to generate 15 highly specific, user-style prompts that reflect **real and recent search queries** (as of 2025) people might ask about products/services in the **{context.get('industry', topic)}** industry, specifically related to **"{topic}"**.

These prompts should be designed as if pulled from recent Google Trends or SEO tools from the year 2025.

It should be the top 15 searches which users in India search today (latest year), about the product category that "{brand}" belongs to. The brand is only provided for you to understand the product category, consumer intent, and competitive context — **do not mention the brand name "{brand}" in any of the prompts**.

These prompts should include:
- Questions about features, products, or services in the {context.get('industry', 'relevant')} industry
- Organic prompts that help check the **brand's organic visibility** in the market by revealing where it stands among top players
- Prompts like "top 5 brands/companies in [category]" to validate visibility
- Comparisons with competitors: {', '.join(context.get('key_competitors', [])[:3]) if context.get('key_competitors') else 'industry competitors'}
- Product specifications, technical details, or usage instructions
- Product reputation, reviews, or recent developments as of 2025
- Target audience specific queries: {context.get('target_audience', 'general users')}

Output Format:
Return a **numbered list of 15 unique, diverse prompts** tailored to the input brand and topic.

All prompts should relate directly to the product category: "{topic}" and industry: "{context.get('industry', 'relevant')}".

FINAL FORMAT INSTRUCTIONS:
- Return exactly 15 prompts, numbered from 1 to 15
- Use this structure: `1. [prompt]`, `2. [prompt]`, ..., `15. [prompt]`
- Each prompt must be a single natural-sounding question and organic
- Do not include brand name "{brand}" in the prompts as the prompts must be organic 
- Keep your search area limited to India only.
- Give only First person prompts, which real users typically ask in 2025 about this category.
Begin immediately with the list of prompts and give 15 prompts.
"""

# ----------------------------------------------------------------------
# 🔑 KeywordGenerator (keeping original)
# ----------------------------------------------------------------------
class KeywordGenerator:
    def __init__(self, api_key: str | None = None):
        load_dotenv()
        self.api_key = (
            api_key
            or os.getenv("SERPAPI_KEY")
            or "faebb8d85a193a573a0133a663bdbc8e82465f6a67ef7fdd87322daae6d2249b"
        )
        self.base_url = "https://serpapi.com/search.json"
    
    def generate_all_keywords(
        self,
        brand: str,
        topic: str,
        country: str = "IN",
        min_keywords: int = 40,
        context: Dict[str, Any] = None
    ) -> Dict[str, List[str]]:
        """Enhanced with context-aware keyword generation"""
        
        # Use category keywords from context if available
        base_queries = [brand, topic]
        if context and context.get('category_keywords'):
            base_queries.extend(context['category_keywords'][:3])
        
        all_keywords = []
        for query in base_queries:
            keywords = self._generate_keywords(query, country, min_keywords // len(base_queries))
            all_keywords.extend(keywords)
        
        return {
            "brand": all_keywords[:min_keywords],
            "topic": self._generate_keywords(topic, country, min_keywords),
            "brand_topic": self._generate_keywords(f"{brand} {topic}", country, min_keywords),
        }
    
    def _generate_keywords(self, query: str, country: str, min_keywords: int) -> List[str]:
        keywords: List[str] = []
        api_result = self._get_api_keywords(query, country)
        keywords.extend(api_result["rising"])
        keywords.extend(api_result["top"])
        
        if len(keywords) < min_keywords:
            keywords.extend(self._create_variations(query, min_keywords - len(keywords)))
        
        uniq = []
        seen = set()
        for kw in keywords:
            norm = kw.strip().lower()
            if norm and norm not in seen:
                seen.add(norm)
                uniq.append(kw.strip())
        return uniq[:min_keywords]
    
    def _get_api_keywords(self, query: str, country: str) -> Dict[str, List[str]]:
        params = {
            "engine": "google_trends",
            "q": query,
            "data_type": "RELATED_QUERIES",
            "geo": country,
            "hl": "en",
            "api_key": self.api_key,
        }
        try:
            response = requests.get(self.base_url, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            return {
                "rising": [item["query"] for item in data.get("related_queries", {}).get("rising", [])],
                "top": [item["query"] for item in data.get("related_queries", {}).get("top", [])],
            }
        except Exception as e:
            print(f"⚠️ API Error for '{query}': {str(e)[:100]}...")
            return {"rising": [], "top": []}
    
    def _create_variations(self, base_query: str, count: int) -> List[str]:
        modifiers = [
            "best", "buy", "price", "review", "how to use", "benefits",
            "online", "near me", "in india", "2024", "latest", "new",
            "discount", "offer", "coupon", "vs", "alternatives", "compare",
            "guide", "tutorial", "features", "pros and cons", "side effects",
            "genuine", "authentic", "premium", "organic", "natural"
        ]
        questions = [
            f"is {base_query} good",
            f"how to choose {base_query}",
            f"where to buy {base_query}",
            f"when to use {base_query}",
            f"why {base_query} is popular"
        ]
        variations = [f"{mod} {base_query}" for mod in modifiers]
        variations.extend(questions)
        return variations[:count]

# [Keep all other existing functions unchanged - extract_google_ai_urls_serpapi, is_non_google_link, 
# extract_numbered_lines, build_keyword_prompts, dedupe, fetch_url_content, get_brand_sentences,
# heuristic_sentiment, call_claude_direct, parse_claude_json, summarize_brand_from_text,
# enrich_url_record, explode_citations, normalize_results, enrich_all_rows, save_to_csv]

# ... [Include ALL the remaining helper functions from your original code] ...

# For brevity, I'm showing the key changes. Copy all your existing helper functions here.

def extract_google_ai_urls_serpapi(query: str, num_results: int = 10) -> List[str]:
    """Extract URLs from Google search using SerpAPI (more reliable)"""
    api_key = os.getenv("SERPAPI_KEY") or "faebb8d85a193a573a0133a663bdbc8e82465f6a67ef7fdd87322daae6d2249b"
    
    params = {
        "engine": "google",
        "q": query,
        "api_key": api_key,
        "num": num_results,
        "hl": "en",
        "gl": "in"
    }
    
    try:
        print(f"   🔍 Searching Google via SerpAPI for: {query}")
        response = requests.get("https://serpapi.com/search.json", params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        urls = []
        for result in data.get("organic_results", []):
            url = result.get("link")
            if url and is_non_google_link(url):
                urls.append(url)
        
        print(f"   ✅ Found {len(urls)} URLs")
        return urls
    except Exception as e:
        print(f"   ⚠️ SerpAPI search failed for '{query}': {e}")
        return []

def is_non_google_link(url: str) -> bool:
    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    return not any(
        google_domain in domain
        for google_domain in ["google.com", "googleusercontent.com", "googleapis.com", "gstatic.com"]
    )

def extract_numbered_lines(text: str) -> List[str]:
    prompts = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line[0].isdigit():
            if ". " in line:
                _, rest = line.split(". ", 1)
            elif ") " in line:
                _, rest = line.split(") ", 1)
            else:
                rest = line.lstrip("0123456789).:- ").strip()
            if rest:
                prompts.append(rest)
    return prompts

def build_keyword_prompts(keywords: Iterable[str], limit: int = 5) -> List[str]:
    templates: List[str] = []
    prompts: List[str] = []
    for kw in list(keywords)[:limit]:
        for t in templates:
            prompts.append(t.format(kw=kw))
    return prompts

def dedupe(prompts: Iterable[str]) -> List[str]:
    seen = set()
    result = []
    for p in prompts:
        norm = p.strip().lower()
        if norm and norm not in seen:
            seen.add(norm)
            result.append(p.strip())
    return result

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
HEADERS = {"User-Agent": USER_AGENT, "Accept-Language": "en-US,en;q=0.9"}

def fetch_url_content(url: str, timeout: int = CONTENT_FETCH_TIMEOUT, max_bytes: int = MAX_FETCH_BYTES) -> str:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout, stream=True)
        resp.raise_for_status()
        content = b""
        for chunk in resp.iter_content(chunk_size=8192):
            content += chunk
            if len(content) >= max_bytes:
                break
        raw = content.decode(resp.encoding or "utf-8", errors="replace")
        soup = BeautifulSoup(raw, "html.parser")
        for bad in soup(["script", "style", "noscript", "header", "footer", "svg", "img"]):
            bad.extract()
        text = soup.get_text(" ")
        text = " ".join(text.split())
        return text
    except Exception as e:
        logger.warning(f"Fetch fail: {url} -> {e}")
        return ""

def get_brand_sentences(text, brand):
    sentences = [s.strip() for s in re.split(r'[.?!]', text)]
    brand_lower = brand.lower()
    return [s for s in sentences if brand_lower in s.lower()]

POS_WORDS = {
    "good","great","excellent","amazing","love","loved","awesome","best","positive","recommended","recommend","reliable","trustworthy","high quality","effective","premium","organic","natural","value","worth","decent","reliable","legit"
}
NEG_WORDS = {
    "bad","poor","terrible","awful","hate","hated","worst","negative","problem","issue","scam","fake","low quality","ineffective","expensive","overpriced","side effect","complaint","not worthy"
}

def heuristic_sentiment(text: str, brand: str) -> Tuple[str, int]:
    low = text.lower()
    brand_mentions = low.count(brand.lower()) if brand else 0
    pos_hits = neg_hits = 0
    brand_sents = get_brand_sentences(text, brand)
    for sent in brand_sents:
        if any(pos in sent for pos in POS_WORDS):
            pos_hits += 1
        if any(neg in sent for neg in NEG_WORDS):
            neg_hits += 1
    if brand_mentions == 0:
        return "neutral", 0
    if pos_hits > neg_hits and pos_hits > 0:
        return "positive", brand_mentions
    if neg_hits > pos_hits and neg_hits > 0:
        return "negative", brand_mentions
    global_pos = sum(1 for w in POS_WORDS if w in low)
    global_neg = sum(1 for w in NEG_WORDS if w in low)
    if global_pos > global_neg and global_pos > 0:
        return "positive", brand_mentions
    if global_neg > global_pos and global_neg > 0:
        return "negative", brand_mentions
    return "neutral", brand_mentions

CLAUDE_SUMMARY_SYSTEM_PROMPT = "You are a concise brand insights assistant. Given webpage text and a brand name, extract brand mentions, summarize brand-relevant info in 2-4 sentences, and classify sentiment (positive / negative / neutral). If the brand is not meaningfully discussed, return an empty summary and neutral sentiment. Output STRICT JSON with keys: brand_mentions(int), sentiment(str), summary(str)."

def call_claude_direct(messages: List[Dict[str, str]], model: str = CLAUDE_MODEL, max_tokens: int = 512) -> str:
    """Call Claude API directly using Anthropic's Messages API"""
    if not CLAUDE_API_KEY:
        raise RuntimeError("CLAUDE_API_KEY not set; cannot call Claude API.")
    
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": CLAUDE_API_KEY,
        "anthropic-version": "2023-06-01"
    }
    
    system_message = ""
    user_messages = []
    for msg in messages:
        if msg.get("role") == "system":
            system_message = msg.get("content", "")
        else:
            user_messages.append(msg)
    
    payload = {
        "model": model,
        "max_tokens": max_tokens,
        "temperature": 0.2,
        "messages": user_messages
    }
    
    if system_message:
        payload["system"] = system_message
    
    resp = requests.post(url, headers=headers, json=payload, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    
    content = data["content"][0]["text"]
    return content.strip()

def parse_claude_json(raw: str) -> Tuple[int, str, str]:
    """Parse JSON response from Claude"""
    txt = raw.strip()
    if txt.startswith("```"):
        txt = txt.strip("`")
        if txt.lower().startswith("json"):
            txt = txt[4:].strip()
    if "{" in txt and txt.rfind("}") != -1:
        start = txt.find("{")
        end = txt.rfind("}") + 1
        txt = txt[start:end]
    try:
        data = json.loads(txt)
    except Exception:
        data = {}
    brand_mentions = int(data.get("brand_mentions", 0) or 0)
    sentiment = (data.get("sentiment") or "neutral").strip().lower()
    if sentiment not in {"positive", "negative", "neutral"}:
        sentiment = "NA"
    summary = (data.get("summary") or "").strip()
    return brand_mentions, sentiment, summary

def summarize_brand_from_text(text: str, brand: str) -> Tuple[int, str, str]:
    """Summarize brand mentions and sentiment using Claude"""
    if not text:
        return 0, "neutral", ""
    clipped = text[:MAX_SUMMARY_CHARS]
    user_prompt = (
        f"BRAND: {brand}\n\nTEXT:\n{clipped}\n\n"
        "Return JSON per instructions."
    )
    messages = [
        {"role": "system", "content": CLAUDE_SUMMARY_SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]
    try:
        raw = call_claude_direct(messages, model=CLAUDE_MODEL)
        return parse_claude_json(raw)
    except Exception as e:
        logger.warning(f"Claude summarization failed ({e}); falling back to heuristics.")
        sent, bcount = heuristic_sentiment(text, brand)
        return bcount, sent, ""

def enrich_url_record(record: Dict[str, Any], brand: str) -> Dict[str, Any]:
    url = record.get("url")
    if not url:
        newrec = record.copy()
        newrec.setdefault("brand_mentions", 0)
        newrec.setdefault("sentiment", "neutral")
        newrec.setdefault("brand_summary", "")
        return newrec
    text = fetch_url_content(url)
    bcount, sentiment, summary = summarize_brand_from_text(text, brand)
    newrec = record.copy()
    newrec["brand_mentions"] = bcount
    newrec["sentiment"] = sentiment
    newrec["brand_summary"] = summary
    if bcount >= 5:
        conf = 0.9
    elif bcount >= 1:
        conf = 0.7
    else:
        conf = 0.4
    if "confidence" in newrec:
        try:
            newrec["confidence"] = max(float(newrec["confidence"]), conf)
        except Exception:
            newrec["confidence"] = conf
    else:
        newrec["confidence"] = conf
    return newrec

EXPECTED_COL_ORDER = [
    "prompt",
    "url",
    "search_rank",
    "brand_mentions",
    "sentiment",
    "brand_summary",
    "confidence",
    "source",
]

def explode_citations(prompt: str, base: Dict[str, Any], urls: List[str]) -> List[Dict[str, Any]]:
    rows = []
    for idx, u in enumerate(urls, start=1):
        row = {
            "prompt": prompt,
            "url": u,
            "search_rank": idx,
            "source": base.get("source", "unknown"),
            "brand_mentions": None,
            "sentiment": None,
            "brand_summary": None,
            "confidence": base.get("confidence", 0.5),
        }
        rows.append(row)
    return rows

def normalize_results(raw_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for item in raw_results:
        prompt = item.get("prompt", "")
        source = item.get("source", "unknown")
        if "citations" in item and isinstance(item["citations"], list):
            rows.extend(explode_citations(prompt, item, item["citations"]))
            continue
        url = item.get("url")
        if url:
            row = {
                "prompt": prompt,
                "url": url,
                "search_rank": item.get("search_rank", item.get("rank", 0)),
                "source": source,
                "brand_mentions": item.get("brand_mentions"),
                "sentiment": item.get("sentiment"),
                "brand_summary": item.get("brand_summary"),
                "confidence": item.get("confidence", 0.5),
            }
            rows.append(row)
            continue
    return rows

def enrich_all_rows(rows: List[Dict[str, Any]], brand: str) -> List[Dict[str, Any]]:
    enriched: List[Dict[str, Any]] = []
    total = len(rows)
    for i, r in enumerate(rows, 1):
        print(f"   ↪ ({i}/{total}) Analyzing {r.get('url','?')[:60]}...")
        enriched.append(enrich_url_record(r, brand))
    return enriched

def save_to_csv(data: list, path: str, brand: str = "", topic: str = ""):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if not data:
        print("⚠️ No data to write.")
        return

    custom_order = [
        "prompt",
        "url",
        "search_rank",
        "brand_mentions",
        "sentiment",
        "brand_summary",
        "confidence",
        "source",
    ]
    with open(path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=custom_order)
        writer.writeheader()
        for row in data:
            ordered_row = {col: row.get(col, "") for col in custom_order}
            writer.writerow(ordered_row)

    total_urls = len(data)
    branded_rows = [r for r in data if r.get("brand_mentions", 0) and r.get("brand_mentions", 0) > 0]
    avg_positioning = (
        sum(r.get("search_rank", 0) for r in branded_rows) / len(branded_rows)
        if branded_rows else 0.0
    )
    visibility_score = (len(branded_rows) / total_urls) * 100 if total_urls > 0 else 0.0
    metrics_section = [
        [],
        ["METRIC", "VALUE"],
        ["brand", brand],
        ["topic", topic],
        ["total_urls", total_urls],
        ["urls_with_brand_mentions", len(branded_rows)],
        ["brand_visibility_score (%)", round(visibility_score, 2)],
        ["average_brand_positioning", round(avg_positioning, 2)],
    ]
    with open(path, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(metrics_section)
    print(f"✅ Data and brand metrics written to: {path}")

# ----------------------------------------------------------------------
# 🎯 ENHANCED MAIN PIPELINE
# ----------------------------------------------------------------------
def main():
    try:
        brand = input("Enter brand name: ").strip()
        topic = input("Enter product name or description (press Enter to use brand name): ").strip()
        
        if not brand:
            print("❌ Brand name is required!")
            return
        
        if not topic:
            topic = brand
            print(f"ℹ️ No topic provided, using brand name as topic: {topic}")
        
        print(f"✅ Brand: {brand}, Topic: {topic}")
        
        # 🆕 NEW: Enrich brand context
        brand_context = enrich_brand_context(brand, topic)
        print(f"\n📊 Brand Context Summary:")
        print(f"   Industry: {brand_context.get('industry')}")
        print(f"   Business Type: {brand_context.get('business_type')}")
        print(f"   Products: {', '.join(brand_context.get('primary_products', [])[:3])}")
        
        MAX_PROMPTS = 15
        COUNTRY_CODE = "IN"
        NUM_GOOGLE_RESULTS = 10

        # 🆕 Use enhanced prompt with context
        print("\n🧠 Generating context-aware prompts from Claude...")
        try:
            meta_prompt = build_enhanced_strategist_prompt(brand, topic, brand_context)
            print(f"✅ Enhanced meta prompt generated: {len(meta_prompt)} chars")
        except Exception as e:
            print(f"❌ Error building meta prompt: {e}")
            import traceback
            traceback.print_exc()
            return
        
        try:
            messages = [
                {"role": "system", "content": "You are a strategist prompt generator with deep industry knowledge."},
                {"role": "user", "content": meta_prompt},
            ]
            print("📡 Calling Claude API...")
            llm_output = call_claude_direct(messages, model=CLAUDE_MODEL, max_tokens=300)
            print(f"✅ Claude responded: {len(llm_output)} chars")
            base_prompts = extract_numbered_lines(llm_output)
            print(f"✅ Extracted {len(base_prompts)} prompts from Claude")
        except Exception as e:
            print(f"❌ Error calling Claude: {e}")
            import traceback
            traceback.print_exc()
            return

        print("\n🔍 Fetching context-aware keywords...")
        try:
            kg = KeywordGenerator()
            keywords_data = kg.generate_all_keywords(
                brand=brand, 
                topic=topic, 
                country=COUNTRY_CODE, 
                min_keywords=40,
                context=brand_context
            )
            brand_keywords = keywords_data.get("brand", [])
            print(f"✅ Fetched {len(brand_keywords)} brand keywords.")
        except Exception as e:
            print(f"❌ Error fetching keywords: {e}")
            import traceback
            traceback.print_exc()
            brand_keywords = []

        keyword_prompts = build_keyword_prompts(brand_keywords)
        all_prompts = dedupe(base_prompts + keyword_prompts)[:MAX_PROMPTS]

        print(f"\n✅ Final prompt count: {len(all_prompts)}")
        for i, p in enumerate(all_prompts, 1):
            print(f"{i}. {p}")

        all_results_raw: List[Dict[str, Any]] = []
        
        # Process each prompt with SerpAPI Google search
        for prompt in all_prompts:
            try:
                print(f"\n🔍 [SerpAPI Google Search] → {prompt}")
                urls = extract_google_ai_urls_serpapi(prompt, num_results=NUM_GOOGLE_RESULTS)
                if urls:
                    all_results_raw.append({
                        "prompt": prompt, 
                        "source": "serpapi_google", 
                        "brand": brand, 
                        "citations": urls
                    })
                else:
                    print(f"   ⚠️ No URLs found for prompt: {prompt}")
            except Exception as e:
                print(f"⚠️ SerpAPI search failed for '{prompt[:50]}...': {e}")
            
            try:
                print("🌐 [Google Analyzer] Analyzing results...")
                google_results = analyze_google_result(prompt, brand)
                for gr in google_results:
                    gr.setdefault("prompt", prompt)
                    gr.setdefault("source", gr.get("source", "google_analyzer"))
                all_results_raw.extend(google_results)
            except Exception as e:
                print(f"⚠️ Google analyzer failed for '{prompt[:50]}...': {e}")

        rows = normalize_results(all_results_raw)

        if not rows:
            if brand_keywords:
                print("⚠️ No rows found from prompts, falling back to direct brand keywords as URLs (placeholders).")
                rows = []
                for idx, kw in enumerate(brand_keywords[:MAX_PROMPTS], start=1):
                    row = {
                        "prompt": kw,
                        "url": "",
                        "search_rank": idx,
                        "brand_mentions": None,
                        "sentiment": None,
                        "brand_summary": None,
                        "confidence": 0.5,
                        "source": "fallback_keywords",
                    }
                    rows.append(row)
            else:
                print("⚠️ No rows to process and no fallback keywords available; exiting early.")
                return

        print(f"\n📊 Normalized {len(rows)} URL rows. Starting brand enrichment (Claude)…")
        enriched_rows = enrich_all_rows(rows, brand)

        # Save results with context metadata
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_brand = brand.replace(" ", "_").replace("/", "_")
        safe_topic = topic.replace(" ", "_").replace("/", "_")
        os.makedirs("data", exist_ok=True)

        json_filename = f"data/{safe_brand}_{safe_topic}_{timestamp}.json"
        csv_filename = f"data/{safe_brand}_{safe_topic}_{timestamp}.csv"

        # Add context to JSON output
        output_data = {
            "brand_context": brand_context,
            "results": enriched_rows
        }
        save_json(output_data, json_filename)
        save_to_csv(enriched_rows, csv_filename, brand=brand, topic=topic)

        print("\n✅ Report saved:")
        print(f"→ {json_filename}")
        print(f"→ {csv_filename}")
        print(f"\n📈 Brand Context Applied:")
        print(f"   Industry: {brand_context.get('industry')}")
        print(f"   Competitors tracked: {', '.join(brand_context.get('key_competitors', [])[:3])}")
        
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR in main(): {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("🚀 Starting Enhanced Brand Pipeline with Context Intelligence...")
    main()
    print("✅ Pipeline completed!")


# ----------------------------------------------------------------------
# Enhanced generate_geo_score function
# ----------------------------------------------------------------------
def generate_geo_score(brand: str, topic: str) -> Dict[str, Any]:
    MAX_PROMPTS = 15
    COUNTRY_CODE = "IN"
    NUM_GOOGLE_RESULTS = 10

    # Enrich context first
    brand_context = enrich_brand_context(brand, topic)

    print("\n🧠 Generating prompts from Claude...")
    meta_prompt = build_enhanced_strategist_prompt(brand, topic, brand_context)
    messages = [
        {"role": "system", "content": "You are a strategist prompt generator."},
        {"role": "user", "content": meta_prompt},
    ]
    llm_output = call_claude_direct(messages, model=CLAUDE_MODEL, max_tokens=300)
    base_prompts = extract_numbered_lines(llm_output)

    print("🔍 Fetching brand keywords...")
    kg = KeywordGenerator()
    keywords_data = kg.generate_all_keywords(
        brand=brand, 
        topic=topic, 
        country=COUNTRY_CODE, 
        min_keywords=40,
        context=brand_context
    )
    brand_keywords = keywords_data.get("brand", [])
    print(f"✅ Fetched {len(brand_keywords)} brand keywords.")

    keyword_prompts = build_keyword_prompts(brand_keywords)
    all_prompts = dedupe(base_prompts + keyword_prompts)[:MAX_PROMPTS]

    all_results_raw: List[Dict[str, Any]] = []
    for prompt in all_prompts:
        try:
            urls = extract_google_ai_urls_serpapi(prompt, num_results=NUM_GOOGLE_RESULTS)
            if urls:
                all_results_raw.append({
                    "prompt": prompt, 
                    "source": "serpapi_google", 
                    "brand": brand, 
                    "citations": urls
                })
        except Exception as e:
            print(f"SerpAPI search failed for '{prompt[:50]}...': {e}")
        
        try:
            google_results = analyze_google_result(prompt, brand)
            for gr in google_results:
                gr.setdefault("prompt", prompt)
                gr.setdefault("source", gr.get("source", "google_analyzer"))
            all_results_raw.extend(google_results)
        except Exception as e:
            print(f"Google analyzer failed for '{prompt[:50]}...': {e}")

    rows = normalize_results(all_results_raw)

    if not rows:
        rows = [
            {
                "prompt": kw,
                "url": "",
                "search_rank": idx,
                "brand_mentions": None,
                "sentiment": None,
                "brand_summary": None,
                "confidence": 0.5,
                "source": "fallback_keywords",
            }
            for idx, kw in enumerate(brand_keywords[:MAX_PROMPTS], start=1)
        ]

    enriched_rows = enrich_all_rows(rows, brand)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_brand = brand.replace(" ", "_").replace("/", "_")
    safe_topic = topic.replace(" ", "_").replace("/", "_")
    os.makedirs("data", exist_ok=True)

    json_filename = f"data/{safe_brand}_{safe_topic}_{timestamp}.json"
    csv_filename = f"data/{safe_brand}_{safe_topic}_{timestamp}.csv"

    output_data = {
        "brand_context": brand_context,
        "results": enriched_rows
    }
    save_json(output_data, json_filename)
    save_to_csv(enriched_rows, csv_filename, brand=brand, topic=topic)

    return {
        "brand": brand,
        "topic": topic,
        "context": brand_context,
        "total_results": len(enriched_rows),
        "json_path": json_filename,
        "csv_path": csv_filename
    }