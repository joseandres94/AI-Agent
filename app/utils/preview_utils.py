"""
Utility functions for handling web application previews and dynamic modifications.
"""

import base64
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple, Union
import zipfile
import subprocess
import json
import shutil
import os
import http.server
import socketserver
import contextlib
import atexit
import socket
import random
import re
import time
import threading
import requests

# Active servers tracking
_active_servers: List[Tuple[object, str]] = []  # [(server_obj, tmp_dir)]
_PREVIEW_TMP_ROOT = Path(tempfile.gettempdir()) / "ai_agent_preview"

# Conditional import for streamlit
try:
    import streamlit as st
except ImportError:
    # Create a mock st object for when streamlit is not available
    class MockStreamlit:
        def error(self, message):
            print(f"ERROR: {message}")
        
        def info(self, message):
            print(f"INFO: {message}")
        
        def success(self, message):
            print(f"SUCCESS: {message}")
        
        def warning(self, message):
            print(f"WARNING: {message}")
    
    st = MockStreamlit()


@atexit.register
def _cleanup_servers():
    """Apaga servidores y borra carpetas temporales al cerrar Python."""
    for server, tdir in _active_servers:
        with contextlib.suppress(Exception):
            server.shutdown()
            server.server_close()
        shutil.rmtree(tdir, ignore_errors=True)

    # Best-effort cleanup of preview root
    with contextlib.suppress(Exception):
        if _PREVIEW_TMP_ROOT.exists():
            shutil.rmtree(_PREVIEW_TMP_ROOT, ignore_errors=True)

def _safe_encode_content(content: str) -> str:
    """Safely encode content to handle Unicode characters"""
    try:
        # Try to encode as UTF-8 first
        return content.encode('utf-8').decode('utf-8')
    except UnicodeError:
        # Fallback: replace problematic characters
        return content.encode('utf-8', errors='replace').decode('utf-8')




def create_build_preview(files: Dict[str, str]) -> Tuple[str, bool]:
    """
    Build and preview the project.
    Returns a tuple: (preview_html, success_flag)
    success_flag is True only when a functional preview is produced.
    """
    try:
        _prepare_clean_workspace()
        _PREVIEW_TMP_ROOT.mkdir(parents=True, exist_ok=True)
        temp_dir = tempfile.mkdtemp(dir=str(_PREVIEW_TMP_ROOT))            # NO se borra automáticamente
        project_path = Path(temp_dir) / "react-app"
        project_path.mkdir(exist_ok=True)

        _create_react_project_structure(project_path, files)

        if not _build_react_app(project_path):
            # Provide simple preview (degraded). Consider not fully successful.
            return _create_simple_html_preview(files), False

        # Determine build directory (Vite uses 'dist')
        dist_dir = project_path / "dist"
        
        if dist_dir.exists():
            build_path = dist_dir
        else:
            return _create_simple_html_preview(files), False

        # Intentar servidor real primero
        server_url = _serve_build_folder(build_path, port=3000)
        if server_url:
            st.success(f"✅ Servidor de preview: {server_url}")
            return _create_iframe_preview(server_url), True

        # Fallback: inline srcdoc
        st.warning("No se pudo iniciar el servidor, usando vista inline (srcdoc).")
        return _create_srcdoc_preview(build_path), True

    except Exception as e:
        # Handle Unicode encoding issues properly
        try:
            error_msg = str(e)
            # Try to encode as UTF-8 first, fallback to ASCII with replacement
            try:
                error_msg = error_msg.encode('utf-8').decode('utf-8')
            except UnicodeError:
                error_msg = error_msg.encode('ascii', errors='replace').decode('ascii')
            st.error(f"Preview error: {error_msg}")
            return _create_error_preview(f"Preview error: {error_msg}"), False
        except Exception as encoding_error:
            # Final fallback for any encoding issues
            safe_error = f"Preview error: {type(e).__name__}: {str(e)[:100]}"
            st.error(safe_error)
            return _create_error_preview(safe_error), False


def _prepare_clean_workspace(min_free_bytes: int = 50 * 1024 * 1024) -> None:
    """Ensure we have a clean temp area and enough disk space before building.
    - Shutdown any previously running preview servers and delete their temp dirs
    - Clean our preview root directory
    - Check available disk space and raise a friendly error if too low
    """
    _shutdown_all_servers()

    # Clean preview root
    with contextlib.suppress(Exception):
        if _PREVIEW_TMP_ROOT.exists():
            for child in _PREVIEW_TMP_ROOT.iterdir():
                shutil.rmtree(child, ignore_errors=True)

    # Check disk space
    try:
        usage = shutil.disk_usage(tempfile.gettempdir())
        if usage.free < min_free_bytes:
            # try another cleanup pass
            with contextlib.suppress(Exception):
                if _PREVIEW_TMP_ROOT.exists():
                    shutil.rmtree(_PREVIEW_TMP_ROOT, ignore_errors=True)
            usage = shutil.disk_usage(tempfile.gettempdir())
            if usage.free < min_free_bytes:
                raise RuntimeError("Insufficient disk space in TEMP for npm install (ENOSPC). Please free space and retry.")
    except Exception as e:
        # If disk_usage fails, continue; build may still succeed
        if isinstance(e, RuntimeError):
            raise


def _shutdown_all_servers() -> None:
    """Shutdown all active servers and remove their temp directories immediately."""
    global _active_servers
    for server, tdir in _active_servers:
        with contextlib.suppress(Exception):
            server.shutdown()
            server.server_close()
        shutil.rmtree(tdir, ignore_errors=True)
    _active_servers = []


def _detect_project_type(files: Dict[str, str]) -> str:
    """All projects are now Vite-based"""
    return 'vite'


def _create_react_project_structure(project_path: Path, files: Dict[str, str]) -> None:
    """Create a complete Vite React project structure with all necessary files"""
    _create_vite_project_structure(project_path, files)





def _create_vite_project_structure(project_path: Path, files: Dict[str, str]) -> None:
    """Create a Vite project structure"""
    
    # Normalize loosely structured agent outputs to proper Vite paths
    files = _normalize_input_files(files)

    # Use package.json from files if it exists, otherwise create default
    if "package.json" in files:
        package_json_content = files["package.json"]
        # If the provided package.json looks like CRA, replace with Vite default
        try:
            pkg = json.loads(package_json_content)
            scripts = pkg.get("scripts", {})
            is_cra = any("react-scripts" in str(v) for v in scripts.values())
            uses_vite = ("vite" in scripts.get("build", "")) or ("vite" in scripts.get("dev", ""))
            if is_cra or not uses_vite:
                # Fall back to our Vite template but keep name/version/description if present
                pkg_name = pkg.get("name", "vite-react-app")
                pkg_version = pkg.get("version", "0.0.0")
                pkg_desc = pkg.get("description", "")
                package_json = {
                    "name": pkg_name,
                    "private": True,
                    "version": pkg_version,
                    "description": pkg_desc,
                    "type": "module",
                    "scripts": {
                        "dev": "vite",
                        "build": "vite build",
                        "preview": "vite preview"
                    },
                    "dependencies": {
                        "react": "^18.2.0",
                        "react-dom": "^18.2.0",
                        "react-router-dom": "^6.8.0"
                    },
                    "devDependencies": {
                        "@vitejs/plugin-react": "^4.2.1",
                        "vite": "^5.0.8"
                    }
                }
                (project_path / "package.json").write_text(json.dumps(package_json, indent=2, ensure_ascii=False), encoding='utf-8')
            else:
                (project_path / "package.json").write_text(package_json_content, encoding='utf-8')
        except Exception:
            # Any parsing error → use default Vite package.json
            package_json = {
                "name": "vite-react-app",
                "private": True,
                "version": "0.0.0",
                "type": "module",
                "scripts": {
                    "dev": "vite",
                    "build": "vite build",
                    "preview": "vite preview"
                },
                "dependencies": {
                    "react": "^18.2.0",
                    "react-dom": "^18.2.0",
                    "react-router-dom": "^6.8.0"
                },
                "devDependencies": {
                    "@vitejs/plugin-react": "^4.2.1",
                    "vite": "^5.0.8"
                }
            }
            (project_path / "package.json").write_text(json.dumps(package_json, indent=2, ensure_ascii=False), encoding='utf-8')
    else:
        # Create package.json for Vite
        package_json = {
            "name": "vite-react-app",
            "private": True,
            "version": "0.0.0",
            "type": "module",
            "scripts": {
                "dev": "vite",
                "build": "vite build",
                "lint": "eslint . --ext js,jsx --report-unused-disable-directives --max-warnings 0",
                "preview": "vite preview"
            },
            "dependencies": {
                "react": "^18.2.0",
                "react-dom": "^18.2.0",
                "react-router-dom": "^6.8.0"
            },
            "devDependencies": {
                "@types/react": "^18.2.43",
                "@types/react-dom": "^18.2.17",
                "@vitejs/plugin-react": "^4.2.1",
                "eslint": "^8.55.0",
                "eslint-plugin-react": "^7.33.2",
                "eslint-plugin-react-hooks": "^4.6.0",
                "eslint-plugin-react-refresh": "^0.4.5",
                "vite": "^5.0.8"
            }
        }
        
        (project_path / "package.json").write_text(json.dumps(package_json, indent=2, ensure_ascii=False), encoding='utf-8')
    
    # Use index.html from files if it exists, otherwise create default
    if "index.html" in files:
        index_html_content = files["index.html"]
        index_html_content = _ensure_index_html_entry(index_html_content)
        (project_path / "index.html").write_text(index_html_content, encoding='utf-8')
    else:
        # Create index.html for Vite (in root, not public/)
        html_content = """<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Vite + React</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>"""
        
        (project_path / "index.html").write_text(html_content, encoding='utf-8')
    
    # Use vite.config.js from files if it exists, otherwise create default
    if "vite.config.js" in files:
        vite_config_content = files["vite.config.js"]
        (project_path / "vite.config.js").write_text(vite_config_content, encoding='utf-8')
    else:
        # Create vite.config.js
        vite_config = """import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    rollupOptions: {
      // Avoid failing on unresolved optional peer deps (e.g., react-icons/* when not used)
      onwarn(warning, warn) {
        if (warning.code === 'UNRESOLVED_IMPORT') return; // ignore
        warn(warning);
      },
    },
  },
})"""
        
        (project_path / "vite.config.js").write_text(vite_config, encoding='utf-8')

    # Ensure src/main.jsx exists so index.html entry works
    src_dir = project_path / "src"
    src_dir.mkdir(exist_ok=True)
    main_jsx = src_dir / "main.jsx"
    if not main_jsx.exists():
        # Create a minimal main.jsx that mounts App if present, else renders a placeholder
        app_import = "import App from './App.jsx'" if (src_dir / 'App.jsx').exists() else None
        content_lines = [
            "import React from 'react'",
            "import ReactDOM from 'react-dom/client'",
            "import './index.css'",
        ]
        if app_import:
            content_lines.append(app_import)
        content_lines.append("const root = document.getElementById('root')")
        if app_import:
            content_lines.append("ReactDOM.createRoot(root).render(<React.StrictMode><App /></React.StrictMode>)")
        else:
            content_lines.append("ReactDOM.createRoot(root).render(<div style={{padding:20}}>App placeholder</div>)")
        main_jsx.write_text("\n".join(content_lines) + "\n", encoding='utf-8')
    
    # Create .eslintrc.cjs
    eslint_config = """module.exports = {
  root: true,
  env: { browser: true, es2020: true },
  extends: [
    'eslint:recommended',
    'plugin:react-hooks/recommended',
  ],
  ignorePatterns: ['dist', '.eslintrc.cjs'],
  parserOptions: { ecmaVersion: 'latest', sourceType: 'module' },
  settings: { react: { version: '18.2' } },
  plugins: ['react-refresh'],
  rules: {
    'react-refresh/only-export-components': [
      'warn',
      { allowConstantExport: true },
    ],
  },
}"""
    
    (project_path / ".eslintrc.cjs").write_text(eslint_config, encoding='utf-8')
    
    # Create src directory and organize files
    src_dir = project_path / "src"
    src_dir.mkdir(exist_ok=True)
    
    # Create components directory
    components_dir = src_dir / "components"
    components_dir.mkdir(exist_ok=True)
    
    # Create pages directory
    pages_dir = src_dir / "pages"
    pages_dir.mkdir(exist_ok=True)
    
    # Create assets directory
    assets_dir = src_dir / "assets"
    assets_dir.mkdir(exist_ok=True)
    
    # Process and organize files
    for file_path, content in files.items():
        # Skip files we already handled above to avoid overwriting decisions
        if file_path in {"package.json", "index.html", "vite.config.js"}:
            continue
        target_path = project_path / file_path
        
        # Ensure parent directory exists
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Handle different file types
        ext = Path(file_path).suffix.lower()
        if ext in ['.jpg', '.jpeg', '.png', '.gif', '.ico', '.webp', '.svg']:
            if ext == '.svg' and not content.startswith('data:'):
                target_path.write_text(content, encoding='utf-8')  # SVG como XML
            else:
                if content.startswith('data:'):
                    m = re.match(r'data:([^;]+);base64,(.+)', content)
                    if m:
                        target_path.write_bytes(base64.b64decode(m.group(2)))
                else:
                    try:
                        target_path.write_bytes(base64.b64decode(content))
                    except Exception:
                        target_path.write_text(content, encoding='utf-8')  # fallback seguro
        else:
            target_path.write_text(_safe_encode_content(content), encoding='utf-8')
    
    # Create Vite-specific main entry point
    _create_vite_main_entry(project_path, files)
    
    # Create default react.svg and vite.svg in root folder
    react_logo_svg = """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-react"><circle cx="12" cy="12" r="10"/><path d="M12 2a10 10 0 0 1 10 10"/><path d="M12 2a10 10 0 0 0-10 10"/><path d="m12 2 10 10"/><path d="m12 2-10 10"/></svg>"""
    (project_path / "react.svg").write_text(react_logo_svg, encoding='utf-8')
    
    vite_logo_svg = """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-zap"><polygon points="13,2 3,14 12,14 11,22 21,10 12,10 13,2"/></svg>"""
    (project_path / "vite.svg").write_text(vite_logo_svg, encoding='utf-8') # Vite logo in root folder

    # After writing files, ensure any missing local imports are stubbed so build doesn't fail
    _ensure_missing_local_modules(project_path)

    # If vite-plugin-pwa is present, normalize its config to avoid Workbox glob errors
    _fix_vite_pwa_config(project_path)

    # Detect styling/framework usage and ensure required dependencies and configs are present
    _detect_and_inject_dependencies(project_path, files)

    # Ensure top-level providers are present when using Chakra UI or MUI
    _ensure_ui_providers(project_path, files)


def _normalize_input_files(files: Dict[str, str]) -> Dict[str, str]:
    """Normalize loosely structured agent outputs into a Vite-compliant file map.
    - If keys are bare 'jsx', 'json', 'markdown', map them to sensible paths.
    - Ensure root index.html exists if not provided.
    - Ensure src/App.jsx and src/main.jsx exist or are inferred from provided jsx.
    """
    normalized: Dict[str, str] = dict(files)

    # Map generic keys to concrete filenames when present
    if "jsx" in normalized and "src/App.jsx" not in normalized and "src/main.jsx" not in normalized:
        normalized["src/App.jsx"] = normalized.pop("jsx")
    if "json" in normalized and "package.json" not in normalized:
        normalized["package.json"] = normalized.pop("json")
    if "markdown" in normalized and "README.md" not in normalized:
        normalized["README.md"] = normalized.pop("markdown")

    # CRA-style public index → root index.html for Vite
    if "public/index.html" in normalized and "index.html" not in normalized:
        normalized["index.html"] = normalized.pop("public/index.html")

    # Minimal defaults if missing
    if "index.html" not in normalized:
        normalized["index.html"] = """<!doctype html>
<html lang=\"en\">
  <head>
    <meta charset=\"UTF-8\" />
    <link rel=\"icon\" type=\"image/svg+xml\" href=\"/vite.svg\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />
    <title>Vite + React</title>
  </head>
  <body>
    <div id=\"root\"></div>
    <script type=\"module\" src=\"/src/main.jsx\"></script>
  </body>
</html>"""

    # If only App.jsx exists, ensure main.jsx exists (will be created later if absent)
    return normalized


def _ensure_index_html_entry(index_html: str) -> str:
    """Ensure index.html contains the Vite entry script and a root div.
    - Adds <div id="root"></div> if missing
    - Adds <script type="module" src="/src/main.jsx"></script> before </body> if missing
    """
    try:
        html = index_html
        if '<div id="root"' not in html:
            body_pos = html.lower().find('<body')
            end_body_tag = html.lower().find('>', body_pos) if body_pos != -1 else -1
            if end_body_tag != -1:
                html = html[: end_body_tag + 1] + "\n    <div id=\"root\"></div>\n" + html[end_body_tag + 1 :]
            else:
                html = html.replace('</head>', '</head>\n<body>\n  <div id="root"></div>\n</body>')

        if 'src="/src/main.jsx"' not in html and "src='/src/main.jsx'" not in html:
            insert_pos = html.lower().rfind('</body>')
            script = "\n    <script type=\"module\" src=\"/src/main.jsx\"></script>\n"
            if insert_pos != -1:
                html = html[:insert_pos] + script + html[insert_pos:]
            else:
                html = html + script
        return html
    except Exception:
        return index_html


def _ensure_missing_local_modules(project_path: Path) -> None:
    """Scan JS/JSX files for relative imports and create stub modules/files if missing.
    This prevents Vite build failures due to generated code referencing files that
    were not returned by the agent (e.g., "../db" or "./components/Welcome").
    """
    src_dir = project_path / "src"
    if not src_dir.exists():
        return

    import_pattern = re.compile(r"import\s+(?:[^'\"\n]+\s+from\s+)?['\"](\.?\.?/[^'\"\n]+)['\"]")
    side_effect_pattern = re.compile(r"import\s*['\"](\.?\.?/[^'\"\n]+)['\"]")

    js_like_exts = [".jsx", ".js", ".ts", ".tsx"]
    asset_exts = [".svg", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico"]

    def ensure_file(path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.suffix in [".css"]:
            if not path.exists():
                path.write_text("", encoding="utf-8")
            return
        if path.suffix == ".json":
            if not path.exists():
                path.write_text("{}\n", encoding="utf-8")
            return
        if path.suffix in asset_exts:
            if not path.exists():
                # 1x1 transparent PNG for most images; simple SVG for .svg; empty for ico
                if path.suffix == ".svg":
                    path.write_text("<svg xmlns='http://www.w3.org/2000/svg' width='1' height='1'/>", encoding="utf-8")
                else:
                    transparent_png = (
                        b"iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO1+Tn4AAAAASUVORK5CYII="
                    )
                    path.write_bytes(base64.b64decode(transparent_png))
            return
        # JS/TS defaults
        if not path.exists():
            if path.suffix in [".ts", ".tsx"]:
                path.write_text("export default {};\n", encoding="utf-8")
            else:
                # Create a minimal React component if name is PascalCase and .jsx
                if path.suffix == ".jsx" or (path.suffix == "" and path.stem[:1].isupper()):
                    path = path.with_suffix(".jsx")
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text("export default function Stub(){return null;}\n", encoding="utf-8")
                else:
                    path.write_text("export default {};\n", encoding="utf-8")

    def resolve_with_extensions(base: Path) -> Path:
        # If path has extension and exists
        if base.suffix:
            return base
        # Try common extensions
        for ext in js_like_exts + [".css", ".json"] + asset_exts:
            candidate = base.with_suffix(ext)
            if candidate.exists():
                return candidate
        # Directory index
        if base.exists() and base.is_dir():
            for ext in ["index.jsx", "index.js", "index.tsx", "index.ts"]:
                candidate = base / ext
                if candidate.exists():
                    return candidate
        return base

    for js_file in list(src_dir.rglob("*.jsx")) + list(src_dir.rglob("*.js")):
        try:
            content = js_file.read_text(encoding="utf-8")
        except Exception:
            continue
        imports = set()
        for m in import_pattern.finditer(content):
            imports.add(m.group(1))
        for m in side_effect_pattern.finditer(content):
            imports.add(m.group(1))
        for rel in imports:
            if not (rel.startswith("./") or rel.startswith("../")):
                continue
            target = (js_file.parent / rel).resolve()
            target = resolve_with_extensions(target)
            # If no extension and file doesn't exist, decide default ext
            if not target.suffix:
                # Heuristic: component name → jsx, else js
                default_ext = ".jsx" if Path(rel).stem[:1].isupper() else ".js"
                target = target.with_suffix(default_ext)
            if not target.exists():
                ensure_file(target)

def _create_vite_main_entry(project_path: Path, files: Dict[str, str]) -> None:
    """Create Vite-specific main entry point"""
    src_dir = project_path / "src"
    
    # Create main.jsx for Vite (instead of index.js)
    main_jsx_path = src_dir / "main.jsx"
    if not main_jsx_path.exists():
        app_jsx_path = src_dir / "App.jsx"
        app_import = "import App from './App.jsx';" if app_jsx_path.exists() else "import App from './App';"
        
        # Wrap with providers if Chakra UI or MUI are detected in provided files
        lower_joined = "\n".join(files.values()).lower()
        use_chakra = "@chakra-ui/react" in lower_joined
        use_mui = "@mui/material" in lower_joined or "@material-ui/core" in lower_joined

        providers_open = ""
        providers_close = ""
        provider_imports = []
        if use_chakra:
            provider_imports.append("import { ChakraProvider } from '@chakra-ui/react'")
            providers_open += "<ChakraProvider>"
            providers_close = "</ChakraProvider>" + providers_close
        if use_mui:
            provider_imports.append("import { ThemeProvider, createTheme } from '@mui/material/styles'")
            provider_imports.append("const theme = createTheme({});")
            providers_open += "<ThemeProvider theme={theme}>"
            providers_close = "</ThemeProvider>" + providers_close

        provider_imports_text = ("\n".join(provider_imports) + "\n") if provider_imports else ""

        main_jsx_content = f"""import React from 'react'
import ReactDOM from 'react-dom/client'
{app_import}
import './index.css'
{provider_imports_text}

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    {providers_open}<App />{providers_close}
  </React.StrictMode>,
)"""
        main_jsx_path.write_text(main_jsx_content, encoding='utf-8')
    else:
        existing_content = main_jsx_path.read_text(encoding='utf-8')
        app_jsx_path = src_dir / "App.jsx"
        if app_jsx_path.exists() and "import App from './App';" in existing_content:
            existing_content = existing_content.replace("import App from './App';", "import App from './App.jsx';")
        # Ensure Chakra UI or MUI providers if those frameworks are detected later in build phase
        main_jsx_path.write_text(existing_content, encoding='utf-8')
    
    # Create App.jsx if it doesn't exist
    app_jsx_path = src_dir / "App.jsx"
    if not app_jsx_path.exists():
        app_jsx_content = """import { useState } from 'react'
import reactLogo from '/react.svg'
import viteLogo from '/vite.svg'
import './App.css'

function App() {
  const [count, setCount] = useState(0)

  return (
    <>
      <div>
        <a href="https://vitejs.dev" target="_blank">
          <img src={viteLogo} className="logo" alt="Vite logo" />
        </a>
        <a href="https://react.dev" target="_blank">
          <img src={reactLogo} className="logo react" alt="React logo" />
        </a>
      </div>
      <h1>Vite + React</h1>
      <div className="card">
        <button onClick={() => setCount((count) => count + 1)}>
          count is {count}
        </button>
        <p>
          Edit <code>src/App.jsx</code> and save to test HMR
        </p>
      </div>
      <p className="read-the-docs">
        Click on the Vite and React logos to learn more
      </p>
    </>
  )
}

export default App"""
        app_jsx_path.write_text(app_jsx_content, encoding='utf-8')
    
    # Create basic CSS files for Vite
    index_css_path = src_dir / "index.css"
    if not index_css_path.exists():
        index_css_content = """#root {
  max-width: 1280px;
  margin: 0 auto;
  padding: 2rem;
  text-align: center;
}

.logo {
  height: 6em;
  padding: 1.5em;
  will-change: filter;
  transition: filter 300ms;
}
.logo:hover {
  filter: drop-shadow(0 0 2em #646cffaa);
}
.logo.react:hover {
  filter: drop-shadow(0 0 2em #61dafbaa);
}

@keyframes logo-spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

@media (prefers-reduced-motion: no-preference) {
  a:nth-of-type(2) .logo {
    animation: logo-spin infinite 20s linear;
  }
}

.card {
  padding: 2em;
}

.read-the-docs {
  color: #888;
}"""
        index_css_path.write_text(index_css_content, encoding='utf-8')
    
    app_css_path = src_dir / "App.css"
    if not app_css_path.exists():
        app_css_content = """#root {
  max-width: 1280px;
  margin: 0 auto;
  padding: 2rem;
  text-align: center;
}

.logo {
  height: 6em;
  padding: 1.5em;
  will-change: filter;
  transition: filter 300ms;
}
.logo:hover {
  filter: drop-shadow(0 0 2em #646cffaa);
}
.logo.react:hover {
  filter: drop-shadow(0 0 2em #61dafbaa);
}

@keyframes logo-spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

@media (prefers-reduced-motion: no-preference) {
  a:nth-of-type(2) .logo {
    animation: logo-spin infinite 20s linear;
  }
}

.card {
  padding: 2em;
}

.read-the-docs {
  color: #888;
}"""
        app_css_path.write_text(app_css_content, encoding='utf-8')


def _clean_jsx_content(content: str) -> str:
    """Clean JSX content by removing problematic imports and exports"""
    if not content:
        return ""
    
    lines = []
    for line in content.splitlines():
        stripped = line.strip()
        
        # Keep essential React imports
        if (stripped.startswith("import React") or 
            stripped.startswith("import ReactDOM") or
            stripped.startswith("import { React") or
            stripped.startswith("import { ReactDOM")):
            lines.append(line)
            continue
            
        # Skip other import statements and export statements
        if (stripped.startswith("import ") or 
            stripped.startswith("export ") or 
            "export " in stripped or
            stripped == "export default App;" or
            stripped == "export default App" or
            stripped.endswith("export default App")):
            continue
            
        lines.append(line)
    return "\n".join(lines)


def _build_react_app(project_path: Path) -> bool:
    """Run npm install and npm run build"""
    try:
        # Try to find npm in common locations
        npm_paths = [
            'npm',  # Try direct command first
            'C:\\Program Files\\nodejs\\npm.cmd',  # Windows default
            'C:\\Program Files\\nodejs\\npm.exe',  # Windows alternative
        ]
        
        npm_cmd = None
        for path in npm_paths:
            try:
                result = subprocess.run([path, '--version'], capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    npm_cmd = path
                    break
            except:
                continue
        
        if not npm_cmd:
            st.error("npm is not available. Please install Node.js and npm.")
            return False
        
        # Run npm install (prefer ci if lockfile is present)
        install_cmd = [npm_cmd, 'ci'] if (project_path / 'package-lock.json').exists() else [npm_cmd, 'install']
        st.info("Installing dependencies... (this may take a few minutes)")
        result = subprocess.run(
            install_cmd,
            cwd=project_path,
            capture_output=True,
            text=True,
            timeout=900  # 15 minutes timeout
        )
        
        if result.returncode != 0:
            error_msg = f"npm install failed: {result.stderr}"
            if not result.stderr.strip():
                error_msg = f"npm install failed with return code {result.returncode}. stdout: {result.stdout}"
            st.error(error_msg)
            st.error(f"npm install stdout: {result.stdout}")
            st.error(f"npm install stderr: {result.stderr}")
            return False

        # Conditionally install dev deps only if referenced in package.json
        pkg = json.loads((project_path / 'package.json').read_text(encoding='utf-8'))
        dev_deps = pkg.get('devDependencies', {})
        deps_to_install: List[str] = []
        for name, ver in dev_deps.items():
            node_modules_path = project_path / 'node_modules' / name
            if not node_modules_path.exists():
                deps_to_install.extend([f"{name}@{ver}"])
        if deps_to_install:
            st.info("Installing devDependencies (detected in package.json)...")
            result = subprocess.run(
                [npm_cmd, 'install', '-D'] + deps_to_install,
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=600
            )
            if result.returncode != 0:
                st.error("Dev dependency installation failed.")
                st.error(f"stdout: {result.stdout}")
                st.error(f"stderr: {result.stderr}")
                return False
        
        # Run npm run build
        st.info("Building React application... (this may take 1-2 minutes)")
        result = subprocess.run(
            [npm_cmd, 'run', 'build'],
            cwd=project_path,
            capture_output=True,
            text=True,
            timeout=600  # 10 minutes timeout
        )
        
        if result.returncode != 0:
            error_msg = f"Build failed: {result.stderr}"
            if not result.stderr.strip():
                error_msg = f"Build failed with return code {result.returncode}. stdout: {result.stdout}"
            st.error(error_msg)
            # Log additional details for debugging
            st.error(f"npm run build stdout: {result.stdout}")
            st.error(f"npm run build stderr: {result.stderr}")
            return False
        
        # Check if build directory exists (CRA) or dist directory (Vite)
        build_dir = project_path / "build"
        dist_dir = project_path / "dist"
        
        if build_dir.exists():
            st.success("React application built successfully! Using inline preview.")
            return True
        elif dist_dir.exists():
            st.success("Vite application built successfully! Using inline preview.")
            return True
        else:
            st.error("Build directory not found (expected 'build' for CRA or 'dist' for Vite)")
            return False
        
    except subprocess.TimeoutExpired:
        st.error("Build timed out")
        return False
    except Exception as e:
        st.error(f"Build error: {str(e)}")
        return False


def _serve_build_folder(build_path: Path, port: Union[int, None] = None) -> Optional[str]:
    """
    Lanza un servidor estático Python con fallback SPA (index.html).
    Devuelve la URL o None si falla.
    """

    if port is None:
        port = 3000  # Always use port 3000 as default

    class SPAHandler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(build_path), **kwargs)
        
        def send_head(self):
            path = Path(self.translate_path(self.path))
            if path.is_file():
                return super().send_head()
            self.path = "/index.html"
            return super().send_head()
        
        def log_message(self, *args):
            pass  # silencia logs

    try:
        server = socketserver.TCPServer(("localhost", port), SPAHandler)
    except OSError:
        return None

    threading.Thread(target=server.serve_forever, daemon=True).start()

    for _ in range(50):            # espera ~5 s
        try:
            if requests.get(f"http://localhost:{port}", timeout=0.2).status_code == 200:
                _active_servers.append((server, str(build_path.parent.parent)))
                return f"http://localhost:{port}"
        except requests.exceptions.RequestException:
            time.sleep(0.1)

    server.shutdown()
    server.server_close()
    return None


def _create_iframe_preview(server_url: str) -> str:
    """Create iframe preview pointing to the server URL.
    Note: no sandbox to avoid blocking module scripts/SPAs inside the iframe.
    """
    return f"""
    <div class="preview-container">
        <h3>Live Preview (Build Server)</h3>
        <iframe 
            src="{server_url}"
            width="100%" 
            height="600px" 
            style="border: 1px solid #ddd; border-radius: 5px; background: white;"
            allow="accelerometer; camera; encrypted-media; geolocation; gyroscope; microphone; midi; clipboard-read; clipboard-write"
            loading="lazy"
            referrerpolicy="no-referrer"
        ></iframe>
        <p style="margin-top: 10px; font-size: 12px; color: #666;">
            Server running at: <a href="{server_url}" target="_blank">{server_url}</a>
        </p>
    </div>
    """


def _create_srcdoc_preview(build_path: Path) -> str:
    """Create srcdoc preview by inlining the build/index.html"""
    try:
        index_html_path = build_path / "index.html"
        if not index_html_path.exists():
            return _create_error_preview("Build index.html not found")
        
        # Read the index.html
        index_html = index_html_path.read_text(encoding='utf-8')
        
        # Rewrite asset URLs to be data URLs for srcdoc compatibility
        index_html = _rewrite_asset_urls(index_html, build_path)
        
        # Use the original HTML but add minimal isolation scripts
        # Extract the head content and body content properly
        head_start = index_html.find('<head>')
        head_end = index_html.find('</head>')
        body_start = index_html.find('<body>')
        body_end = index_html.find('</body>')
        
        if head_start != -1 and head_end != -1 and body_start != -1 and body_end != -1:
            head_content = index_html[head_start + 6:head_end]
            body_content = index_html[body_start + 6:body_end]
            
            # Add minimal isolation and security headers
            isolation_meta = """
     <meta http-equiv="X-Frame-Options" content="SAMEORIGIN" />
     <meta http-equiv="Content-Security-Policy" content="default-src 'self' 'unsafe-inline' 'unsafe-eval' data: blob:;" />
     <style>
         body {
             margin: 0;
             padding: 0;
             font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
         }
         #root {
             min-height: 100vh;
         }
         /* Ensure content is visible */
         .main-content {
             flex: 1;
             min-height: 400px;
             padding: 20px;
         }
         /* Basic styles to ensure content is visible */
         * {
             box-sizing: border-box;
         }
         /* Ensure all content is visible */
         .App {
             min-height: 100vh;
             display: flex;
             flex-direction: column;
         }
         /* Make sure navigation works */
         nav a {
             cursor: pointer;
         }
     </style>"""
            
            isolation_script = """
     <script>
         // Prevent navigation to parent page
         window.addEventListener('beforeunload', function(e) {
             e.preventDefault();
             e.returnValue = '';
         });
         
         // Prevent any attempts to access parent window
         if (window.parent !== window) {
             try {
                 window.parent.postMessage('preview-loaded', '*');
             } catch (e) {
                 // Ignore cross-origin errors
             }
         }
         
         // Allow React Router navigation but prevent external navigation
         window.addEventListener('click', function(e) {
             if (e.target.tagName === 'A' && e.target.href) {
                 // Allow internal navigation (React Router)
                 if (e.target.href.startsWith('#') || e.target.href.startsWith('/')) {
                     return true;
                 }
                 // Prevent external navigation
                 e.preventDefault();
                 return false;
             }
         });
         
         // Simple React app loading check
         window.addEventListener('load', function() {
             console.log('Page loaded, checking React app...');
             
             // Simple check for React app
             setTimeout(function() {
                 const root = document.getElementById('root');
                 if (root) {
                     console.log('Root element found, content length:', root.children.length);
                     
                     // Check for specific content elements
                     const nav = document.querySelector('nav');
                     const heroSection = document.querySelector('h1');
                     const mainContent = document.querySelector('main');
                     
                     if (nav) console.log('Navigation found');
                     if (heroSection) console.log('Hero section found');
                     if (mainContent) console.log('Main content found');
                 }
             }, 1000);
         });
         
         // Handle React Router navigation
         window.addEventListener('popstate', function() {
             console.log('Navigation detected:', window.location.pathname);
         });
     </script>"""
            
            index_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    {isolation_meta}
    {head_content}
</head>
<body>
    {body_content}
    {isolation_script}
</body>
</html>"""
        else:
            # Fallback: use the original HTML with basic isolation
            index_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <meta http-equiv="X-Frame-Options" content="SAMEORIGIN" />
    <title>React App Preview</title>
</head>
<body>
    <div id="root"></div>
    <script>
        // Prevent navigation to parent page
        window.addEventListener('beforeunload', function(e) {{
            e.preventDefault();
            e.returnValue = '';
        }});
    </script>
    {index_html}
        </body>
</html>"""
        
        # Use data URL approach to avoid escaping issues
        html_bytes = index_html.encode('utf-8')
        html_base64 = base64.b64encode(html_bytes).decode('utf-8')
        data_url = f"data:text/html;base64,{html_base64}"
        
        return f"""
         <div class="preview-container">
             <h3>Live Preview (Build Success)</h3>
             <iframe 
                 src="{data_url}"
                 width="100%" 
                 height="600px" 
                 style="border: 1px solid #ddd; border-radius: 5px; background: white; overflow: hidden;"
                 sandbox="allow-scripts allow-same-origin allow-forms allow-popups allow-top-navigation"
                 allow="accelerometer; camera; encrypted-media; geolocation; gyroscope; microphone; midi; clipboard-read; clipboard-write"
                 loading="lazy"
                 referrerpolicy="no-referrer"
                 name="react-preview-frame"
                 onload="this.style.height='600px';"
             ></iframe>
             <p style="margin-top: 10px; font-size: 12px; color: #666;">
                 ✅ Build successful! Using inline HTML preview (no external server required)
             </p>
             <div style="margin-top: 10px; padding: 10px; background: #f8f9fa; border-radius: 5px; font-size: 12px;">
                 <strong>Debug Info:</strong> If the preview appears incomplete, try refreshing the page or wait a few seconds for the React app to fully load.
             </div>
         </div>
         """
        
    except Exception as e:
        return _create_error_preview(f"Failed to create srcdoc preview: {str(e)}")


def _rewrite_asset_urls(html_content: str, build_path: Path) -> str:
    """Rewrite asset URLs in HTML to be data URLs or relative paths"""
    import re
    
    # Find all asset references (including those with hashes)
    asset_pattern = r'(src|href)=["\']([^"\']*\.(js|css|png|jpg|jpeg|gif|svg|ico|webp))["\']'
    
    def replace_asset(match):
        attr, url, ext = match.groups()
        
        # Skip external URLs
        if url.startswith('http'):
            return match.group(0)
        
        # Try to find the asset file
        asset_path = build_path / url.lstrip('/')
        if asset_path.exists():
            try:
                if ext in ['png', 'jpg', 'jpeg', 'gif', 'svg', 'ico', 'webp']:
                    # Convert images to data URLs
                    file_bytes = asset_path.read_bytes()
                    mime_type = f"image/{ext}" if ext != 'svg' else "image/svg+xml"
                    if ext == 'ico':
                        mime_type = "image/x-icon"
                    
                    data_url = f"data:{mime_type};base64,{base64.b64encode(file_bytes).decode()}"
                    return f'{attr}="{data_url}"'
                else:
                    # For JS/CSS, convert to data URLs for srcdoc compatibility
                    file_bytes = asset_path.read_bytes()
                    mime_type = "text/javascript" if ext == "js" else "text/css"
                    data_url = f"data:{mime_type};base64,{base64.b64encode(file_bytes).decode()}"
                    return f'{attr}="{data_url}"'
            except Exception:
                return match.group(0)
        
        return match.group(0)
    
    # Also handle static folder references
    static_pattern = r'(src|href)=["\'](/static/[^"\']*)["\']'
    
    def replace_static(match):
        attr, url = match.groups()
        
        # Try to find the static file
        static_path = build_path / url.lstrip('/')
        if static_path.exists():
            try:
                file_bytes = static_path.read_bytes()
                # Determine MIME type based on file extension
                ext = static_path.suffix.lower()
                if ext in ['.js']:
                    mime_type = "text/javascript"
                elif ext in ['.css']:
                    mime_type = "text/css"
                elif ext in ['.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.webp']:
                    mime_type = f"image/{ext[1:]}" if ext != '.svg' else "image/svg+xml"
                    if ext == '.ico':
                        mime_type = "image/x-icon"
                else:
                    mime_type = "application/octet-stream"
                
                data_url = f"data:{mime_type};base64,{base64.b64encode(file_bytes).decode()}"
                return f'{attr}="{data_url}"'
            except Exception:
                return match.group(0)
        
        return match.group(0)
    
    # Apply both patterns
    html_content = re.sub(asset_pattern, replace_asset, html_content)
    html_content = re.sub(static_pattern, replace_static, html_content)
    
    return html_content


def _scan_style_and_packages_from_files(files: Dict[str, str]) -> Dict[str, Any]:
    """Detect which styling frameworks and npm packages appear to be required based on file contents.
    Looks for Tailwind, Bootstrap, Material-UI (MUI), Chakra UI, react-icons, and vite-plugin-pwa usage.
    """
    joined = "\n".join(files.values()) if files else ""
    lower = joined.lower()

    uses_tailwind = (
        "tailwind" in lower or "@tailwind" in lower or any(k.endswith("tailwind.config.js") for k in files.keys())
    )
    uses_bootstrap = (
        "bootstrap" in lower or "bootstrap.min.css" in lower or any(
            re.search(r'class(?:Name)?=\"[^\"]*(?:container|row|col-\d|btn|btn-)[^\"]*\"', v, re.I)
            for v in files.values()
        )
    )
    uses_mui = ("@mui/material" in lower) or ("@material-ui/core" in lower)
    uses_chakra = ("@chakra-ui/react" in lower)
    uses_chakra_icons = ("@chakra-ui/icons" in lower)
    uses_react_icons = ("react-icons/" in lower) or ("react-icons" in lower)
    uses_vite_pwa = ("vite-plugin-pwa" in lower) or ("vitepwa" in lower)

    return {
        "tailwind": uses_tailwind,
        "bootstrap": uses_bootstrap,
        "mui": uses_mui,
        "chakra": uses_chakra,
        "chakra_icons": uses_chakra_icons,
        "react_icons": uses_react_icons,
        "vite_pwa": uses_vite_pwa,
    }


def _read_json(path: Path) -> Dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _write_json(path: Path, data: Dict[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def _ensure_tailwind_setup(project_path: Path) -> None:
    """Ensure Tailwind CSS config and directives exist in the Vite React project."""
    postcss_path = project_path / "postcss.config.js"
    if not postcss_path.exists():
        postcss_path.write_text(
            """export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
""",
            encoding="utf-8",
        )

    tailwind_path = project_path / "tailwind.config.js"
    if not tailwind_path.exists():
        tailwind_path.write_text(
            """/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './index.html',
    './src/**/*.{js,jsx,ts,tsx}',
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
""",
            encoding="utf-8",
        )

    src_dir = project_path / "src"
    src_dir.mkdir(parents=True, exist_ok=True)
    index_css = src_dir / "index.css"
    css_text = index_css.read_text(encoding="utf-8") if index_css.exists() else ""
    if "@tailwind base;" not in css_text:
        index_css.write_text(
            "@tailwind base;\n@tailwind components;\n@tailwind utilities;\n\n" + css_text,
            encoding="utf-8",
        )


def _ensure_bootstrap_import(project_path: Path) -> None:
    """Ensure Bootstrap stylesheet is imported via JS or HTML for class-based styling."""
    src_dir = project_path / "src"
    main_path = src_dir / "main.jsx"
    if main_path.exists():
        content = main_path.read_text(encoding="utf-8")
        if "bootstrap/dist/css/bootstrap.min.css" not in content:
            main_path.write_text(
                "import 'bootstrap/dist/css/bootstrap.min.css';\n" + content,
                encoding="utf-8",
            )
    else:
        index_html = project_path / "index.html"
        if index_html.exists():
            html = index_html.read_text(encoding="utf-8")
            if "bootstrap.min.css" not in html:
                head_end = html.find("</head>")
                link_tag = (
                    "\n<link rel=\"stylesheet\" href=\"https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css\" integrity=\"sha384-QWTL+7GC9V8N0QFj6Y7Ge3X1iGWejR5Gnx4WmZkS2Qqf8iJYx6S2n9bN9+8b7Ajp\" crossorigin=\"anonymous\">\n"
                )
                if head_end != -1:
                    index_html.write_text(
                        html[:head_end] + link_tag + html[head_end:], encoding="utf-8"
                    )


def _merge_dependencies(pkg: Dict[str, Any], deps: Dict[str, str], dev_deps: Dict[str, str]) -> Dict[str, Any]:
    pkg.setdefault("dependencies", {})
    pkg.setdefault("devDependencies", {})
    for k, v in deps.items():
        pkg["dependencies"].setdefault(k, v)
    for k, v in dev_deps.items():
        pkg["devDependencies"].setdefault(k, v)
    return pkg


def _detect_and_inject_dependencies(project_path: Path, files: Dict[str, str]) -> None:
    """Update package.json and project files based on detected frameworks/packages.
    - Adds Tailwind, Bootstrap, MUI, Chakra UI, react-icons to dependencies as needed
    - Leaves CSS3 as-is (no extra deps)
    - If vite-plugin-pwa is detected, ensures it's listed (fix config separately)
    """
    detection = _scan_style_and_packages_from_files(files)
    pkg_path = project_path / "package.json"
    pkg = _read_json(pkg_path)
    if not pkg:
        return

    deps: Dict[str, str] = {}
    dev_deps: Dict[str, str] = {}

    cfg_path = project_path / "vite.config.js"
    try:
        vite_cfg_txt = cfg_path.read_text(encoding="utf-8")
    except Exception:
        vite_cfg_txt = ""

    if "vite-plugin-pwa" in vite_cfg_txt:
        dev_deps.setdefault("vite-plugin-pwa", "^0.20.5")

    if detection["tailwind"]:
        dev_deps.update({
            "tailwindcss": "^3.4.7",
            "postcss": "^8.4.41",
            "autoprefixer": "^10.4.20",
        })
    if detection["bootstrap"]:
        deps.update({"bootstrap": "^5.3.3"})
    if detection["mui"]:
        deps.update({
            "@mui/material": "^5.15.20",
            "@mui/icons-material": "^5.15.20",
            "@emotion/react": "^11.11.4",
            "@emotion/styled": "^11.11.5",
        })
    if detection["chakra"]:
        deps.update({
            "@chakra-ui/react": "^2.8.2",
            "@emotion/react": "^11.11.4",
            "@emotion/styled": "^11.11.5",
            "framer-motion": "^11.0.0",
        })
    if detection["chakra_icons"]:
        deps.update({"@chakra-ui/icons": "^2.1.0"})
    if detection["react_icons"]:
        deps.update({"react-icons": "^5.2.1"})
    if detection["vite_pwa"]:
        dev_deps.update({"vite-plugin-pwa": "^0.20.5"})

    pkg = _merge_dependencies(pkg, deps, dev_deps)
    _write_json(pkg_path, pkg)

    # Ensure file changes
    if detection["tailwind"]:
        _ensure_tailwind_setup(project_path)
    if detection["bootstrap"]:
        _ensure_bootstrap_import(project_path)


def _ensure_ui_providers(project_path: Path, files: Dict[str, str]) -> None:
    """If Chakra UI or MUI are referenced by files, wrap the app with providers in main.jsx."""
    detection = _scan_style_and_packages_from_files(files)
    if not (detection["chakra"] or detection["mui"]):
        return
    src_dir = project_path / "src"
    main_jsx_path = src_dir / "main.jsx"
    if not main_jsx_path.exists():
        return
    text = main_jsx_path.read_text(encoding='utf-8')

    changed = False
    if detection["chakra"] and "ChakraProvider" not in text:
        # add import and wrap
        if "@chakra-ui/react" not in text:
            text = "import { ChakraProvider } from '@chakra-ui/react'\n" + text
        # wrap <App />
        text = re.sub(r"(<React\.StrictMode>\s*)(<App \/>)(\s*<\/React\.StrictMode>)",
                      r"\1<ChakraProvider>\2</ChakraProvider>\3", text, flags=re.S)
        if "ChakraProvider" in text:
            changed = True

    if detection["mui"] and "ThemeProvider" not in text:
        if "@mui/material" not in text:
            text = "import { ThemeProvider, createTheme } from '@mui/material/styles'\n" + text
            text = "const theme = createTheme({});\n" + text
        else:
            if "createTheme" not in text:
                text = "import { ThemeProvider, createTheme } from '@mui/material/styles'\n" + text
                text = "const theme = createTheme({});\n" + text
        # wrap
        text = re.sub(r"(<React\.StrictMode>\s*)(<App \/>)(\s*<\/React\.StrictMode>)",
                      r"\1<ThemeProvider theme={theme}>\2</ThemeProvider>\3", text, flags=re.S)
        if "ThemeProvider" in text:
            changed = True

    if changed:
        main_jsx_path.write_text(text, encoding='utf-8')


def _fix_vite_pwa_config(project_path: Path) -> None:
    vite_config_path = project_path / "vite.config.js"
    if not vite_config_path.exists():
        return
    try:
        text = vite_config_path.read_text(encoding="utf-8")
    except Exception:
        return

    has_import = ("from 'vite-plugin-pwa'" in text) or ('from "vite-plugin-pwa"' in text)
    has_call = re.search(r"\bVitePWA\s*\(", text) is not None

    # A. Import si falta
    if has_call:
        if not has_import:
            if "import react from '@vitejs/plugin-react'" in text:  
                text = re.sub(
                    r"import\s+react\s+from\s+['\"]@vitejs/plugin-react['\"];?",
                    "import react from '@vitejs/plugin-react'\nimport { VitePWA } from 'vite-plugin-pwa'",
                    text, count=1
                )
            else:
                text = "import { VitePWA } from 'vite-plugin-pwa'\n" + text
            vite_config_path.write_text(text, encoding="utf-8")
        return

    # B. Si no hay llamada, inyecta sin workbox (generateSW por defecto)
    if not has_call:
        def inject(m):
            inside = m.group(2).strip()
            injected = "VitePWA({ strategies: 'generateSW', registerType: 'autoUpdate' })"
            new_inside = injected + (", " if inside else "") + inside
            return m.group(1) + new_inside + m.group(3)

        plugins_re = re.compile(r"(plugins\s*:\s*\[)([\s\S]*?)(\])")
        text, n = plugins_re.subn(inject, text, count=1)
        if n == 0:
            text = re.sub(
                r"export\s+default\s+defineConfig\(\s*\{",
                "export default defineConfig({\n  plugins: [react(), VitePWA({ strategies: 'generateSW', registerType: 'autoUpdate' })],",
                text, count=1
            )
        vite_config_path.write_text(text, encoding="utf-8")
        return

def _create_simple_html_preview(files: Dict[str, str]) -> str:
    """Create a simple HTML preview when build fails"""
    try:
        # Create the files list for the JavaScript
        files_list = list(files.keys())
        
        # Try to create a more functional preview by bundling the main components
        try:
            # Find the main App component
            app_content = None
            
            for file_path, content in files.items():
                if file_path.endswith('App.jsx') or file_path.endswith('App.js'):
                    app_content = _clean_jsx_content(content)
            
            # Create a basic HTML structure with bundled components
            html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>React App Preview</title>
    <script src="https://unpkg.com/react@18/umd/react.development.js"></script>
    <script src="https://unpkg.com/react-dom@18/umd/react-dom.development.js"></script>
    <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body { margin: 0; padding: 20px; font-family: Arial, sans-serif; }
        .preview-container { max-width: 800px; margin: 0 auto; }
        .file-list { background: #f5f5f5; padding: 15px; border-radius: 5px; margin: 20px 0; }
        .file-item { margin: 5px 0; padding: 5px; background: white; border-radius: 3px; }
    </style>
</head>
<body>
    <div class="preview-container">
        <h1>React App Preview (Simple Mode)</h1>
        <p>Build process failed, showing file structure and basic preview.</p>
        
        <div class="file-list">
            <h3>Files in project:</h3>
            <div id="file-list"></div>
        </div>
        
        <div id="app-preview">
            <h2>App Preview</h2>
            <div id="root"></div>
        </div>
    </div>
    
    <script type="text/babel">
        // Bundled React components
        {app_content if app_content else '// App component not found'}
        
        // Simple React component to show the app structure
        function AppPreview() {{
            const files = {files_list};
            
            return (
                <div className="p-4">
                    <h2 className="text-2xl font-bold mb-4">Project Structure</h2>
                    <div className="space-y-2">
                        {files.map((file, index) => (
                            <div key={index} className="p-2 bg-gray-100 rounded">
                                <strong>{file}</strong>
                            </div>
                        ))}
                    </div>
                </div>
            );
        }}
        
        // Try to render the actual App component, fallback to AppPreview
        try {{
            ReactDOM.render(<App />, document.getElementById('root'));
        }} catch (e) {{
            ReactDOM.render(<AppPreview />, document.getElementById('root'));
        }}
    </script>
</body>
</html>"""
            
            # Replace the placeholders in the HTML
            html_content = html_content.replace('{files_list}', str(files_list))
            if app_content:
                html_content = html_content.replace('{app_content if app_content else \'// App component not found\'}', app_content)
            else:
                html_content = html_content.replace('{app_content if app_content else \'// App component not found\'}', '// App component not found')
                
        except Exception as e:
            # Fallback to simple file list if bundling fails
            html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>React App Preview</title>
    <script src="https://unpkg.com/react@18/umd/react.development.js"></script>
    <script src="https://unpkg.com/react-dom@18/umd/react-dom.development.js"></script>
    <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body { margin: 0; padding: 20px; font-family: Arial, sans-serif; }
        .preview-container { max-width: 800px; margin: 0 auto; }
        .file-list { background: #f5f5f5; padding: 15px; border-radius: 5px; margin: 20px 0; }
        .file-item { margin: 5px 0; padding: 5px; background: white; border-radius: 3px; }
    </style>
</head>
<body>
    <div class="preview-container">
        <h1>React App Preview (Simple Mode)</h1>
        <p>Build process failed, showing file structure instead.</p>
        
        <div class="file-list">
            <h3>Files in project:</h3>
            <div id="file-list"></div>
        </div>
        
        <div id="app-preview">
            <h2>App Preview</h2>
            <div id="root"></div>
        </div>
    </div>
    
    <script type="text/babel">
        // Simple React component to show the app structure
        function AppPreview() {{
            const files = {files_list};
            
            return (
                <div className="p-4">
                    <h2 className="text-2xl font-bold mb-4">Project Structure</h2>
                    <div className="space-y-2">
                        {files.map((file, index) => (
                            <div key={index} className="p-2 bg-gray-100 rounded">
                                <strong>{file}</strong>
                            </div>
                        ))}
                    </div>
                </div>
            );
        }}
        
        ReactDOM.render(<AppPreview />, document.getElementById('root'));
    </script>
</body>
</html>"""
            
            # Replace the placeholder in the HTML
            html_content = html_content.replace('{files_list}', str(files_list))
        
        return f"""
        <div class="preview-container">
            <h3>Simple HTML Preview</h3>
            <div style="padding: 15px; background: #f8f9fa; border: 1px solid #dee2e6; border-radius: 5px; margin-bottom: 15px;">
                <p><strong>Build Status:</strong> Build process failed or timed out</p>
                <p><strong>Reason:</strong> npm install/build takes 2-3 minutes. You can:</p>
                <ul style="margin: 10px 0; padding-left: 20px;">
                    <li>Wait for the full build process to complete (recommended)</li>
                    <li>Use this simple preview to see the project structure</li>
                    <li>Download the files and build manually with <code>npm install && npm run build</code></li>
                </ul>
            </div>
            <iframe 
                srcdoc="{html_content.replace('"', '&quot;')}"
                width="100%" 
                height="600px" 
                style="border: 1px solid #ddd; border-radius: 5px; background: white;"
                sandbox="allow-scripts allow-same-origin"
            ></iframe>
            <p style="margin-top: 10px; font-size: 12px; color: #666;">
                Simple preview showing project structure (full build process failed or timed out)
            </p>
        </div>
        """
        
    except Exception as e:
        return _create_error_preview(f"Failed to create simple preview: {str(e)}")


def _create_error_preview(error_message: str) -> str:
    """Create an error preview"""
    # Ensure error message is ASCII-safe
    safe_error = error_message.encode('ascii', errors='replace').decode('ascii')
    return f"""
    <div class="preview-container">
        <h3>Preview Error</h3>
        <div style="padding: 20px; background: #f8f9fa; border: 1px solid #dee2e6; border-radius: 5px;">
            <p style="color: #dc3545; margin: 0;">{safe_error}</p>
        </div>
    </div>
    """


def create_zip_download(files: Dict[str, str], filename: str = "web_app.zip") -> bytes:
    """Create a ZIP file containing all the uploaded files"""
    import io
    
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for file_path, content in files.items():
            # Ensure the file path uses forward slashes for ZIP compatibility
            zip_path = file_path.replace('\\', '/')
            zip_file.writestr(zip_path, content)
    
    zip_buffer.seek(0)
    return zip_buffer.getvalue()


def extract_metadata_from_files(files: Dict[str, str]) -> Dict[str, Any]:
    """Extract metadata from uploaded files"""
    metadata = {
        'total_files': len(files),
        'has_html': False,
        'has_css': False,
        'has_js': False,
        'has_jsx': False,
        'has_vite': False,
        'frameworks_detected': [],
        'structure_type': 'unknown'
    }
    
    # Analyze file types
    html_files = []
    css_files = []
    js_files = []
    jsx_files = []
    config_files = []
    
    for file_path, content in files.items():
        file_lower = file_path.lower()
        
        if file_lower.endswith('.html'):
            html_files.append(file_path)
            metadata['has_html'] = True
        elif file_lower.endswith('.css'):
            css_files.append(file_path)
            metadata['has_css'] = True
        elif file_lower.endswith('.js') and not file_lower.endswith('.jsx'):
            js_files.append(file_path)
            metadata['has_js'] = True
        elif file_lower.endswith('.jsx'):
            jsx_files.append(file_path)
            metadata['has_jsx'] = True
        elif any(file_lower.endswith(ext) for ext in ['.json', '.config.js', '.config.ts']):
            config_files.append(file_path)
    
    # Detect frameworks and build tools
    for file_path, content in files.items():
        content_lower = content.lower()
        file_lower = file_path.lower()
        
        # Detect Vite
        if ('vite.config.js' in file_lower or 
            'vite.config.ts' in file_lower or 
            'vite' in content_lower):
            metadata['has_vite'] = True
            if 'Vite' not in metadata['frameworks_detected']:
                metadata['frameworks_detected'].append('Vite')
        
        if 'react' in content_lower or 'jsx' in content_lower:
            if 'React' not in metadata['frameworks_detected']:
                metadata['frameworks_detected'].append('React')
        
        if 'vue' in content_lower:
            if 'Vue.js' not in metadata['frameworks_detected']:
                metadata['frameworks_detected'].append('Vue.js')
        
        if 'angular' in content_lower:
            if 'Angular' not in metadata['frameworks_detected']:
                metadata['frameworks_detected'].append('Angular')
        
        if 'tailwind' in content_lower or 'tailwindcss' in content_lower:
            if 'Tailwind CSS' not in metadata['frameworks_detected']:
                metadata['frameworks_detected'].append('Tailwind CSS')
        
        if 'bootstrap' in content_lower:
            if 'Bootstrap' not in metadata['frameworks_detected']:
                metadata['frameworks_detected'].append('Bootstrap')
    
    # Determine structure type
    if metadata['has_vite'] and metadata['has_jsx']:
        metadata['structure_type'] = 'vite_react'
    elif metadata['has_vite']:
        metadata['structure_type'] = 'vite_app'
    elif metadata['has_jsx'] and len(jsx_files) > 2:
        metadata['structure_type'] = 'complex_react'
    elif metadata['has_jsx']:
        metadata['structure_type'] = 'react_app'
    elif metadata['has_js']:
        metadata['structure_type'] = 'vanilla_js'
    elif metadata['has_html']:
        metadata['structure_type'] = 'static_html'
    
    # Add file counts
    metadata['html_files'] = html_files
    metadata['css_files'] = css_files
    metadata['js_files'] = js_files
    metadata['jsx_files'] = jsx_files
    metadata['config_files'] = config_files
    
    return metadata 