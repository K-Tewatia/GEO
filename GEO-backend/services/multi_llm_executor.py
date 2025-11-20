import os
import asyncio
from typing import List, Dict, Any, Optional
import json

from dotenv import load_dotenv
load_dotenv()
# LLM imports
from anthropic import Anthropic
from openai import OpenAI
import google.genai as genai

# Import Google AI Overview scraper
from services.google_ai_overview_scraper import extract_ai_overview_links, setup_driver

# API Keys
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
PERPLEXITY_API_KEY = os.environ.get("PERPLEXITY_API_KEY")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# Initialize clients
anthropic_client = Anthropic(api_key=ANTHROPIC_API_KEY) if ANTHROPIC_API_KEY else None
openai_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
gemini_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

def detect_available_llms() -> List[str]:
    """Dynamically detect which LLM APIs are available based on API keys"""
    available = []
    
    if ANTHROPIC_API_KEY:
        available.append("Claude")
    if OPENAI_API_KEY:
        available.append("ChatGPT")
    if PERPLEXITY_API_KEY:
        available.append("Perplexity")
    if GEMINI_API_KEY:
        available.append("Google AI")
    
    # Google AI Overview doesn't need API key - uses Selenium
    # Always available as it doesn't require API credentials
    available.append("Google AI Overview")
    
    return available

async def execute_claude(prompt: str) -> Dict[str, Any]:
    """Execute prompt using Claude with web search enabled"""
    try:
        response = anthropic_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            temperature=0.3,
            system="You are a knowledgeable market researcher. Provide detailed, factual responses about brands, products, and market information. Include specific examples and citations when possible.",
            messages=[{"role": "user", "content": prompt}]
        )
        
        response_text = response.content[0].text
        
        # Extract potential citations/URLs from response
        citations = extract_urls_from_text(response_text)
        
        return {
            'llm_name': 'Claude',
            'response': response_text,
            'citations': citations,
            'success': True,
            'error': None
        }
    except Exception as e:
        return {
            'llm_name': 'Claude',
            'response': '',
            'citations': [],
            'success': False,
            'error': str(e)
        }

async def execute_chatgpt(prompt: str) -> Dict[str, Any]:
    """Execute prompt using ChatGPT (GPT-4o)"""
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a knowledgeable market researcher. Provide detailed, factual responses about brands, products, and market information."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=2000
        )
        
        response_text = response.choices[0].message.content
        citations = extract_urls_from_text(response_text)
        
        return {
            'llm_name': 'ChatGPT',
            'response': response_text,
            'citations': citations,
            'success': True,
            'error': None
        }
    except Exception as e:
        return {
            'llm_name': 'ChatGPT',
            'response': '',
            'citations': [],
            'success': False,
            'error': str(e)
        }

async def execute_perplexity(prompt: str) -> Dict[str, Any]:
    """Execute prompt using Perplexity with online search"""
    try:
        import httpx
        
        headers = {
            'Authorization': f'Bearer {PERPLEXITY_API_KEY}',
            'Content-Type': 'application/json'
        }
        
        data = {
            "model": "llama-3.1-sonar-large-128k-online",
            "messages": [
                {
                    "role": "system",
                    "content": "You are a knowledgeable market researcher. Provide detailed, factual responses with citations."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.2,
            "top_p": 0.9,
            "stream": False
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                'https://api.perplexity.ai/chat/completions',
                headers=headers,
                json=data,
                timeout=60.0
            )
            response.raise_for_status()
            result = response.json()
        
        response_text = result['choices'][0]['message']['content']
        citations = result.get('citations', [])
        
        return {
            'llm_name': 'Perplexity',
            'response': response_text,
            'citations': citations,
            'success': True,
            'error': None
        }
    except Exception as e:
        return {
            'llm_name': 'Perplexity',
            'response': '',
            'citations': [],
            'success': False,
            'error': str(e)
        }

async def execute_google_ai(prompt: str) -> Dict[str, Any]:
    """Execute prompt using Google Gemini"""
    try:
        response = gemini_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        
        response_text = response.text or ""
        citations = extract_urls_from_text(response_text)
        
        return {
            'llm_name': 'Google AI',
            'response': response_text,
            'citations': citations,
            'success': True,
            'error': None
        }
    except Exception as e:
        return {
            'llm_name': 'Google AI',
            'response': '',
            'citations': [],
            'success': False,
            'error': str(e)
        }

def extract_urls_from_text(text: str) -> List[str]:
    """Extract URLs from text using regex"""
    import re
    url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
    urls = re.findall(url_pattern, text)
    return list(set(urls))

async def execute_prompt_on_llm(prompt: str, llm_name: str) -> Dict[str, Any]:
    """Execute a single prompt on a specific LLM"""
    if llm_name == "Claude":
        return await execute_claude(prompt)
    elif llm_name == "ChatGPT":
        return await execute_chatgpt(prompt)
    elif llm_name == "Perplexity":
        return await execute_perplexity(prompt)
    elif llm_name == "Google AI":
        return await execute_google_ai(prompt)
    elif llm_name == "Google AI Overview":
        # This should not be called in async context
        # Will be handled separately in sync function
        return {
            'llm_name': 'Google AI Overview',
            'response': 'Handled separately',
            'citations': [],
            'success': True,
            'error': None
        }
    else:
        return {
            'llm_name': llm_name,
            'response': '',
            'citations': [],
            'success': False,
            'error': f"Unknown LLM: {llm_name}"
        }

async def execute_prompts_multi_llm(prompts: List[str], llms: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """
    Execute multiple prompts across multiple LLMs concurrently
    
    Args:
        prompts: List of prompts to execute
        llms: Optional list of specific LLMs to use (if None, uses all available)
    
    Returns:
        List of results with structure:
        {
            'prompt': str,
            'prompt_index': int,
            'llm_name': str,
            'response': str,
            'citations': List[str],
            'success': bool,
            'error': Optional[str]
        }
    """
    if llms is None:
        llms = detect_available_llms()
    
    # Filter out Google AI Overview from async execution
    async_llms = [llm for llm in llms if llm != "Google AI Overview"]
    
    if not async_llms:
        return []
    
    # Create tasks for all prompt-LLM combinations
    tasks = []
    for prompt_index, prompt in enumerate(prompts):
        for llm_name in async_llms:
            tasks.append({
                'prompt': prompt,
                'prompt_index': prompt_index,
                'llm_name': llm_name
            })
    
    # Execute all tasks concurrently
    async_tasks = [
        execute_prompt_on_llm(task['prompt'], task['llm_name'])
        for task in tasks
    ]
    
    results = await asyncio.gather(*async_tasks, return_exceptions=True)
    
    # Combine results with prompt info
    final_results = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            final_results.append({
                'prompt': tasks[i]['prompt'],
                'prompt_index': tasks[i]['prompt_index'],
                'llm_name': tasks[i]['llm_name'],
                'response': '',
                'citations': [],
                'success': False,
                'error': str(result)
            })
        else:
            final_results.append({
                'prompt': tasks[i]['prompt'],
                'prompt_index': tasks[i]['prompt_index'],
                **result
            })
    
    return final_results

def execute_prompts_multi_llm_sync(prompts: List[str], llms: Optional[List[str]] = None, brand_name: str = None) -> List[Dict[str, Any]]:
    """
    Synchronous wrapper - FIXED VERSION with Google AI Overview support
    """
    print(f"\n🚀 Executing {len(prompts)} prompts with {llms}")
    
    all_responses = []
    
    # Check if Google AI Overview is in the list
    has_google_ai_overview = any(llm.lower() == "google ai overview" for llm in llms)
    
    # Handle Google AI Overview separately (Selenium-based)
    if has_google_ai_overview:
        print("\n📊 Processing Google AI Overview (Selenium scraping)...")
        try:
            driver = setup_driver()
            print("  ✅ Chrome driver initialized")
            
            for prompt_index, prompt in enumerate(prompts):
                try:
                    print(f"\n  [{prompt_index + 1}/{len(prompts)}] Scraping: {prompt[:60]}...")
                    
                    # Extract AI Overview data
                    extraction_result = extract_ai_overview_links(driver, prompt, max_links=10)
                    
                    # Format response similar to other LLMs
                    answer_text = extraction_result.get('answer_text', '')
                    links = extraction_result.get('links', [])
                    
                    # Build response text with citations
                    response_text = answer_text
                    if links:
                        response_text += "\n\nSources:\n"
                        for link in links[:5]:  # Top 5 citations
                            response_text += f"- {link['title']}: {link['url']}\n"
                    
                    all_responses.append({
                        "prompt_index": prompt_index,
                        "prompt": prompt,
                        "llm_name": "Google AI Overview",
                        "response": response_text or "[No AI Overview found]",
                        "citations": [link['url'] for link in links]
                    })
                    
                    print(f"  ✅ Google AI Overview extracted ({len(answer_text)} chars, {len(links)} links)")
                    
                    # Delay between requests
                    if prompt_index < len(prompts) - 1:
                        import time
                        import random
                        delay = random.uniform(3, 5)
                        print(f"  ⏳ Waiting {delay:.1f}s...")
                        time.sleep(delay)
                        
                except Exception as e:
                    print(f"  ❌ Error with Google AI Overview: {str(e)}")
                    all_responses.append({
                        "prompt_index": prompt_index,
                        "prompt": prompt,
                        "llm_name": "Google AI Overview",
                        "response": f"[Error] {str(e)}",
                        "error": True
                    })
            
            driver.quit()
            print("\n  ✔ Browser closed")
            
        except Exception as e:
            print(f"\n  ❌ Failed to initialize Google AI Overview: {str(e)}")
    
    # Handle other LLMs (Claude, Mistral)
    other_llms = [llm for llm in llms if llm.lower() not in ["google ai overview"]]
    
    for prompt_index, prompt in enumerate(prompts):
        for llm_name in other_llms:
            try:
                if llm_name.lower() == "claude":
                    # Execute Claude synchronously
                    response = anthropic_client.messages.create(
                        model="claude-sonnet-4-20250514",
                        max_tokens=1000,
                        messages=[{"role": "user", "content": prompt}]
                    )
                    response_text = response.content[0].text
                    
                    all_responses.append({
                        "prompt_index": prompt_index,
                        "prompt": prompt,
                        "llm_name": "Claude",
                        "response": response_text,
                    })
                    print(f"  ✅ Claude executed")
                    
                elif llm_name.lower() == "mistral":
                    # Execute Mistral synchronously
                    from mistralai.client import MistralClient
                    mistral_client = MistralClient(api_key=os.environ.get("MISTRAL_API_KEY"))
                    
                    message = mistral_client.chat(
                        model="mistral-small-latest",
                        messages=[{"role": "user", "content": prompt}],
                        max_tokens=1000
                    )
                    response_text = message.choices[0].message.content
                    
                    all_responses.append({
                        "prompt_index": prompt_index,
                        "prompt": prompt,
                        "llm_name": "Mistral",
                        "response": response_text,
                    })
                    print(f"  ✅ Mistral executed")
                    
                else:
                    print(f"  ⚠️ Unknown LLM: {llm_name}")
                    
            except Exception as e:
                print(f"  ❌ Error with {llm_name}: {str(e)}")
                all_responses.append({
                    "prompt_index": prompt_index,
                    "prompt": prompt,
                    "llm_name": llm_name,
                    "response": f"[Error] {str(e)}",
                    "error": True
                })
    
    print(f"\n✅ Done! {len(all_responses)} responses\n")
    return all_responses