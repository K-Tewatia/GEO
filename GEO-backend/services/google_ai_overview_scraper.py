import time
import random
import re
import csv
from datetime import datetime
from typing import List, Dict, Any
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()


def setup_driver():
    """Setup Chrome driver with stealth settings"""
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
    ]
    
    opts = webdriver.ChromeOptions()
    opts.add_argument(f'--user-agent={random.choice(user_agents)}')
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_argument("--start-maximized")
    opts.add_argument("--disable-notifications")
    opts.add_argument("--disable-popup-blocking")
    # Add headless mode if you want it to run in background
    # opts.add_argument("--headless=new")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option('useAutomationExtension', False)
    
    # Try to use system chromedriver or specify path
    try:
        driver = webdriver.Chrome(options=opts)
    except:
        # If system chromedriver not found, try common paths
        try:
            service = Service(executable_path="chromedriver.exe")
            driver = webdriver.Chrome(service=service, options=opts)
        except:
            service = Service(executable_path="drivers/chromedriver.exe")
            driver = webdriver.Chrome(service=service, options=opts)
    
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver


def wait_for_ai_overview(driver, timeout=10):
    """Wait for AI Overview section to appear and load"""
    try:
        # Wait for potential AI Overview indicators
        wait = WebDriverWait(driver, timeout)
        
        # Try multiple strategies to detect AI Overview loading
        ai_overview_selectors = [
            "div[data-attrid*='GenerativeAnswer']",
            "div[data-hveid] div:contains('AI Overview')",
            "div[jsname]",  # Generic container that might hold AI Overview
        ]
        
        # Wait a bit for dynamic content to load
        time.sleep(3)
        
        # Scroll to trigger lazy loading
        driver.execute_script("window.scrollTo(0, 500);")
        time.sleep(2)
        
        # Scroll more to ensure full content loads
        driver.execute_script("window.scrollTo(0, 800);")
        time.sleep(2)
        
        return True
        
    except Exception as e:
        print(f"    ⏱️ Timeout waiting for AI Overview: {str(e)}")
        return False


def click_show_more_button(driver):
    """Try to click 'Show more' button to expand AI Overview"""
    try:
        # Common patterns for "Show more" button
        show_more_patterns = [
            "//span[contains(text(), 'Show more')]",
            "//button[contains(text(), 'Show more')]",
            "//div[contains(text(), 'Show more')]",
            "//span[contains(text(), 'show more')]",
            "//*[contains(@aria-label, 'Show more')]",
            "//span[contains(@class, 'show-more')]"
        ]
        
        for pattern in show_more_patterns:
            try:
                show_more_btn = driver.find_element(By.XPATH, pattern)
                if show_more_btn.is_displayed():
                    driver.execute_script("arguments[0].scrollIntoView(true);", show_more_btn)
                    time.sleep(1)
                    driver.execute_script("arguments[0].click();", show_more_btn)
                    print("    ✅ Clicked 'Show more' button")
                    time.sleep(3)  # Wait after expanding
                    return True
            except:
                continue
        
        print("    ℹ️ No 'Show more' button found")
        return False
    except Exception as e:
        print(f"    ⚠️ Error clicking 'Show more': {str(e)}")
        return False


def extract_ai_overview_text(ai_section) -> str:
    """
    Extract the AI Overview answer text from the section
    
    Args:
        ai_section: BeautifulSoup element containing AI Overview
    
    Returns:
        str: Extracted AI Overview text
    """
    try:
        # Get all text from the AI section
        text_content = ai_section.get_text(separator=' ', strip=True)
        
        # Remove common UI elements that aren't part of the answer
        patterns_to_remove = [
            r'AI Overview',
            r'Learn more',
            r'Show more',
            r'Feedback',
            r'Sources',
            r'Citations',
            r'View all',
            r'See more'
        ]
        
        for pattern in patterns_to_remove:
            text_content = re.sub(pattern, '', text_content, flags=re.IGNORECASE)
        
        # Clean up extra whitespace
        text_content = re.sub(r'\s+', ' ', text_content).strip()
        
        # Limit length to avoid overly long responses
        if len(text_content) > 4000:
            text_content = text_content[:4000] + "..."
        
        return text_content
    
    except Exception as e:
        print(f"    ⚠️ Error extracting AI Overview text: {str(e)}")
        return ""


def extract_ai_overview_links(driver, query: str, max_links: int = 10) -> Dict[str, Any]:
    """
    Search Google and extract citation links AND answer text from AI Overview
    
    Args:
        driver: Selenium WebDriver instance
        query: Search query string
        max_links: Maximum number of links to extract
    
    Returns:
        dict: Contains 'answer_text', 'links' list, and metadata
    """
    result = {
        'answer_text': '',
        'links': [],
        'has_ai_overview': False
    }
    
    try:
        print(f"  🔍 Searching: {query[:60]}...")
        
        # Navigate to Google
        driver.get("https://www.google.com")
        time.sleep(random.uniform(2, 3))
        
        # Handle cookie consent if present
        try:
            reject_button = driver.find_element(By.XPATH, "//*[contains(text(), 'Reject all')]")
            reject_button.click()
            time.sleep(1)
        except:
            try:
                accept_button = driver.find_element(By.XPATH, "//*[contains(text(), 'Accept all')]")
                accept_button.click()
                time.sleep(1)
            except:
                pass
        
        # Enter search query
        try:
            search_box = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, "q"))
            )
            search_box.clear()
            search_box.send_keys(query)
            search_box.send_keys(Keys.RETURN)
            time.sleep(random.uniform(4, 6))  # Increased wait time
        except Exception as e:
            print(f"    ❌ Error entering query: {str(e)}")
            return result
        
        # Wait for AI Overview to load (IMPORTANT!)
        print("    ⏳ Waiting for AI Overview to load...")
        wait_for_ai_overview(driver, timeout=10)
        
        # Try to click "Show more" button
        click_show_more_button(driver)
        
        # Additional scroll and wait after expanding
        driver.execute_script("window.scrollTo(0, 1000);")
        time.sleep(2)
        
        # Parse page
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Find AI Overview section - try multiple strategies
        ai_section = None
        
        # Strategy 1: Look for "AI Overview" text (most reliable)
        ai_heading = soup.find(string=lambda text: text and 'AI Overview' in text if text else False)
        if ai_heading:
            # Try to find parent container
            parent = ai_heading.find_parent('div', {'data-hveid': True})
            if not parent:
                parent = ai_heading.find_parent('div', {'data-attrid': True})
            if not parent:
                # Go up multiple levels
                parent = ai_heading.find_parent('div')
                for _ in range(5):  # Try up to 5 levels up
                    if parent and len(parent.get_text(strip=True)) > 200:
                        break
                    parent = parent.find_parent('div') if parent else None
            
            ai_section = parent
            if ai_section:
                print("    ✅ Found AI Overview (by heading)")
        
        # Strategy 2: Look for divs with substantial content and citations
        if not ai_section:
            hveid_divs = soup.find_all('div', {'data-hveid': True})
            for div in hveid_divs:
                text_content = div.get_text(strip=True)
                links_in_div = div.find_all('a', {'target': '_blank', 'rel': 'noopener'})
                
                # AI Overview typically has substantial text (>200 chars) and multiple citation links (>=2)
                if len(text_content) > 200 and len(links_in_div) >= 2:
                    ai_section = div
                    print("    ✅ Found AI Overview (by content)")
                    break
        
        # Strategy 3: Look for generative AI specific attributes
        if not ai_section:
            ai_section = soup.find('div', {'data-attrid': lambda x: x and 'GenerativeAnswer' in x if x else False})
            if ai_section:
                print("    ✅ Found AI Overview (by attribute)")
        
        # Strategy 4: Look for specific class patterns (Google sometimes uses these)
        if not ai_section:
            possible_sections = soup.find_all('div', class_=re.compile(r'.*gen.*|.*overview.*', re.I))
            for section in possible_sections:
                text_content = section.get_text(strip=True)
                if len(text_content) > 200:
                    ai_section = section
                    print("    ✅ Found AI Overview (by class pattern)")
                    break
        
        if not ai_section:
            print("    ❌ AI Overview not found on page")
            print("    💡 Possible reasons: No AI Overview for this query, region restrictions, or page structure changed")
            return result
        
        result['has_ai_overview'] = True
        
        # Extract AI Overview answer text
        answer_text = extract_ai_overview_text(ai_section)
        result['answer_text'] = answer_text
        
        if answer_text:
            print(f"    📝 Extracted answer text ({len(answer_text)} characters)")
        else:
            print("    ⚠️ No answer text extracted")
        
        # Extract citation links (target="_blank", rel="noopener")
        citation_links = ai_section.find_all('a', {
            'target': '_blank',
            'rel': 'noopener',
            'href': True
        })
        
        # Also try alternative link patterns
        if not citation_links:
            citation_links = ai_section.find_all('a', href=True)
        
        print(f"    🔎 Found {len(citation_links)} potential citation links")
        
        seen_urls = set()
        
        for link in citation_links:
            if len(result['links']) >= max_links:
                break
            
            href = link.get('href', '')
            
            # Remove text fragment for deduplication
            clean_url = re.sub(r'#:~:text=.*$', '', href)
            
            # Filter: external links only (not Google properties)
            if (href.startswith('http') and 
                'google.com' not in href and
                'youtube.com' not in href and
                '/search?' not in href and
                clean_url not in seen_urls):
                
                seen_urls.add(clean_url)
                
                # Get title
                title = link.get_text(strip=True)
                if not title or len(title) < 3:
                    aria_label = link.get('aria-label', '')
                    if aria_label:
                        title = aria_label
                    else:
                        domain_match = re.search(r'https?://(?:www\.)?([^/]+)', href)
                        title = domain_match.group(1) if domain_match else 'Source'
                
                result['links'].append({
                    'position': len(result['links']) + 1,
                    'title': title[:150],
                    'url': href
                })
        
        if result['links']:
            print(f"    ✅ Extracted {len(result['links'])} citation URLs")
        else:
            print("    ⚠️ No citation links extracted from AI Overview")
        
    except Exception as e:
        print(f"    ❌ Error during extraction: {str(e)}")
        import traceback
        traceback.print_exc()
    
    return result


def scrape_google_ai_overview(prompts: List[str], brand_name: str, max_links_per_prompt: int = 10) -> Dict[str, Any]:
    """
    Scrape Google AI Overview for multiple prompts
    
    Args:
        prompts: List of search prompts
        brand_name: Brand name for file naming
        max_links_per_prompt: Maximum links to extract per prompt
    
    Returns:
        Dictionary with results and CSV filename
    """
    print("\n" + "="*80)
    print("🎯 GOOGLE AI OVERVIEW SCRAPING")
    print("="*80 + "\n")
    
    driver = None
    all_results = []
    
    try:
        # Setup driver
        print("🚀 Initializing Chrome driver...")
        driver = setup_driver()
        print("✅ Driver ready\n")
        
        # Process each prompt
        for idx, prompt in enumerate(prompts, 1):
            print(f"[{idx}/{len(prompts)}] Processing prompt:")
            
            # Extract links AND answer text
            extraction_result = extract_ai_overview_links(driver, prompt, max_links_per_prompt)
            
            # Store results
            prompt_result = {
                'prompt_index': idx,
                'prompt': prompt,
                'has_ai_overview': extraction_result['has_ai_overview'],
                'answer_text': extraction_result['answer_text'],
                'num_links': len(extraction_result['links']),
                'links': extraction_result['links']
            }
            all_results.append(prompt_result)
            
            # Random delay between queries to avoid detection
            if idx < len(prompts):
                delay = random.uniform(5, 8)  # Increased delay
                print(f"    ⏳ Waiting {delay:.1f}s before next query...\n")
                time.sleep(delay)
        
    except Exception as e:
        print(f"\n❌ Error during scraping: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        if driver:
            driver.quit()
            print("\n✔ Browser closed")
    
    # Generate CSV
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_filename = f"{brand_name.replace(' ', '_')}_google_ai_overview_{timestamp}.csv"
    
    print(f"\n💾 Saving results to CSV: {csv_filename}")
    save_results_to_csv(all_results, csv_filename)
    
    # Summary
    prompts_with_ai = sum(1 for r in all_results if r['has_ai_overview'])
    total_links = sum(r['num_links'] for r in all_results)
    
    print(f"\n{'='*80}")
    print(f"📊 SCRAPING COMPLETE")
    print(f"{'='*80}")
    print(f"Total Prompts: {len(prompts)}")
    print(f"Prompts with AI Overview: {prompts_with_ai}")
    print(f"Total Links Extracted: {total_links}")
    print(f"Average Links per Prompt: {total_links/len(prompts):.1f}")
    print(f"CSV File: {csv_filename}")
    print(f"{'='*80}\n")
    
    return {
        'results': all_results,
        'csv_filename': csv_filename,
        'total_prompts': len(prompts),
        'prompts_with_ai_overview': prompts_with_ai,
        'total_links': total_links
    }


def save_results_to_csv(results: List[Dict[str, Any]], filename: str):
    """Save scraping results to CSV file with answer text"""
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write header
            writer.writerow([
                'Prompt Index', 
                'Prompt', 
                'Has AI Overview',
                'AI Overview Answer',
                'Link Position', 
                'Link Title', 
                'URL'
            ])
            
            # Write data
            for result in results:
                prompt_idx = result['prompt_index']
                prompt = result['prompt']
                has_ai = 'Yes' if result['has_ai_overview'] else 'No'
                answer = result['answer_text']
                
                if result['links']:
                    for link in result['links']:
                        writer.writerow([
                            prompt_idx,
                            prompt,
                            has_ai,
                            answer,
                            link['position'],
                            link['title'],
                            link['url']
                        ])
                else:
                    # Write row even if no links found
                    writer.writerow([
                        prompt_idx, 
                        prompt, 
                        has_ai,
                        answer if answer else 'No AI Overview found',
                        'N/A', 
                        'No links found', 
                        'N/A'
                    ])
        
        print(f"    ✅ CSV file saved successfully")
    
    except Exception as e:
        print(f"    ❌ Error saving CSV: {str(e)}")


def analyze_ai_overview_results(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze the scraped results to generate insights"""
    total_prompts = len(results)
    prompts_with_ai = sum(1 for r in results if r['has_ai_overview'])
    prompts_with_links = sum(1 for r in results if r['num_links'] > 0)
    total_links = sum(r['num_links'] for r in results)
    
    # Calculate average answer length
    answer_lengths = [len(r['answer_text']) for r in results if r['answer_text']]
    avg_answer_length = sum(answer_lengths) / len(answer_lengths) if answer_lengths else 0
    
    # Get unique domains
    all_domains = []
    for result in results:
        for link in result['links']:
            domain_match = re.search(r'https?://(?:www\.)?([^/]+)', link['url'])
            if domain_match:
                all_domains.append(domain_match.group(1))
    
    from collections import Counter
    domain_counts = Counter(all_domains)
    top_domains = domain_counts.most_common(10)
    
    analysis = {
        'total_prompts': total_prompts,
        'prompts_with_ai_overview': prompts_with_ai,
        'prompts_with_links': prompts_with_links,
        'ai_overview_rate': (prompts_with_ai / total_prompts * 100) if total_prompts > 0 else 0,
        'total_citations': total_links,
        'avg_citations_per_prompt': total_links / total_prompts if total_prompts > 0 else 0,
        'avg_answer_length': round(avg_answer_length, 0),
        'top_cited_domains': top_domains,
        'unique_domains': len(set(all_domains))
    }
    
    return analysis