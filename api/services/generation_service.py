import logging
from typing import Dict, Any, List
from api.models.request_models import GenerationRequest
from api.services.ai_service import AIService

logger = logging.getLogger(__name__)

class GenerationService:
    """Service for orchestrating the application generation process"""
    
    def __init__(self, ai_service: AIService):
        self.ai_service = ai_service
    
    async def generate_application(self, request: GenerationRequest) -> Dict[str, Any]:
        """Generate a complete web application based on the request"""
        try:
            logger.info(f"Starting generation for prompt: {request.prompt[:100]}...")
            
            # Generate the code using AI service
            files = await self.ai_service.generate_code(
                prompt=request.prompt,
                framework=request.framework,
                styling=request.styling,
                features=request.features,
                complexity=request.complexity,
                model=request.model,
                images=request.images
            )
            
            # Create metadata
            metadata = {
                "framework": request.framework,
                "styling": request.styling,
                "features": request.features,
                "complexity": request.complexity,
                "model": request.model,
                "files_count": len(files),
                "total_size": sum(len(content) for content in files.values())
            }
            
            # Create response
            result = {
                "status": "success",
                "files": files,
                "metadata": metadata,
                "message": f"Successfully generated {len(files)} files",
                # Surface raw LLM response for debugging in the UI
                "raw_llm_response": getattr(self.ai_service, "last_raw_response", None)
            }
            
            logger.info(f"Generation completed successfully. Generated {len(files)} files.")
            return result
            
        except Exception as e:
            logger.error(f"Generation failed: {str(e)}")
            return {
                "status": "error",
                "message": f"Generation failed: {str(e)}",
                "files": {},
                "metadata": {}
            }
    
    def validate_generation_request(self, request: GenerationRequest) -> Dict[str, Any]:
        """Validate the generation request"""
        errors = []
        
        # Check required fields
        if not request.prompt or not request.prompt.strip():
            errors.append("Prompt is required")
        
        # Validate framework
        valid_frameworks = ["React", "Vue.js", "Vanilla JavaScript", "Python Flask", "Python FastAPI"]
        if request.framework and request.framework not in valid_frameworks:
            errors.append(f"Invalid framework. Must be one of: {', '.join(valid_frameworks)}")
        
        # Validate complexity
        valid_complexities = ["Simple", "Medium", "Complex"]
        if request.complexity and request.complexity not in valid_complexities:
            errors.append(f"Invalid complexity. Must be one of: {', '.join(valid_complexities)}")
        
        # Validate model (allow all gpt-5* plus legacy aliases)
        valid_prefixes = ["gpt-5"]
        legacy_allowed = ["gpt-4", "gpt-3.5-turbo"]
        if request.model:
            is_valid = (
                any(request.model.startswith(p) for p in valid_prefixes)
                or request.model in legacy_allowed
            )
            if not is_valid:
                allowed_desc = ", ".join(["gpt-5-*", *legacy_allowed])
                errors.append(f"Invalid model. Must be one of: {allowed_desc}")
        
        if errors:
            return {
                "valid": False,
                "errors": errors
            }
        
        return {
            "valid": True,
            "request": request
        }
    
    def get_generation_statistics(self, files: Dict[str, str]) -> Dict[str, Any]:
        """Get statistics about the generated files"""
        if not files:
            return {
                "total_files": 0,
                "total_size": 0,
                "file_types": {},
                "average_file_size": 0
            }
        
        file_types = {}
        total_size = 0
        
        for file_path, content in files.items():
            # Determine file type from extension
            if '.' in file_path:
                ext = file_path.split('.')[-1].lower()
                file_types[ext] = file_types.get(ext, 0) + 1
            else:
                file_types['no_extension'] = file_types.get('no_extension', 0) + 1
            
            total_size += len(content)
        
        return {
            "total_files": len(files),
            "total_size": total_size,
            "file_types": file_types,
            "average_file_size": total_size / len(files) if files else 0
        }
    
    def create_download_package(self, files: Dict[str, str]) -> Dict[str, Any]:
        """Create a downloadable package of the generated files"""
        import json
        import base64
        import zipfile
        import io
        
        try:
            # Create a zip file in memory
            zip_buffer = io.BytesIO()
            
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for file_path, content in files.items():
                    zip_file.writestr(file_path, content)
            
            # Get the zip content
            zip_content = zip_buffer.getvalue()
            
            # Encode as base64 for easy transmission
            encoded_content = base64.b64encode(zip_content).decode('utf-8')
            
            return {
                "success": True,
                "content": encoded_content,
                "size": len(zip_content),
                "filename": "generated_app.zip"
            }
            
        except Exception as e:
            logger.error(f"Error creating download package: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def analyze_generated_code(self, files: Dict[str, str]) -> Dict[str, Any]:
        """Analyze the generated code for quality and completeness"""
        analysis = {
            "has_html": False,
            "has_css": False,
            "has_js": False,
            "has_readme": False,
            "has_package_json": False,
            "file_count": len(files),
            "total_lines": 0,
            "estimated_complexity": "Low"
        }
        
        for file_path, content in files.items():
            # Check file types
            if file_path.endswith('.html'):
                analysis["has_html"] = True
            elif file_path.endswith('.css'):
                analysis["has_css"] = True
            elif file_path.endswith('.js') or file_path.endswith('.jsx'):
                analysis["has_js"] = True
            elif file_path.lower() == 'readme.md':
                analysis["has_readme"] = True
            elif file_path.lower() == 'package.json':
                analysis["has_package_json"] = True
            
            # Count lines
            analysis["total_lines"] += len(content.split('\n'))
        
        # Estimate complexity based on file count and lines
        if analysis["file_count"] > 10 or analysis["total_lines"] > 500:
            analysis["estimated_complexity"] = "High"
        elif analysis["file_count"] > 5 or analysis["total_lines"] > 200:
            analysis["estimated_complexity"] = "Medium"
        else:
            analysis["estimated_complexity"] = "Low"
        
        return analysis 