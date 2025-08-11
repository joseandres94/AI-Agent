from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os
import sys
import json
from datetime import datetime
import logging
from dotenv import load_dotenv

# Import local modules
from api.models.request_models import GenerationRequest, HealthResponse
from api.services.ai_service import AIService
from api.services.generation_service import GenerationService
from api.utils.config import get_settings
from api.services.ai_service import AIService as _AIServiceForDebug

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="AI Agent - Web App Generator API",
    description="An intelligent AI agent that creates web applications from natural language prompts",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
settings = get_settings()
ai_service = AIService()
generation_service = GenerationService(ai_service)

# In-memory storage for generation history (in production, use a database)
generation_history = []

@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint"""
    return {
        "message": "AI Agent Web App Generator API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    try:
        # Check if AI service is available
        ai_status = await ai_service.check_availability()
        
        return HealthResponse(
            status="healthy",
            timestamp=datetime.now().isoformat(),
            version="1.0.0",
            ai_service_status=ai_status
        )
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Service unhealthy")

@app.get("/models")
async def get_available_models():
    """Get available AI models"""
    try:
        models = await ai_service.get_available_models()
        return {
            "models": models,
            "default_model": settings.openai_model
        }
    except Exception as e:
        logger.error(f"Error getting models: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get models")

@app.post("/generate")
async def generate_application(request: GenerationRequest):
    """Generate a web application based on the provided prompt"""
    try:
        logger.info(f"Received generation request: {request.prompt[:100]}...")
        
        # Validate request
        if not request.prompt.strip():
            raise HTTPException(status_code=400, detail="Prompt is required")
        
        # Generate the application
        result = await generation_service.generate_application(request)
        
        # Store in history
        generation_record = {
            "id": len(generation_history) + 1,
            "timestamp": datetime.now().isoformat(),
            "prompt": request.prompt,
            "framework": request.framework,
            "styling": request.styling,
            "features": request.features,
            "complexity": request.complexity,
            "model": request.model,
            "files_generated": len(result.get("files", {}))
        }
        generation_history.append(generation_record)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating application: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")

@app.get("/history")
async def get_generation_history():
    """Get the history of generated applications"""
    try:
        return {
            "history": generation_history,
            "total_generations": len(generation_history)
        }
    except Exception as e:
        logger.error(f"Error getting history: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get history")

class ParseRequest(BaseModel):
    content: str
    framework: str = "React"
    styling: str = "Tailwind CSS"

@app.post("/debug/parse")
async def debug_parse_generated_code(req: ParseRequest):
    """Debug endpoint to parse raw LLM content using the server's parser."""
    try:
        svc = _AIServiceForDebug()
        files = svc._parse_generated_code(req.content)#, req.framework, req.styling)
        return {"files": files, "count": len(files)}
    except Exception as e:
        logger.error(f"Parse debug failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/history")
async def clear_generation_history():
    """Clear the generation history"""
    try:
        global generation_history
        generation_history = []
        return {"message": "History cleared successfully"}
    except Exception as e:
        logger.error(f"Error clearing history: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to clear history")

@app.get("/status/{generation_id}")
async def get_generation_status(generation_id: int):
    """Get the status of a specific generation"""
    try:
        if generation_id <= 0 or generation_id > len(generation_history):
            raise HTTPException(status_code=404, detail="Generation not found")
        
        generation = generation_history[generation_id - 1]
        return generation
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting generation status: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get generation status")

if __name__ == "__main__":
    import uvicorn
    print(settings.api_host, settings.api_port)
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug
    ) 