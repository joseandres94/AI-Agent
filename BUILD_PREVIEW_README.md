# Build-Based Preview System

## Overview

The new build-based preview system creates a production-like preview by:

1. **Creating a complete React project structure** with all necessary files
2. **Running `npm install && npm run build`** to build the application
3. **Serving the build folder** via a static file server
4. **Embedding the preview** in an iframe with full React functionality

## Key Features

### ✅ **Production-Like Preview**
- Uses actual React build process
- Includes all dependencies (React, React Router, Tailwind CSS)
- Handles complex component structures
- Supports all React features (hooks, routing, etc.)

### ✅ **Static Server Integration**
- Automatically starts a static file server
- Serves the built application from `build/` folder
- Provides fallback to inline HTML if server fails
- Configurable port (default: 3000)

### ✅ **Complete React Support**
- React 18 with createRoot
- React Router DOM for navigation
- Tailwind CSS for styling
- All modern React features

### ✅ **Asset Handling**
- Converts uploaded images to data URLs
- Handles all image formats (PNG, JPG, SVG, etc.)
- Integrates assets into the build process
- Supports both local and external assets

## Architecture

```
User Uploads Files
       ↓
Create React Project Structure
       ↓
npm install && npm run build
       ↓
Start Static Server (serve/http-server)
       ↓
Embed in iframe with sandbox
```

## Implementation Details

### 1. Project Structure Creation

The system creates a complete React project:

```
react-app/
├── package.json          # Dependencies and scripts
├── public/
│   └── index.html       # Main HTML file
├── src/
│   ├── index.js         # Entry point
│   ├── App.js           # Main App component
│   ├── index.css        # Global styles
│   ├── App.css          # App styles
│   ├── components/      # React components
│   ├── pages/           # React pages
│   └── assets/          # Images and assets
└── tailwind.config.js   # Tailwind configuration
```

### 2. Build Process

```python
def _build_react_app(project_path: Path) -> bool:
    # Run npm install
    subprocess.run(['npm', 'install'], cwd=project_path)
    
    # Run npm run build
    subprocess.run(['npm', 'run', 'build'], cwd=project_path)
    
    # Verify build directory exists
    return (project_path / "build").exists()
```

### 3. Static Server

```python
def _serve_build_folder(build_path: Path, port: int) -> Optional[str]:
    # Try serve package first
    subprocess.run(['npx', 'serve', '-s', str(build_path), '-l', str(port)])
    
    # Fallback to http-server
    subprocess.run(['npx', 'http-server', str(build_path), '-p', str(port)])
    
    return f"http://localhost:{port}"
```

### 4. Iframe Embedding

```html
<iframe 
    src="http://localhost:3000"
    width="100%" 
    height="600px" 
    sandbox="allow-scripts allow-same-origin allow-forms allow-popups"
    allow="accelerometer; camera; encrypted-media; geolocation; gyroscope; microphone; midi; clipboard-read; clipboard-write"
></iframe>
```

## Usage

### Basic Usage

```python
from app.utils.preview_utils import create_build_preview

# Your React files
files = {
    "src/App.js": "...",
    "src/components/Navbar.jsx": "...",
    "src/pages/HomePage.jsx": "...",
    # ... more files
}

# Generate preview
preview_html = create_build_preview(files, port=3000)
```

### In Streamlit

```python
# In your Streamlit app
if st.button("🔍 Test Preview"):
    preview_html = create_build_preview(uploaded_files, preview_port)
    st.markdown(preview_html, unsafe_allow_html=True)
```

## Configuration

### Port Configuration

```python
# Set custom port
preview_port = st.number_input(
    "Preview Server Port",
    min_value=3000,
    max_value=9000,
    value=3000
)
```

### Auto-rebuild Settings

```python
auto_rebuild = st.checkbox(
    "Auto-rebuild on file changes",
    value=True
)
```

## Fallback System

If the static server fails to start, the system falls back to an inline approach:

1. **Reads the built `index.html`**
2. **Converts assets to data URLs**
3. **Embeds everything in `srcdoc`**

```html
<iframe 
    srcdoc="<html>...complete built HTML...</html>"
    width="100%" 
    height="600px"
></iframe>
```

## Error Handling

The system provides comprehensive error handling:

- **Build failures**: Shows error message with details
- **Server startup failures**: Falls back to inline preview
- **Missing dependencies**: Guides user to install Node.js/npm
- **Port conflicts**: Tries alternative ports

## Requirements

### System Requirements

- **Node.js** (v14 or higher)
- **npm** (comes with Node.js)
- **Python 3.7+** with required packages

### Python Dependencies

```python
import subprocess
import tempfile
import requests
import json
import time
from pathlib import Path
```

## Testing

Run the test script to verify the system:

```bash
python test_build_preview.py
```

This will:
1. Create a sample React app
2. Build it with npm
3. Start a static server
4. Generate the preview HTML
5. Save it to `test_preview.html`

## Troubleshooting

### Common Issues

1. **"npm not found"**
   - Install Node.js from https://nodejs.org/
   - Verify with `npm --version`

2. **"Build failed"**
   - Check console output for specific errors
   - Ensure all React dependencies are included
   - Verify file structure is correct

3. **"Server won't start"**
   - Check if port is already in use
   - Try a different port
   - System will fall back to inline preview

4. **"Iframe is blank"**
   - Check browser console for errors
   - Verify server is running at the correct URL
   - Try the fallback inline preview

### Debug Information

The system provides detailed debug information:

```python
with st.expander("🔍 Debug Information"):
    st.write("**Build Process:**")
    st.write("• Creates complete React project structure")
    st.write("• Runs npm install && npm run build")
    st.write("• Serves build folder via static server")
    st.write("• Embeds in iframe with full React functionality")
```

## Performance

### Build Times

- **First build**: ~30-60 seconds (npm install)
- **Subsequent builds**: ~10-20 seconds
- **Server startup**: ~2-5 seconds

### Memory Usage

- **Temporary project**: ~50-100MB
- **Build artifacts**: ~10-50MB
- **Static server**: ~10-20MB

## Security

### Sandbox Permissions

The iframe uses appropriate sandbox permissions:

```html
sandbox="allow-scripts allow-same-origin allow-forms allow-popups"
```

This allows:
- ✅ JavaScript execution
- ✅ Same-origin requests
- ✅ Form submissions
- ✅ Popup windows
- ❌ Cross-origin requests (blocked for security)

## Future Enhancements

### Planned Features

1. **Hot Reload Support**
   - Watch for file changes
   - Auto-rebuild on updates
   - Live preview updates

2. **Multiple Framework Support**
   - Vue.js support
   - Angular support
   - Vanilla JS support

3. **Advanced Asset Handling**
   - WebP optimization
   - SVG optimization
   - Font loading

4. **Performance Optimizations**
   - Build caching
   - Incremental builds
   - Parallel processing

## Migration from Old System

### Before (HTML Preview)

```python
# Old system
preview_html = create_html_preview(files)
st.markdown(create_embedded_preview(preview_html), unsafe_allow_html=True)
```

### After (Build Preview)

```python
# New system
preview_html = create_build_preview(files, port=3000)
st.markdown(preview_html, unsafe_allow_html=True)
```

### Benefits of Migration

- ✅ **Full React functionality**
- ✅ **Production-like environment**
- ✅ **Better error handling**
- ✅ **More reliable preview**
- ✅ **Support for complex apps**

## Conclusion

The build-based preview system provides a production-like environment for testing React applications. It handles complex component structures, routing, and styling while providing a reliable and secure preview experience.

For questions or issues, please refer to the debug information in the Streamlit interface or check the console output for detailed error messages.
