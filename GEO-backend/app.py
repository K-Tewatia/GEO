from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import logging
import json
from dotenv import load_dotenv
import os
import sqlite3
import services.database_manager
# Import your existing modules
from services.deep_research import conduct_deep_research
from services.prompt_generator import generate_prompts
from services.keyword_extractor import extract_keywords
from services.multi_llm_executor import execute_prompts_multi_llm_sync
from services.scoring_engine import calculate_scores, aggregate_results
from services.share_of_voice import calculate_share_of_voice
from services.database_manager import (
    create_session_id, save_session, save_llm_response, 
    save_scoring_result, save_competitors, save_share_of_voice,
    get_session_results, get_all_sessions, init_database, create_prompt_id, get_recent_sessions,
    get_saved_prompts, save_prompts_to_db, save_brand_score_summary  
)
from services.database_manager import (
    get_all_unique_brands,
    get_recent_sessions_by_brand,
    get_saved_prompts_for_analysis,
    get_visibility_history_for_same_prompts,
    get_product_specific_visibility_history
)

# Setup
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize database
init_database()

# FastAPI app
app = FastAPI(
    title="Brand Visibility Analyzer API",
    description="Backend API for brand visibility analysis",
    version="1.0.0"
)

# ============= CORS MIDDLEWARE =============
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store analysis progress
analysis_progress = {}

# ============= REQUEST MODELS =============

class AnalysisRequest(BaseModel):
    brand_name: str
    product_name: Optional[str] = None
    website_url: Optional[str] = None
    num_prompts: int = 10
    selected_llms: List[str]
    regenerate_prompts: bool = False

# ============= API ENDPOINTS =============

@app.get("/health")
def health_check():
    """Check if API is running"""
    return {
        "status": "healthy",
        "message": "API is running!"
    }

@app.post("/api/analysis/run")
async def run_analysis(request: AnalysisRequest, background_tasks: BackgroundTasks):
    """Start a new analysis (runs in background)"""
    try:
        # Validate request
        if not request.brand_name or not request.brand_name.strip():
            raise HTTPException(status_code=400, detail="Brand name is required")
        
        if not request.selected_llms or len(request.selected_llms) == 0:
            raise HTTPException(status_code=400, detail="At least one LLM must be selected")
        
        # Normalize LLM names
        normalized_llms = []
        valid_llms = ["Claude", "Mistral", "Google AI Overview"]
        
        for llm in request.selected_llms:
            if isinstance(llm, str):
                matched = False
                for valid_llm in valid_llms:
                    if valid_llm.lower() in llm.lower() or llm.lower() in valid_llm.lower():
                        normalized_llms.append(valid_llm)
                        matched = True
                        break
                
                if not matched and llm.lower() not in ["string", ""]:
                    normalized_llms.append(llm)
        
        if not normalized_llms:
            raise HTTPException(status_code=400, detail="Invalid LLM selection")
        
        # Create session ID
        session_id = create_session_id(request.brand_name, request.product_name)
        
        # Initialize progress tracking
        analysis_progress[session_id] = {
            "progress": 0,
            "current_step": "Initializing...",
            "status": "running",
            "session_id": session_id
        }
        
        logger.info(f"✅ Analysis started for {request.brand_name} (Session: {session_id})")
        logger.info(f"   LLMs: {normalized_llms}")
        logger.info(f"   Prompts: {request.num_prompts}")
        
        # Add background task
        background_tasks.add_task(
            execute_analysis_workflow,
            session_id,
            request.brand_name,
            request.product_name,
            request.website_url,
            request.num_prompts,
            normalized_llms,
            request.regenerate_prompts
        )
        
        return {
            "session_id": session_id,
            "status": "started",
            "message": f"Analysis started for {request.brand_name}"
        }
    
    except HTTPException as e:
        logger.error(f"❌ Validation error: {str(e.detail)}")
        raise
    except Exception as e:
        logger.error(f"❌ Error starting analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/api/recent-analyses")
def recent_analyses():
    try:
        # Adjust limit as needed (10 latest)
        recent_sessions = get_recent_sessions(limit=10)  
        # Example format: [{session_id, brand_name, timestamp, product_name, website_url}]
        return {"total": len(recent_sessions), "analyses": recent_sessions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching recent analyses: {str(e)}")
    
@app.get("/api/analysis/status/{session_id}")
def get_status(session_id: str):
    """Get current analysis progress"""
    if session_id not in analysis_progress:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    
    return analysis_progress[session_id]

@app.get("/api/results/{session_id}")
def get_results(session_id: str):
    """Get completed analysis results"""
    try:
        from services.database_manager import get_session_results_aggregated
        
        results = get_session_results_aggregated(session_id)
        if not results:
            raise HTTPException(status_code=404, detail="Session not found")
        return results
    except Exception as e:
        logger.error(f"Error fetching results: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/results/")
def list_sessions():
    """List all sessions"""
    try:
        sessions = get_all_sessions()
        return {
            "total": len(sessions),
            "sessions": sessions
        }
    except Exception as e:
        logger.error(f"Error listing sessions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ============= BACKGROUND TASK =============

async def execute_analysis_workflow(
    session_id: str,
    brand_name: str,
    product_name: Optional[str],
    website_url: Optional[str],
    num_prompts: int,
    selected_llms: List[str],
    regenerate_prompts: bool = False
):
    """Execute the complete analysis workflow"""
    try:
        # Step 1: Deep Research (10%)
        update_progress(session_id, 10, "🔍 Conducting market research...")
        logger.info(f"Step 1: Deep Research for {brand_name}")
        research_data = conduct_deep_research(brand_name, product_name, website_url)
        
        # Step 2: Keyword Extraction (20%)
        update_progress(session_id, 20, "🔑 Extracting keywords...")
        logger.info("Step 2: Keyword Extraction")
        keywords = extract_keywords(brand_name, research_data, product_name)
        
        # Step 3: Prompt Generation/Loading (30%)
        update_progress(session_id, 30, "📝 Checking for saved prompts...")
        logger.info("Step 3: Prompt Generation/Loading")
        
        prompts = None
        
        # Check if we should use saved prompts
        if not regenerate_prompts:
            from services.database_manager import get_saved_prompts
            prompts = get_saved_prompts(brand_name, product_name)
            
            if prompts:
                logger.info(f"✅ Using {len(prompts)} saved prompts from database")
                update_progress(session_id, 30, "✅ Loaded saved prompts!")
            else:
                logger.info("No saved prompts found, generating new ones...")
        else:
            logger.info("🔄 Regenerate flag enabled, generating new prompts...")
        
        # Generate new prompts if needed
        if not prompts:
            update_progress(session_id, 30, "📝 Generating new prompts...")
            prompts = generate_prompts(brand_name, num_prompts, research_data, keywords)
            
            if not prompts:
                raise Exception("Failed to generate prompts")
            
            # Save newly generated prompts
            from services.database_manager import save_prompts_to_db
            save_prompts_to_db(brand_name, prompts, product_name)
            logger.info(f"💾 Saved {len(prompts)} new prompts to database")
            # Save session metadata
        save_session(session_id, brand_name, product_name, website_url, research_data, keywords)
        
        # ✅ ADD THIS CRITICAL LINE - Extract competitors for later use
        competitors_list = research_data.get('competitors', [])
        logger.info(f"Extracted competitors: {competitors_list}")
        
        # Step 4: Execute LLM Analysis (60%)
        update_progress(session_id, 40, f"🤖 Running {len(selected_llms)} LLMs: {', '.join(selected_llms)}...")
        logger.info(f"Step 4: Executing LLMs: {selected_llms}")
        
        llm_responses = execute_prompts_multi_llm_sync(
            prompts=prompts,
            llms=selected_llms,
            brand_name=brand_name
        )
        
        if not llm_responses:
            raise Exception("No LLM responses received")
        
        # Step 5: Scoring (80%)
        update_progress(session_id, 80, "📊 Calculating scores...")
        logger.info("Step 5: Scoring")
        scored_results = calculate_scores(llm_responses, brand_name, keywords)
        
        # ✅ FIXED: Save LLM responses WITH CITATIONS to database
        logger.info("💾 Saving LLM responses and citations to database...")
        for result in scored_results:
            try:
                prompt_id = create_prompt_id(session_id, result.get('prompt_index', 0))
                
                # Extract citations and prompt from the original llm_responses
                matching_response = next(
                    (r for r in llm_responses 
                    if r.get('prompt_index') == result.get('prompt_index') 
                    and r.get('llm_name') == result.get('llm_name')),
                    None
                )
                
                # ✅ Get both citations AND prompt text from original response
                citations = matching_response.get('citations', []) if matching_response else []
                prompt_text = matching_response.get('prompt', '') if matching_response else result.get('prompt', '')
                
                logger.info(f"📌 Saving - LLM: {result.get('llm_name')}, Prompt exists: {bool(prompt_text)}, Citations: {len(citations)}")
                
                # ✅ IMPORTANT: Pass prompt_text explicitly - THIS WAS THE BUG!
                save_llm_response(
                    prompt_id, 
                    session_id, 
                    result.get('llm_name'),
                    prompt_text,  # ✅ FIX: Use actual prompt text from matching_response
                    result.get('response', ''),
                    citations=citations
                )
                
                # ✅ ENSURE VISIBILITY SCORE IS IN SCORES DICT
                scores_dict = result.get('scores', {})
                if 'normalized_visibility' not in scores_dict and 'visibility_score' in result:
                    scores_dict['normalized_visibility'] = result.get('visibility_score', 0)
                
                # Save scoring results - now WITH visibility score
                save_scoring_result(
                    prompt_id, 
                    session_id, 
                    result.get('llm_name'),
                    scores_dict  # ✅ FIX: This now includes normalized_visibility
                )
                
            except Exception as e:
                logger.warning(f"❌ Could not save response/scoring result: {str(e)}")
                logger.warning(f"   Debug - Result: {result}")

        # Step 6: Share of Voice (90%)
        update_progress(session_id, 90, "📈 Computing share of voice...")
        logger.info("Step 6: Share of Voice")
        
        sov_data = None
        
        # ✅ USE THE competitors_list EXTRACTED EARLIER
        if competitors_list:
            try:
                logger.info(f"Found {len(competitors_list)} competitors: {competitors_list}")
                save_competitors(session_id, competitors_list)
                
                # ✅ FIXED: Pass both scored_results AND competitors_list
                sov_data = calculate_share_of_voice(scored_results, competitors_list)
                
                if sov_data:
                    # ✅ FIXED: Save each brand's SOV data properly
                    if 'ranked_brands' in sov_data:
                        ranked_brands = sov_data.get('ranked_brands', [])
                        logger.info(f"Saving SOV for {len(ranked_brands)} brands")
                        
                        for rank_index, brand_data in enumerate(ranked_brands, 1):
                            try:
                                brand_name_sov = brand_data.get('brand_name', 'Unknown')
                                sov_scores_dict = {
                                    'normalized_visibility': float(brand_data.get('normalized_visibility', 0)),
                                    'average_positioning': float(brand_data.get('average_positioning', 0)),
                                    'weighted_score': float(brand_data.get('weighted_score', 0)),
                                }
                                
                                save_share_of_voice(
                                    session_id,
                                    brand_name_sov,
                                    sov_scores_dict,
                                    rank_index
                                )
                                logger.info(f"  ✔ Saved SOV for {brand_name_sov} (Rank {rank_index})")
                            except Exception as e:
                                logger.warning(f"Could not save SOV for {brand_data.get('brand_name', 'Unknown')}: {str(e)}")
                        
                        logger.info(f"✔ Share of Voice saved: {len(ranked_brands)} brands")
                    else:
                        logger.warning("⚠️ Share of Voice missing 'ranked_brands' key")
                else:
                    logger.warning("⚠️ Share of Voice returned None")
                    
            except Exception as e:
                logger.error(f"❌ Error calculating Share of Voice: {str(e)}", exc_info=True)
                sov_data = None
        else:
            logger.info("⚠️ No competitors found in research data - skipping Share of Voice")
            sov_data = None
        
        # Aggregate results
        summary = aggregate_results(scored_results)
        
        # Step 7: Complete (100%)
        update_progress(session_id, 100, "✅ Analysis complete!")
        analysis_progress[session_id]["status"] = "completed"
        
        logger.info(f"✅ Analysis completed for {brand_name}")
        logger.info(f"   - Scored Results: {len(scored_results)}")
        logger.info(f"   - Share of Voice: {'Yes' if sov_data else 'No'}")
        
    except Exception as e:
        logger.error(f"❌ Error in analysis workflow: {str(e)}", exc_info=True)
        analysis_progress[session_id]["status"] = "error"
        analysis_progress[session_id]["error"] = str(e)

def update_progress(session_id: str, progress: int, step: str):
    """Update analysis progress"""
    if session_id in analysis_progress:
        analysis_progress[session_id]["progress"] = progress
        analysis_progress[session_id]["current_step"] = step
        logger.info(f"[{session_id}] {progress}% - {step}")

from services.database_manager import get_brand_visibility_history

# Add this endpoint after your existing endpoints

@app.get("/api/brand-history/{brand_name}")
async def get_brand_history(brand_name: str):
    """
    ✅ NEW: Get brand visibility history across all analysis dates
    
    Example: GET /api/brand-history/Apple
    
    Returns:
    {
        "brand_name": "Apple",
        "history": [
            {
                "date": "2024-10-06",
                "timestamp": "2024-10-06T14:30:00",
                "visibility_score": 65.5,
                "session_id": "apple_20241006_143000"
            },
            {
                "date": "2024-10-28",
                "timestamp": "2024-10-28T10:15:00",
                "visibility_score": 72.1,
                "session_id": "apple_20241028_101500"
            }
        ],
        "total_analyses": 2
    }
    """
    try:
        history = get_brand_visibility_history(brand_name)
        
        if not history:
            raise HTTPException(
                status_code=404,
                detail=f"No analysis history found for brand: {brand_name}"
            )
        
        return {
            "brand_name": brand_name,
            "history": history,
            "total_analyses": len(history)
        }
    except Exception as e:
        logger.error(f"Error fetching brand history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
@app.get("/api/brands")
def get_all_brands():
    """Get all unique brands for dropdown selector"""
    try:
        brands = get_all_unique_brands()
        return {"brands": brands}
    except Exception as e:
        logger.error(f"Error fetching brands: {str(e)}")
        return {"brands": [], "error": str(e)}

@app.get("/api/recent-analyses-by-brand/{brand_name}")
def get_recent_analyses_by_brand(brand_name: str, limit: int = 20):
    """Get recent analyses for a specific brand"""
    try:
        sessions = get_recent_sessions_by_brand(brand_name, limit)
        return {"sessions": sessions}
    except Exception as e:
        logger.error(f"Error fetching analyses for brand {brand_name}: {str(e)}")
        return {"sessions": [], "error": str(e)}

@app.get("/api/visibility-history/brand-product/{brand_name}/{product_name}")
def get_brand_product_history(brand_name: str, product_name: str):
    """Get visibility history for brand + product combination"""
    try:
        history = get_product_specific_visibility_history(brand_name, product_name)
        return {"history": history}
    except Exception as e:
        logger.error(f"Error fetching product visibility history: {str(e)}")
        return {"history": [], "error": str(e)}
    
def get_llm_names_from_session(session_id: str) -> List[str]:
    conn = sqlite3.connect(services.database_manager.DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT llm_name FROM llm_responses WHERE session_id = ?", (session_id,))
    llm_names = [row[0] for row in cursor.fetchall()]
    conn.close()
    return llm_names

@app.post("/api/reanalyze-with-same-prompts/{session_id}")
async def reanalyze_with_same_prompts(
    session_id: str,
    background_tasks: BackgroundTasks
):
    """Re-analyze with the same prompts from a previous session"""
    try:
        # Get original session details
        original_session = get_session_results(session_id)
        if not original_session:
            raise HTTPException(status_code=404, detail="Original session not found")
        
        # Extract metadata
        session_metadata = original_session.get('session')
        if not session_metadata:
             raise HTTPException(status_code=404, detail="Original session metadata not found")
        
        # session_metadata is a tuple from DB: (session_id, brand_name, product_name, website_url, timestamp, research_data, keywords)
        brand_name = session_metadata[1]
        product_name = session_metadata[2]
        website_url = session_metadata[3]
        research_data_json = session_metadata[5]
        keywords_json = session_metadata[6]
        
        # Get prompts and LLMs
        prompts = get_saved_prompts_for_analysis(session_id)
        llm_names = get_llm_names_from_session(session_id) # Use the fixed helper function
        
        if not prompts:
            raise HTTPException(status_code=400, detail="No prompts found for this session")
        if not llm_names:
            logger.warning("No LLM names found in original session, defaulting to Claude")
            llm_names = ['Claude']
        
        # Create new session ID
        # ✅ FIX: Must pass brand_name to create_session_id
        new_session_id = create_session_id(brand_name, product_name)
        
        # Save new session using original data (which is JSON/string formatted)
        save_session(
            new_session_id,
            brand_name,
            product_name,
            website_url,
            research_data_json, # Already JSON string from original session DB fetch
            keywords_json        # Already JSON string from original session DB fetch
        )
        
        # Initialize progress tracking for the new session
        analysis_progress[new_session_id] = {
            "progress": 0,
            "current_step": "Initializing Re-analysis...",
            "status": "running",
            "session_id": new_session_id
        }

        # Run analysis with saved prompts
        background_tasks.add_task(
            run_analysis_with_saved_prompts,
            new_session_id,
            brand_name,
            prompts,
            llm_names,
            research_data_json, # Pass JSON strings/dict for background task
            keywords_json
        )
        
        return {
            "new_session_id": new_session_id,
            "message": "Re-analysis started with same prompts",
            "status": "processing"
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error in re-analysis: {str(e)}", exc_info=True)
        # Ensure the re-analysis session is marked as error if started
        if 'new_session_id' in locals() and new_session_id in analysis_progress:
            analysis_progress[new_session_id]["status"] = "error"
            analysis_progress[new_session_id]["error"] = str(e)
        raise HTTPException(status_code=500, detail=str(e))
    

async def run_analysis_with_saved_prompts(
    session_id: str,
    brand_name: str,
    prompts: list,
    llm_names: list,
    research_data_json: Optional[str] = None,
    keywords_json: Optional[str] = None
):
    """Execute analysis using pre-saved prompts"""
    update_progress(session_id, 10, "🤖 Re-executing LLMs with saved prompts...")

    try:
        research_data = {}
        keywords = []
        competitors_list = []
        product_name = None  # <-- Always define safely

        # Parse research_data safely
        if research_data_json:
            try:
                if isinstance(research_data_json, str):
                    research_data = json.loads(research_data_json)
                elif isinstance(research_data_json, dict):
                    research_data = research_data_json
                else:
                    logger.warning(f"research_data_json has unexpected type: {type(research_data_json)}")
                    research_data = {}
                logger.info(f"📊 Parsed research_data keys: {list(research_data.keys()) if isinstance(research_data, dict) else 'Not a dict'}")
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse research_data_json: {str(e)}")
                logger.error(f"Raw research_data_json: {research_data_json[:200]}...")
                research_data = {}

        # Extract product_name from research_data (fallback: None)
        if isinstance(research_data, dict):
            product_name = research_data.get('product_name', None)

        # Parse keywords safely
        if keywords_json:
            try:
                if isinstance(keywords_json, str):
                    keywords = json.loads(keywords_json)
                elif isinstance(keywords_json, list):
                    keywords = keywords_json
                else:
                    logger.warning(f"keywords_json has unexpected type: {type(keywords_json)}")
                    keywords = []
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse keywords_json: {str(e)}")
                keywords = []

        # Competitors extraction w/ fallback to DB
        if isinstance(research_data, dict):
            competitors_list = research_data.get('competitors', [])
            logger.info(f"Extracted {len(competitors_list)} competitors from research_data")
        else:
            logger.warning(f"research_data is not a dict: {type(research_data)}")
            competitors_list = []
        if not competitors_list:
            logger.warning("⚠️ No competitors in research_data, checking database...")
            try:
                conn = sqlite3.connect(services.database_manager.DATABASE_PATH)
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT DISTINCT competitor_name 
                    FROM competitors c
                    JOIN analysis_sessions s ON c.session_id = s.session_id
                    WHERE s.brand_name = ?
                    ORDER BY c.rank
                    LIMIT 10
                """, (brand_name,))
                db_competitors = [row[0] for row in cursor.fetchall()]
                conn.close()
                if db_competitors:
                    competitors_list = db_competitors
                    logger.info(f"✅ Found {len(competitors_list)} competitors from database: {competitors_list}")
                else:
                    logger.warning(f"⚠️ No competitors found in database for brand: {brand_name}")
            except Exception as e:
                logger.error(f"Error querying database for competitors: {str(e)}")
        logger.info(f"✓ Final data - Competitors: {len(competitors_list)} {competitors_list}, Keywords: {len(keywords)}")

        # Step 1: Execute prompts with multiple LLMs
        llm_responses = execute_prompts_multi_llm_sync(
            prompts=prompts,
            llms=llm_names,
            brand_name=brand_name
        )
        if not llm_responses:
            raise Exception("No LLM responses received in re-analysis")
        update_progress(session_id, 60, "📊 Recalculating scores...")

        # Step 2: Calculate scores
        scored_results = calculate_scores(llm_responses, brand_name, keywords)

        # Step 3: Save LLM responses and scores
        for result in scored_results:
            prompt_index = result.get('prompt_index', 0)
            prompt_id = create_prompt_id(session_id, prompt_index)

            # Find matching original response for citations/prompt text
            matching_response = next(
                (r for r in llm_responses
                 if r.get('prompt_index') == prompt_index
                 and r.get('llm_name') == result.get('llm_name')),
                None
            )

            citations = matching_response.get('citations', []) if matching_response else []
            prompt_text = matching_response.get('prompt', '') if matching_response else result.get('prompt', '')

            save_llm_response(
                prompt_id,
                session_id,
                result.get('llm_name'),
                prompt_text,
                result.get('response', ''),
                citations=citations
            )

            save_scoring_result(
                prompt_id,
                session_id,
                result.get('llm_name'),
                result.get('scores', {})
            )

        logger.info(f"💾 Saving {len(prompts)} prompts for re-analysis session {session_id}")
        try:
            from services.database_manager import save_prompts_to_db
            save_prompts_to_db(brand_name, prompts, product_name)
            logger.info(f"✓ Prompts saved successfully for brand: {brand_name}")
        except Exception as e:
            logger.warning(f"Could not save prompts for re-analysis: {str(e)}")

        update_progress(session_id, 80, "📈 Computing Share of Voice...")

        # Step 4: Share of Voice (Session-Specific)
        if competitors_list:
            try:
                save_competitors(session_id, competitors_list)
                logger.info(f"✓ Saved {len(competitors_list)} competitors for session {session_id}")
                sov_data = calculate_share_of_voice(scored_results, competitors_list)
                if sov_data and 'ranked_brands' in sov_data:
                    logger.info(f"📊 Saving Share of Voice for {len(sov_data['ranked_brands'])} brands in session {session_id}")
                    for rank_index, brand_data in enumerate(sov_data['ranked_brands'], 1):
                        sov_scores_dict = {
                            'normalized_visibility': float(brand_data.get('normalized_visibility', 0)),
                            'average_positioning': float(brand_data.get('average_positioning', 0)),
                            'weighted_score': float(brand_data.get('weighted_score', 0)),
                        }
                        save_share_of_voice(
                            session_id,
                            brand_data.get('brand_name', 'Unknown'),
                            sov_scores_dict,
                            rank_index
                        )
                        logger.info(f"  ✓ Saved SOV for {brand_data.get('brand_name')} - Rank {rank_index} - Visibility: {sov_scores_dict['normalized_visibility']:.1f}%")
                    logger.info(f"✅ Share of Voice calculation complete for session {session_id}")
                else:
                    logger.warning(f"⚠️ No SOV data generated for session {session_id}")
            except Exception as e:
                logger.error(f"❌ Error calculating Share of Voice in re-analysis: {str(e)}", exc_info=True)
        else:
            logger.info(f"ℹ️ No competitors provided for session {session_id} - skipping Share of Voice calculation")

        # Step 5: Aggregate results for frontend summary
        update_progress(session_id, 90, "📊 Aggregating results...")
        logger.info("Step 5: Aggregating results for summary metrics...")

        summary = aggregate_results(scored_results)
        logger.info(f"✓ Aggregated results:")
        logger.info(f"  - Total prompts: {summary.get('total_prompts', 0)}")
        logger.info(f"  - Total mentions: {summary.get('total_mentions', 0)}")
        logger.info(f"  - Mention rate: {summary.get('mention_rate', 0):.1f}%")
        logger.info(f"  - Avg position: {summary.get('avg_position', 0)}")
        logger.info(f"  - Avg visibility: {summary.get('avg_visibility_score', 0):.1f}")

        save_brand_score_summary(session_id, brand_name, summary)
        logger.info(f"✓ Saved summary metrics to database for session {session_id}")

        # Step 6: Complete
        update_progress(session_id, 100, "✅ Re-analysis complete!")
        analysis_progress[session_id]["status"] = "completed"
        logger.info(f"✅ Re-analysis completed for session {session_id}")

    except Exception as e:
        logger.error(f"❌ Error during re-analysis execution for {session_id}: {str(e)}", exc_info=True)
        update_progress(session_id, 100, f"❌ Error: {str(e)}")
        analysis_progress[session_id]["status"] = "error"
        analysis_progress[session_id]["error"] = str(e)



@app.get("/api/same-prompts-history/{session_id}")
def get_same_prompts_history(session_id: str):
    """Get visibility history for when same prompts are analyzed again"""
    try:
        # ✅ FIX: Use get_session_results_aggregated which returns brand_name correctly
        from services.database_manager import get_session_results_aggregated
        
        original_results = get_session_results_aggregated(session_id)
        if not original_results:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # ✅ FIX: Extract brand_name from correct structure
        brand_name = original_results.get('brand_name')
        product_name = original_results.get('product_name', '')  # Optional
        
        if not brand_name:
            logger.error(f"No brand_name found in session {session_id}")
            return {"history": [], "error": "Brand name not found"}
        
        logger.info(f"📊 Fetching same prompts history for brand: {brand_name}, session: {session_id}")
        
        # Get saved prompts
        prompts = get_saved_prompts_for_analysis(session_id)
        if not prompts:
            logger.info(f"No prompts found for session {session_id}")
            return {"history": [], "message": "No prompts found"}
        
        logger.info(f"Found {len(prompts)} prompts for matching")
        
        # Get history of when these same prompts were analyzed
        history = get_visibility_history_for_same_prompts(brand_name, product_name, prompts)
        
        logger.info(f"✓ Returning {len(history)} data points for same prompts history")
        return {"history": history}
        
    except Exception as e:
        logger.error(f"Error fetching same prompts history: {str(e)}", exc_info=True)
        return {"history": [], "error": str(e)}


# ============= RUN =============

if __name__ == "__main__":
    import uvicorn
    
    print("\n" + "="*60)
    print("🚀 BRAND VISIBILITY ANALYZER - LOCAL BACKEND")
    print("="*60)
    print("\n📍 API running at: http://localhost:8000")
    print("📚 API Docs at: http://localhost:8000/docs")
    print("📖 ReDoc at: http://localhost:8000/redoc")
    print("\n✅ Press Ctrl+C to stop\n")
    
    uvicorn.run(
        "app:app",
        host="127.0.0.1",
        port=8000,
        reload=False,
        log_level="info"
    )