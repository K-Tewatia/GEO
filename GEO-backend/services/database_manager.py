import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
import os
import logging
from urllib.parse import urlparse
from collections import Counter
logger = logging.getLogger(__name__)

DATABASE_PATH = "brand_visibility.db"

def init_database():
    """Initialize SQLite database with schema for brand visibility analysis"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Main analysis sessions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS analysis_sessions (
            session_id TEXT PRIMARY KEY,
            brand_name TEXT NOT NULL,
            product_name TEXT,
            industry TEXT,
            website_url TEXT,
            timestamp TEXT NOT NULL,
            research_data TEXT,
            keywords TEXT
        )
    ''')
    
    # LLM responses table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS llm_responses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prompt_id TEXT NOT NULL,
            session_id TEXT NOT NULL,
            llm_name TEXT NOT NULL,
            prompt_text TEXT NOT NULL,
            response_text TEXT NOT NULL,
            citations TEXT,
            timestamp TEXT NOT NULL,
            FOREIGN KEY (session_id) REFERENCES analysis_sessions(session_id)
        )
    ''')
    
    # Scoring results table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scoring_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prompt_id TEXT NOT NULL,
            session_id TEXT NOT NULL,
            llm_name TEXT NOT NULL,
            brand_mention_score REAL,
            position_score REAL,
            description_richness_score REAL,
            keyword_strength_score REAL,
            total_score REAL,
            normalized_visibility REAL,
            average_positioning REAL,
            weighted_score REAL,
            brand_position INTEGER,
            total_items INTEGER,
            timestamp TEXT NOT NULL,
            FOREIGN KEY (session_id) REFERENCES analysis_sessions(session_id)
        )
    ''')
    
    # Competitors table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS competitors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            competitor_name TEXT NOT NULL,
            rank INTEGER,
            FOREIGN KEY (session_id) REFERENCES analysis_sessions(session_id)
        )
    ''')
    
    # Share of Voice results table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS share_of_voice (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            brand_name TEXT NOT NULL,
            normalized_visibility REAL,
            average_positioning REAL,
            weighted_score REAL,
            rank INTEGER,
            timestamp TEXT NOT NULL,
            FOREIGN KEY (session_id) REFERENCES analysis_sessions(session_id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS saved_prompts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            brand_name TEXT NOT NULL,
            product_name TEXT,
            prompts_json TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            UNIQUE(brand_name, product_name)
        )
        ''')
    
    conn.commit()
    conn.close()

def create_session_id(brand_name: str, product_name: Optional[str] = None) -> str:
    """Create unique session ID from brand name, product name, and timestamp"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if product_name:
        return f"{brand_name.replace(' ', '_')}_{product_name.replace(' ', '_')}_{timestamp}"
    return f"{brand_name.replace(' ', '_')}_{timestamp}"

def create_prompt_id(session_id: str, prompt_index: int) -> str:
    """Create unique prompt ID"""
    return f"{session_id}_prompt_{prompt_index}"


def save_session(session_id: str, brand_name: str, product_name: Optional[str] = None, 
                 website_url: Optional[str] = None, research_data: Optional[Dict] = None,
                 keywords: Optional[List[str]] = None, industry: Optional[str] = None):
    """Save analysis session metadata"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    timestamp = datetime.now().isoformat()
    research_json = json.dumps(research_data) if research_data else None
    keywords_json = json.dumps(keywords) if keywords else None
    
    # ✅ FIXED: Added industry to VALUES - now 8 columns = 8 values
    cursor.execute('''
        INSERT INTO analysis_sessions 
        (session_id, brand_name, product_name, industry, website_url, timestamp, research_data, keywords)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (session_id, brand_name, product_name, industry, website_url, timestamp, research_json, keywords_json))
    
    conn.commit()
    conn.close()

def save_llm_response(prompt_id: str, session_id: str, llm_name: str, 
                     prompt_text: str, response_text: str, citations: Optional[List[str]] = None):
    """Save LLM response with citations"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    timestamp = datetime.now().isoformat()
    citations_json = json.dumps(citations) if citations else None
    
    cursor.execute('''
        INSERT INTO llm_responses 
        (prompt_id, session_id, llm_name, prompt_text, response_text, citations, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (prompt_id, session_id, llm_name, prompt_text, response_text, citations_json, timestamp))
    
    conn.commit()
    conn.close()

def save_scoring_result(prompt_id: str, session_id: str, llm_name: str, scores: Dict[str, Any]):
    """Save scoring results for a prompt-LLM combination"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    timestamp = datetime.now().isoformat()
    
    cursor.execute('''
        INSERT INTO scoring_results 
        (prompt_id, session_id, llm_name, brand_mention_score, position_score, 
         description_richness_score, keyword_strength_score, total_score,
         normalized_visibility, average_positioning, weighted_score,
         brand_position, total_items, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        prompt_id, session_id, llm_name,
        scores.get('brand_mention_score', 0),
        scores.get('position_score', 0),
        scores.get('description_richness_score', 0),
        scores.get('keyword_strength_score', 0),
        scores.get('total_score', 0),
        scores.get('normalized_visibility', 0),
        scores.get('average_positioning', 0),
        scores.get('weighted_score', 0),
        scores.get('brand_position', 0),
        scores.get('total_items', 0),
        timestamp
    ))
    
    conn.commit()
    conn.close()

def save_competitors(session_id: str, competitors: list):
    """Save competitor names for a session"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    try:
        for rank, competitor in enumerate(competitors, 1):
            cursor.execute('''
                INSERT INTO competitors (session_id, competitor_name, rank)
                VALUES (?, ?, ?)
            ''', (session_id, competitor, rank))
        conn.commit()
        logger.info(f"✓ Saved {len(competitors)} competitors for session {session_id}")
    except Exception as e:
        logger.error(f"Error saving competitors: {str(e)}")
    finally:
        conn.close()


def save_share_of_voice(session_id: str, brand_name: str, sov_scores: Dict[str, Any], rank: int):
    """Save Share of Voice results"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    timestamp = datetime.now().isoformat()
    
    cursor.execute('''
        INSERT INTO share_of_voice 
        (session_id, brand_name, normalized_visibility, average_positioning, weighted_score, rank, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        session_id, brand_name,
        sov_scores.get('normalized_visibility', 0),
        sov_scores.get('average_positioning', 0),
        sov_scores.get('weighted_score', 0),
        rank, timestamp
    ))
    
    conn.commit()
    conn.close()
def save_brand_score_summary(session_id: str, brand_name: str, summary: Dict[str, Any]):
    """Save aggregated brand score summary for a session"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    timestamp = datetime.now().isoformat()
    
    try:
        # Save as JSON in a summary column or insert individual metrics
        # Option A: Store in existing scoring_results with special prompt_id
        summary_prompt_id = f"{session_id}_summary"
        
        cursor.execute('''
            INSERT INTO scoring_results
            (prompt_id, session_id, llm_name, brand_mention_score, position_score,
             description_richness_score, keyword_strength_score, total_score,
             normalized_visibility, average_positioning, weighted_score,
             brand_position, total_items, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            summary_prompt_id,
            session_id,
            'SUMMARY',  # Special marker for aggregated data
            summary.get('total_mentions', 0),
            summary.get('avg_position', 0),
            0,  # Not used in summary
            0,  # Not used in summary
            summary.get('avg_visibility_score', 0),
            summary.get('avg_visibility_score', 0),
            summary.get('avg_position', 0),
            summary.get('avg_visibility_score', 0),
            0,
            summary.get('total_prompts', 0),
            timestamp
        ))
        
        conn.commit()
        logger.info(f"✓ Saved brand score summary for session {session_id}")
    except Exception as e:
        logger.error(f"Error saving brand score summary: {str(e)}")
    finally:
        conn.close()

def get_session_results(session_id: str) -> Dict[str, Any]:
    """Retrieve all results for a session"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Get session metadata
    cursor.execute('SELECT * FROM analysis_sessions WHERE session_id = ?', (session_id,))
    session = cursor.fetchone()
    
    # Get LLM responses
    cursor.execute('SELECT * FROM llm_responses WHERE session_id = ?', (session_id,))
    responses = cursor.fetchall()
    
    # Get scoring results
    cursor.execute('SELECT * FROM scoring_results WHERE session_id = ?', (session_id,))
    scores = cursor.fetchall()
    
    # Get competitors
    cursor.execute('SELECT * FROM competitors WHERE session_id = ? ORDER BY rank', (session_id,))
    competitors = cursor.fetchall()
    
    # Get Share of Voice
    cursor.execute('SELECT * FROM share_of_voice WHERE session_id = ? ORDER BY rank', (session_id,))
    sov = cursor.fetchall()
    
    conn.close()
    
    return {
        'session': session,
        'responses': responses,
        'scores': scores,
        'competitors': competitors,
        'share_of_voice': sov
    }

def get_all_sessions() -> List[Dict[str, Any]]:
    """Get list of all analysis sessions"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT session_id, brand_name, product_name, timestamp 
        FROM analysis_sessions 
        ORDER BY timestamp DESC
    ''')
    sessions = cursor.fetchall()
    
    conn.close()
    
    return [
        {
            'session_id': s[0],
            'brand_name': s[1],
            'product_name': s[2],
            'timestamp': s[3]
        }
        for s in sessions
    ]

def get_brand_visibility_history(brand_name: str) -> List[Dict[str, Any]]:
    """
    ✅ FIXED: Returns visibility data grouped by date with proper aggregation
    """
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT 
                s.session_id,
                s.brand_name,
                s.timestamp,
                SUBSTR(s.timestamp, 1, 10) as date,
                AVG(sr.normalized_visibility) as avg_visibility
            FROM analysis_sessions s
            LEFT JOIN scoring_results sr ON s.session_id = sr.session_id
            WHERE s.brand_name = ?
            GROUP BY s.session_id, s.timestamp
            ORDER BY s.timestamp ASC
        ''', (brand_name,))
        
        sessions = cursor.fetchall()
        
        if not sessions:
            logger.warning(f"No sessions found for brand: {brand_name}")
            return []
        
        result = []
        for session in sessions:
            session_dict = dict(session)
            result.append({
                'date': session_dict['date'],
                'timestamp': session_dict['timestamp'],
                'visibility': round(float(session_dict['avg_visibility'] or 0), 2),
                'session_id': session_dict['session_id'],
                'brand_name': brand_name
            })
        
        logger.info(f"✓ Retrieved {len(result)} historical sessions for brand: {brand_name}")
        return result
        
    except Exception as e:
        logger.error(f"❌ Error getting brand visibility history for {brand_name}: {str(e)}")
        return []
    finally:
        conn.close()


def get_llm_aggregate_scores(session_id: str, llm_name: str) -> Dict[str, float]:
    """Get aggregate scores for a specific LLM in a session"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT 
            AVG(normalized_visibility) as avg_visibility,
            AVG(average_positioning) as avg_positioning,
            AVG(weighted_score) as avg_weighted_score,
            COUNT(*) as total_prompts
        FROM scoring_results 
        WHERE session_id = ? AND llm_name = ?
    ''', (session_id, llm_name))
    
    result = cursor.fetchone()
    conn.close()
    
    return {
        'avg_visibility': result[0] or 0,
        'avg_positioning': result[1] or 0,
        'avg_weighted_score': result[2] or 0,
        'total_prompts': result[3] or 0
    }

def get_saved_prompts(brand_name: str, product_name: Optional[str] = None) -> Optional[List[str]]:
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
        SELECT prompts_json FROM saved_prompts 
        WHERE brand_name = ? AND product_name IS ?
        ''', (brand_name, product_name))
        
        result = cursor.fetchone()
        if result:
            prompts = json.loads(result[0])
            return prompts
        return None
    except Exception as e:
        logger.error(f"Error retrieving saved prompts: {str(e)}")
        return None
    finally:
        conn.close()


def save_prompts_to_db(brand_name: str, prompts: List[str], product_name: Optional[str] = None):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        timestamp = datetime.now().isoformat()
        prompts_json = json.dumps(prompts)
        
        cursor.execute('''
        INSERT OR REPLACE INTO saved_prompts 
        (brand_name, product_name, prompts_json, timestamp)
        VALUES (?, ?, ?, ?)
        ''', (brand_name, product_name, prompts_json, timestamp))
        
        conn.commit()
    except Exception as e:
        logger.error(f"Error saving prompts: {str(e)}")
    finally:
        conn.close()

# Initialize database on module import
init_database()

def get_session_results_aggregated(session_id: str):
    """Get aggregated results for a specific session"""
    import sqlite3
    import json
    from urllib.parse import urlparse
    from collections import Counter
    
    conn = sqlite3.connect("brand_visibility.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        logger.info(f"🔍 Fetching aggregated results for session: {session_id}")
        cursor.execute("SELECT * FROM analysis_sessions WHERE session_id = ?", (session_id,))
        session_row = cursor.fetchone()
        
        if not session_row: 
            return None
        
        session_dict = dict(session_row)
        brand_name = session_dict.get('brand_name', 'Unknown')

        cursor.execute("SELECT * FROM llm_responses WHERE session_id = ? ORDER BY id", (session_id,))
        llm_rows = cursor.fetchall()
        
        cursor.execute("SELECT * FROM scoring_results WHERE session_id = ?", (session_id,))
        scoring_rows = cursor.fetchall()
        scoring_results = [dict(r) for r in scoring_rows]
        
        llm_responses = []
        all_citations = []

        for row in llm_rows:
            r = dict(row)
            response_text = r.get('response_text', '')
            prompt_text = r.get('prompt_text', '').strip() or 'Source Unknown'
            llm_name = r.get('llm_name', 'Unknown')
            prompt_id = r.get('prompt_id')

            try: 
                citations = json.loads(r.get('citations', '[]') or '[]')
            except: 
                citations = []

            visibility_score = 0
            matching_score = next(
                (s for s in scoring_results if s.get('prompt_id') == prompt_id and s.get('llm_name') == llm_name),
                None
            )
            if matching_score:
                visibility_score = float(matching_score.get('normalized_visibility', 0))

            llm_responses.append({
                'prompt': prompt_text,
                'response': response_text,
                'llm_name': llm_name,
                'citations': citations,
                'visibility_score': visibility_score
            })
            all_citations.extend(citations)

        # Domain citations
        domain_citations = []
        if all_citations:
            domains = []
            for citation_url in all_citations:
                try:
                    parsed = urlparse(citation_url)
                    domain = parsed.netloc or parsed.path
                    if domain:
                        domains.append(domain.replace('www.', ''))
                except: 
                    continue
            
            if domains:
                domain_counts = Counter(domains)
                total_citations = len(domains)
                domain_citations = [
                    {'domain': d, 'citations': c, 'percentage': round((c/total_citations*100), 1)}
                    for d, c in domain_counts.most_common(10)
                ]
        
        # ✅ UPDATED: Check for saved summary first, fallback to calculation
        cursor.execute("""
            SELECT * FROM scoring_results 
            WHERE session_id = ? AND llm_name = 'SUMMARY'
            LIMIT 1
        """, (session_id,))
        summary_row = cursor.fetchone()

        if summary_row:
            # Use saved summary
            summary_dict = dict(summary_row)
            avg_visibility = float(summary_dict.get('normalized_visibility', 0))
            avg_position = float(summary_dict.get('average_positioning', 0))
            avg_mentions = float(summary_dict.get('brand_mention_score', 0))
            logger.info(f"✓ Using saved summary metrics for session {session_id}")
        else:
            # Fallback to calculation from individual scores
            total_visibility = sum(float(r.get('normalized_visibility', 0)) for r in scoring_results)
            total_position = sum(float(r.get('average_positioning', 0)) for r in scoring_results)
            total_mentions = sum(float(r.get('brand_mention_score', 0)) for r in scoring_results)
            score_count = len(scoring_results)
            
            avg_visibility = (total_visibility / score_count) if score_count > 0 else 0
            avg_position = (total_position / score_count) if score_count > 0 else 0
            avg_mentions = (total_mentions / score_count) if score_count > 0 else 0
            logger.info(f"✓ Calculated summary metrics from individual scores for session {session_id}")
        
        # Share of Voice
        cursor.execute("SELECT * FROM share_of_voice WHERE session_id = ? ORDER BY rank", (session_id,))
        sov_rows = cursor.fetchall()
        
        brand_scores = []
        share_of_voice = []
        
        if sov_rows:
            for idx, row in enumerate(sov_rows, 1):
                r = dict(row)
                brand = r.get('brand_name', f'Brand {idx}')
                visibility = float(r.get('normalized_visibility', 0))
                brand_scores.append({
                    'brand': brand, 
                    'mention_count': int(avg_mentions) if brand == brand_name else idx, 
                    'average_position': float(r.get('average_positioning', 0)),
                    'visibility_score': visibility, 
                    'mention_rate': visibility / 100, 
                    'rank': idx
                })
                share_of_voice.append({
                    'brand': brand, 
                    'percentage': min(100, visibility), 
                    'mention_count': int(avg_mentions) if brand == brand_name else idx
                })
        else:
            # Fallback logic
            brand_data = {}
            for r in scoring_results:
                if brand_name not in brand_data: 
                    brand_data[brand_name] = []
                brand_data[brand_name].append(float(r.get('normalized_visibility', 0)))
            
            for brand, vis_list in brand_data.items():
                avg_vis = sum(vis_list)/len(vis_list) if vis_list else 0
                brand_scores.append({
                    'brand': brand, 
                    'mention_count': int(avg_mentions), 
                    'average_position': avg_position,
                    'visibility_score': avg_vis, 
                    'mention_rate': avg_vis/100, 
                    'rank': 1
                })
                share_of_voice.append({
                    'brand': brand, 
                    'percentage': avg_vis, 
                    'mention_count': int(avg_mentions)
                })

        # Competitors
        cursor.execute("SELECT DISTINCT competitor_name FROM competitors WHERE session_id = ? ORDER BY rank", (session_id,))
        competitors = [dict(r)['competitor_name'] for r in cursor.fetchall()]
        
        return {
            'session_id': session_id,
            'brand_name': brand_name,
            'num_prompts': len(llm_responses),
            'brand_scores': brand_scores,
            'share_of_voice': share_of_voice,
            'llm_responses': llm_responses,
            'domain_citations': domain_citations,
            'competitors': competitors,
            'created_at': session_dict.get('timestamp', ''),
            'average_visibility_score': avg_visibility,
            'average_position': avg_position,
            'average_mentions': avg_mentions
        }
    except Exception as e:
        logger.error(f"Error getting aggregated results: {e}", exc_info=True)
        return None
    finally:
        conn.close()


def get_all_unique_brands():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT DISTINCT brand_name FROM analysis_sessions ORDER BY brand_name ASC")
        return [dict(row)['brand_name'] for row in cursor.fetchall()]
    finally:
        conn.close()

def get_recent_sessions_by_brand(brand_name: str, limit: int = 20):
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT session_id, brand_name, product_name, website_url, timestamp
            FROM analysis_sessions WHERE brand_name = ? ORDER BY timestamp DESC LIMIT ?
        """, (brand_name, limit))
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()

def get_saved_prompts_for_analysis(session_id: str):
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT DISTINCT prompt_text FROM llm_responses
            WHERE session_id = ? ORDER BY timestamp ASC
        """, (session_id,))
        return [dict(row)['prompt_text'] for row in cursor.fetchall()]
    finally:
        conn.close()

def get_visibility_history_for_same_prompts(brand_name: str, product_name: str, prompts: list):
    """
    Get visibility history for the same set of prompts over time.
    FIXED: Groups by SESSION instead of DATE to show each re-analysis separately.
    """
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        if not prompts:
            logger.warning("No prompts provided for same prompts history")
            return []
        
        if not brand_name:
            logger.warning("No brand_name provided for same prompts history")
            return []
        
        placeholders = ','.join(['?' for _ in prompts])
        
        # Query to get all sessions with matching brand and prompts
        # Group by session and timestamp to get each re-analysis separately
        query = f"""
            SELECT 
                s.session_id,
                s.timestamp,
                AVG(sr.normalized_visibility) AS avg_visibility
            FROM scoring_results sr
            JOIN analysis_sessions s ON sr.session_id = s.session_id
            JOIN llm_responses lr ON lr.prompt_id = sr.prompt_id AND lr.session_id = sr.session_id
            WHERE s.brand_name = ?
              AND lr.prompt_text IN ({placeholders})
              AND sr.llm_name != 'SUMMARY'
            GROUP BY s.session_id, s.timestamp
            ORDER BY s.timestamp ASC
        """
        
        params = [brand_name] + prompts
        cursor.execute(query, params)
        
        results = [dict(row) for row in cursor.fetchall()]
        
        if not results:
            logger.info(f"No historical data found for same prompts (brand: {brand_name}, prompts: {len(prompts)})")
            return []
        
        # Format each session as a separate data point with datetime info
        chart_data = []
        for row in results:
            timestamp = row['timestamp']
            if 'T' in timestamp:
                date_display = timestamp.split('T')[0]
                time_display = timestamp.split('T')[1][:5]  # HH:MM
            else:
                date_display = timestamp.split(' ')[0]
                time_display = timestamp.split(' ')[1][:5] if ' ' in timestamp else '00:00'
            
            chart_data.append({
                'date': f"{date_display} {time_display}",  # e.g. "2024-11-20 09:30"
                'visibility': round(row['avg_visibility'] or 0, 2),
                'timestamp': timestamp,
                'session_id': row['session_id']
            })
        
        logger.info(f"✓ Found {len(chart_data)} session points for same prompts history (brand: {brand_name})")
        return chart_data
        
    except Exception as e:
        logger.error(f"Error in get_visibility_history_for_same_prompts: {str(e)}", exc_info=True)
        return []
    finally:
        conn.close()

def get_product_specific_visibility_history(brand_name: str, product_name: str):
    """
    ✅ FIXED: Returns visibility history for brand+product combinations across all analyses
    """
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT 
                AVG(sr.normalized_visibility) as avg_visibility,
                s.timestamp,
                s.session_id,
                SUBSTR(s.timestamp, 1, 10) as date
            FROM scoring_results sr
            JOIN analysis_sessions s ON sr.session_id = s.session_id
            WHERE s.brand_name = ?
                AND s.product_name = ?
            GROUP BY s.session_id, s.timestamp
            ORDER BY s.timestamp ASC
        """, (brand_name, product_name))
        
        results = [dict(row) for row in cursor.fetchall()]
        
        # Group by date in case multiple analyses on same date
        history = {}
        for row in results:
            date = row['date']
            if date not in history:
                history[date] = []
            history[date].append(row['avg_visibility'])
        
        chart_data = [
            {
                'date': date,
                'visibility': round(sum(scores) / len(scores), 2),
                'timestamp': date
            }
            for date, scores in sorted(history.items())
        ]
        
        return chart_data
        
    finally:
        conn.close()


def get_recent_sessions(limit=10):
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    try:
        cursor.execute('''
            SELECT session_id, brand_name, timestamp, product_name, website_url
            FROM analysis_sessions
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (limit,))
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()