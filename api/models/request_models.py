from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class ImageData(BaseModel):
    """Model for uploaded image data"""
    name: str = Field(..., description="Original filename of the image")
    data: str = Field(..., description="Base64 encoded image data")
    mime_type: str = Field(..., description="MIME type of the image")
    size: int = Field(..., description="Size of the image in bytes")
    role: Optional[str] = Field("reference", description="Purpose of the image (logo, background, layout, etc.)")
    alt: Optional[str] = Field("", description="Alt text for accessibility")
    notes: Optional[str] = Field("", description="Additional notes about the image")

class GenerationRequest(BaseModel):
    """Request model for generating web applications"""
    prompt: str = Field(..., description="Natural language description of the web application to generate")
    framework: Optional[str] = Field("React", description="Preferred framework for the application")
    styling: Optional[str] = Field("Tailwind CSS", description="Styling framework to use")
    features: Optional[List[str]] = Field(default_factory=list, description="List of features to include")
    complexity: Optional[str] = Field("Medium", description="Complexity level of the application")
    model: Optional[str] = Field("gpt-5-2025-08-07", description="AI model to use for generation")
    images: Optional[List[ImageData]] = Field(default_factory=list, description="List of uploaded images for visual context")
    
    class Config:
        json_schema_extra = {
            "example": {
                "prompt": "Create a todo list application with the ability to add, edit, and delete tasks. Include dark mode support and a modern design.",
                "framework": "React",
                "styling": "Tailwind CSS",
                "features": ["User Authentication", "Dark Mode", "Responsive Design"],
                "complexity": "Medium",
                "model": "gpt-5-2025-08-07",
                "images": []
            }
        }

class HealthResponse(BaseModel):
    """Response model for health check endpoint"""
    status: str = Field(..., description="Health status of the service")
    timestamp: str = Field(..., description="ISO timestamp of the health check")
    version: str = Field(..., description="API version")
    ai_service_status: str = Field(..., description="Status of the AI service")

class GenerationResponse(BaseModel):
    """Response model for generation endpoint"""
    status: str = Field(..., description="Status of the generation process")
    files: Dict[str, str] = Field(..., description="Generated files with their content")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata about the generation")
    download_url: Optional[str] = Field(None, description="URL to download the generated application")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "files": {
                    "index.html": "<!DOCTYPE html>...",
                    "app.js": "// React application code...",
                    "styles.css": "/* CSS styles... */"
                },
                "metadata": {
                    "framework": "React",
                    "styling": "Tailwind CSS",
                    "complexity": "Medium"
                },
                "download_url": "http://localhost:8000/download/123"
            }
        }

class GenerationHistoryItem(BaseModel):
    """Model for generation history items"""
    id: int = Field(..., description="Unique identifier for the generation")
    timestamp: str = Field(..., description="ISO timestamp of the generation")
    prompt: str = Field(..., description="Original prompt used for generation")
    framework: str = Field(..., description="Framework used for generation")
    styling: str = Field(..., description="Styling framework used")
    features: List[str] = Field(..., description="Features included in the generation")
    complexity: str = Field(..., description="Complexity level of the generation")
    model: str = Field(..., description="AI model used for generation")
    files_generated: int = Field(..., description="Number of files generated")

class ErrorResponse(BaseModel):
    """Error response model"""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat(), description="Error timestamp")

class ModelInfo(BaseModel):
    """Model information"""
    name: str = Field(..., description="Model name")
    description: str = Field(..., description="Model description")
    capabilities: List[str] = Field(..., description="Model capabilities")
    max_tokens: Optional[int] = Field(None, description="Maximum tokens for the model")

class ModelsResponse(BaseModel):
    """Response model for available models endpoint"""
    models: List[ModelInfo] = Field(..., description="List of available models")
    default_model: str = Field(..., description="Default model to use") 