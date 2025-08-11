import openai
import os
import logging
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
import re

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class AIService:
    """Service for handling AI model interactions"""
    
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.default_model = os.getenv("OPENAI_MODEL", "gpt-5-2025-08-07")
        # Hold last raw response for debugging via API
        self.last_raw_response: Optional[Any] = None
        
        if not self.api_key:
            logger.warning("OpenAI API key not found. AI functionality will be limited.")
        
        # Initialize OpenAI client
        if self.api_key:
            openai.api_key = self.api_key
            self.client = openai.OpenAI(api_key=self.api_key)
        else:
            self.client = None
    
    async def check_availability(self) -> str:
        """Check if the AI service is available"""
        if not self.client:
            return "unavailable"
        
        try:
            # Simple test call to check API availability
            response = self.client.chat.completions.create(
                model="gpt-5-nano-2025-08-07",
                messages=[{"role": "user", "content": "Hello"}],
                #max_completion_tokens=5
            )
            self.last_raw_response = self._safe_dump_response(response)
            return "available"
        except Exception as e:
            logger.error(f"AI service check failed: {str(e)}")
            return "error"
    
    async def get_available_models(self) -> List[Dict[str, Any]]:
        """Get available AI models"""
        models = [
            {
                "name": "gpt-5-2025-08-07",
                "description": "Latest and most advanced GPT-5 model with improved reasoning, speed, and cost efficiency",
                "capabilities": ["Code generation", "Text analysis", "Creative writing", "Multimodal input"],
            },
            {
                "name": "gpt-5-mini-2025-08-07",
                "description": "Fast and efficient GPT-5 family model for most tasks",
                "capabilities": ["Code generation", "Text analysis", "Creative writing"],
            }
        ]
        
        return models
    async def generate_code(self, prompt: str, framework: str, styling: str, features: List[str], complexity: str, model: Optional[str] = None, images: Optional[List[Dict[str, Any]]] = None) -> Dict[str, str]:
        """Generate code based on the provided prompt and parameters"""
        ALLOWED_MIME = {"image/png", "image/jpg", "image/jpeg", "image/webp", "image/svg+xml"}
        MAX_IMAGES = 3
        MAX_IMAGE_BYTES = 1_800_000  # ~1.8MB; skip larger to keep context safe

        if not self.client:
            raise Exception("AI service not available. Please check your OpenAI API key.")
        
        # Create a detailed system prompt
        system_prompt = self._create_system_prompt(framework, styling, features, complexity)
        
        # Create user prompt
        user_prompt = f"""
        Please generate a complete web application based on the following requirements:
        
        {prompt}
        
        Requirements:
        - Framework: {framework}
        - Styling: {styling}
        - Features: {', '.join(features)}
        - Complexity: {complexity}
        
        Please provide the complete code structure with all necessary files.
        """
        
        # Prepare messages for the API call (multimodal when images are present)
        messages: List[Dict[str, Any]] = [{"role": "system", "content": system_prompt}]

        valid_images: List[Dict[str, Any]] = []
        if images:
            for img in images[:MAX_IMAGES]:
                # Convert ImageData object to dictionary if needed
                if hasattr(img, 'model_dump'):
                    img_dict = img.model_dump()
                elif hasattr(img, 'dict'):
                    img_dict = img.dict()
                else:
                    img_dict = img
                
                mt = (img_dict.get("mime_type") or "").lower()
                b64 = (img_dict.get("data") or "")
                approx_bytes = int(len(b64) * 0.75)  # rough estimate
                if mt in ALLOWED_MIME and b64 and approx_bytes <= MAX_IMAGE_BYTES:
                    valid_images.append(img_dict)

        if valid_images:
            # Describe images up front to guide the model
            image_notes_lines = []
            for i, img in enumerate(valid_images, 1):
                image_notes_lines.append(
                    f"- Image {i}: name={img.get('name','')}, mime={img.get('mime_type','')}, "
                    f"role={img.get('role','reference')}, alt={img.get('alt','')}, notes={img.get('notes','')}"
                )
            visual_context = "Visual References:\n" + "\n".join(image_notes_lines)

            content: List[Dict[str, Any]] = [{"type": "text", "text": f"{user_prompt}\n\n{visual_context}\n"}]
            for img in valid_images:
                content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{img['mime_type']};base64,{img['data']}"
                        # Optionally: "detail": "low"
                    }
                })
            messages.append({"role": "user", "content": content})
        else:
            messages.append({"role": "user", "content": user_prompt})
        
        try:
            selected_model = model or self.default_model
            response = self.client.chat.completions.create(
                model=selected_model,
                messages=messages,
            )
            self.last_raw_response = self._safe_dump_response(response)
            
            # Parse the response and extract code files
            content = response.choices[0].message.content
            files = self._parse_generated_code(content)
            if not files:
                logger.warning("Parser returned no files; falling back to default structure")
                return self._create_default_structure(framework, styling)
            return files
            
        except Exception as e:
            logger.error(f"Error generating code: {str(e)}")
            raise Exception(f"Failed to generate code: {str(e)}")

    def _safe_dump_response(self, response: Any) -> Any:
        """Return a JSON-serializable snapshot of the SDK response."""
        try:
            if hasattr(response, "model_dump_json"):
                import json
                return json.loads(response.model_dump_json())
        except Exception:
            pass
        try:
            if hasattr(response, "model_dump"):
                return response.model_dump()
        except Exception:
            pass
        try:
            if hasattr(response, "to_dict"):
                return response.to_dict()
        except Exception:
            pass
        try:
            return str(response)
        except Exception:
            return {"repr": repr(response)}
    
    def _create_system_prompt(self, framework: str, styling: str, features: List[str], complexity: str) -> str:
        """Create a system prompt for code generation"""
        return f"""
        You are an expert full-stack web developer and AI assistant specialized in generating complete, runnable web apps.

        Your task is to output a **PRODUCTION-READY** app from the following parameters:
        - framework: {framework}
        - styling: {styling}  // one of: Tailwind CSS | Bootstrap | CSS3 | Material-UI (also called MUI) | Chakra UI
        - features: {features}
        - complexity: {complexity}

        ## HARD REQUIREMENTS (**CRITICAL**)
        1) Generate **ALL** pages/components/logic requested. Use ONLY {framework} + {styling}. **NEVER** mix UI systems.
        2) Routing (if React): React Router v6 with **BrowserRouter wrapping <App />**.
        3) index.html MUST include:
        - `<div id="root"></div>`
        - `<script type="module" src="/src/main.jsx"></script>` ← mandatory
        - (Only preload fonts if explicitly requested.)
        4) **Imports must match files you create**. If you import `./services/i18n.js`, you MUST create `src/services/i18n.js`. No phantom imports or paths.
        5) **File extensions policy (CRITICAL)**:
        - Any file that contains **JSX** must use **.jsx** (or .tsx). **Never** put JSX in `.js`.
        - Use explicit extensions in local imports (`import x from './foo.jsx'`), not bare `./foo`.
        6) **package.json**:
        - All imported **runtime** libs go in `"dependencies"`. Build tooling goes in `"devDependencies"`.
        - Use: `"vite": "^5.x"`, `"@vitejs/plugin-react": "^4.x"` in **devDependencies**.
        - **Do NOT generate SSR builds or run vite build --ssr** unless I explicitly request it. The output must be a static SPA that can be served with vite preview (requires dist/index.html)
        - Include peer deps for the chosen styling → {styling}:
            - Tailwind → `tailwindcss`, `postcss`, `autoprefixer` (**devDependencies**).
            - Chakra UI → `@chakra-ui/react`, `@emotion/react`, `@emotion/styled`, `framer-motion` (**dependencies**).
            - Material-UI → `@mui/material`, `@emotion/react`, `@emotion/styled` (**dependencies**). (Add `@mui/icons-material` if you use icons.)
            - Bootstrap → `bootstrap` (**dependencies**) (and import its CSS in `src/main.jsx`).
            - CSS3 → **no Tailwind/Chakra/MUI/Bootstrap** packages.
        - Common utilities you import (e.g., `dayjs`, `i18next`, `react-i18next`, `react-icons`) must be listed in **dependencies**.
        7) **Styling guardrails** (enforce exclusivity):
        - **Tailwind** → include `tailwind.config.js`, `postcss.config.js`, and `@tailwind base; @tailwind components; @tailwind utilities;` in `src/index.css`. **No Chakra/MUI/Bootstrap usage**.
        - **Chakra UI** → wrap app with `ChakraProvider` (+ `ColorModeScript`). **No Tailwind/MUI/Bootstrap**.
        - **Material-UI** → wrap with `ThemeProvider`. **No Tailwind/Chakra/Bootstrap**.
        - **Bootstrap** → import `"bootstrap/dist/css/bootstrap.min.css"` in `src/main.jsx`. **No Tailwind/Chakra/MUI**.
        - **CSS3** → plain CSS only; **no Tailwind/Chakra/MUI/Bootstrap**.
        8) **PWA (vite-plugin-pwa)** — pick **ONE**:
        - a) **`generateSW` (preferred)**:
            - In `vite.config.js` use:
                ```js
                import {{ VitePWA }} from 'vite-plugin-pwa'
                // inside defineConfig({{ plugins: [ ... ] }})
                VitePWA({{
                    strategies: 'generateSW',
                    registerType: 'autoUpdate',
                    // OPTIONAL only if needed; if used, must be EXACT and without leading slashes:
                    // workbox: {{ globPatterns: ['**/*.{{js,css,html,ico,png,svg}}'] }}
                    manifest: {{ /* your manifest here */ }}
                }})
                ```
            - Do **NOT** set `globDirectory`. Do **NOT** use leading slashes in glob patterns.
        - b) **`injectManifest`**:
            - Create `src/sw.js` with `self.__WB_MANIFEST`.
            - Plugin **MUST OMIT** any `workbox` options.
        - Use a **single** manifest source: EITHER the plugin `manifest` object OR `public/manifest.webmanifest` + `<link rel="manifest">` in `index.html`, not both.
        - Use `vite-plugin-pwa` **^0.20.x** (not older).
        - Register the SW **once** (choose one): `virtual:pwa-register` OR `virtual:pwa-register/react`.
        - The Vite config **must** import the plugin: `import {{ VitePWA }} from 'vite-plugin-pwa'` before using `VitePWA(...)`.
        9) **Assets/Icons**:
        - Provide **real files** under `public/icons/` (SVG or PNG). **Do not** inline `data:` URLs in the manifest.
        - In the manifest, icon paths should be `"/icons/..."`.
        10) **robots.txt** must be plain text, not JSON.
        11) **Encoding & text**:
        - Output UTF-8 only. Use straight ASCII quotes `' "`. Avoid smart punctuation that causes mojibake (e.g. “—” written as `ÔÇö`).
        12) **Client-only code**:
        - Do **NOT** use Node-only APIs (`fs`, `path`, etc.) in client code.
        13) **Output format**:
        - **One fenced code block per file using triple backticks and `title=<path>`**. No prose outside code blocks. Finish with `Done.`
        14) **CRITICAL** check the existence of the URLs you are including in the project. If some URL does not exist (Error 404), replace it for another until it works.
        15) All the images included in the project has to be related to the topic of the project (e.g. if the project is about a restaurant, the images has to be related to the restaurant and food. If it is about fashion, the images has to be related to fashion and clothes).

        ## OUTPUT FORMAT (**CRITICAL**)
        - For every file, output the ACTUAL CODE and you MUST use fenced code blocks with triple backticks and title=<file_path> (**CRITICAL TO ALWAYS FOLLOW THIS RULE**). Example:
            ```jsx title=src/App.jsx
            // code here
            ```

        ## STYLE PROFILES (apply the one in `{styling}`)
        ### Tailwind CSS
        - Include `tailwind.config.js` with:
            ```js
            export default {{
                content: ['./index.html','./src/**/*.{{js,jsx,ts,tsx}}'],
                theme: {{ extend: {{}} }},
                plugins: []
            }}
            ```
        - Include `postcss.config.js`.
        - `src/index.css` must contain:
            ```css
            @tailwind base;
            @tailwind components;
            @tailwind utilities;
            ```
        - No Chakra/MUI/Bootstrap classes/components.

        ### Bootstrap
        - Add `"bootstrap"` to dependencies.
        - Import `"bootstrap/dist/css/bootstrap.min.css"` at the **top** of `src/main.jsx`.
        - Use Bootstrap classes in your JSX. No Tailwind/Chakra/MUI usage.

        ### CSS3
        - Only plain CSS modules or global CSS. No Tailwind/Chakra/MUI/Bootstrap.

        ### Material-UI (MUI)
        - Wrap app with `ThemeProvider` and `CssBaseline`.
        - Add `@emotion/react` & `@emotion/styled` in dependencies. Add `@mui/icons-material` only if you use icons.
        - Any component/provider that returns JSX must live in a `.jsx` file.

        ### Chakra UI
        - Wrap with `ChakraProvider` and include `ColorModeScript`.
        - Add `@emotion/*` and `framer-motion` in dependencies.
        - All Chakra components in `.jsx` files.

        ## VITE CONFIG REQUIREMENTS
        - `vite.config.js` must import both:
            ```js
            import react from '@vitejs/plugin-react'
            import {{ VitePWA }} from 'vite-plugin-pwa'
            ```

        - Export:
            ```js
            import {{ defineConfig }} from 'vite'
            export default defineConfig({{
            plugins: [
                react(),
                VitePWA({{
                strategies: 'generateSW',
                registerType: 'autoUpdate',
                manifest: {{
                    name: 'App',
                    short_name: 'App',
                    start_url: '/',
                    scope: '/',
                    display: 'standalone',
                    background_color: '#ffffff',
                    theme_color: '#111827',
                    icons: [
                    {{ src: '/icons/icon-192.png', sizes: '192x192', type: 'image/png', purpose: 'any' }},
                    {{ src: '/icons/icon-512.png', sizes: '512x512', type: 'image/png', purpose: 'any maskable' }}
                    ]
                }}
                }})
            ]
            }})
            ```

        **Never reference VitePWA without importing it.**
        **Never use globDirectory.**
        **If you include workbox.globPatterns, it must be exactly: ['**/*.{{js,css,html,ico,png,svg}}'] (no leading /).**


        ## VISUAL REFERENCES (Images) — how to use them
        You may receive images as multimodal context (e.g., logo, background photo, moodboard, wireframe/screenshot of desired style).
        Follow this exactly:

        A) **Interpretation**
        - If an image looks like a LOGO → create `public/assets/logo.<ext>` and use it in the header/brand. Provide `<link rel="icon" href="/assets/logo.<ext>">`.
        - If a BACKGROUND/hero photo is provided → save under `public/assets/hero.<ext>` and set it as hero background (CSS or component prop).
        - If MOODBOARD/STYLE reference → extract a small color palette (3-6 HEX values), font suggestions (system-safe fallback), and spacing/shape cues.
        - If WIREFRAME or SITE screenshot → approximate the layout (sections, spacing, visual hierarchy) without copying brand assets verbatim.

        B) **File handling**
        - Save every referenced image into `public/assets/` with a safe filename, and reference it relatively in code (no base64 in production files).
        - Provide `alt` text where images are used.
        - Do NOT import the image into the PWA manifest unless it is specifically an app icon; never embed data URLs in the manifest.
        - **Do NOT embed base64 into image files**. When you reference /assets/*.png|jpg|webp|svg, just reference the path; my tool will write binary files. If you must include a placeholder, put the text BINARY_PLACEHOLDER and I will replace it.”
        - **All local images must live under public/assets/**. Use /assets/... in JSX/HTML so Vite serves them from public.
        - For PWA icons, only reference `/icons/icon-192.png` and `/icons/icon-512.png` (no data URLs).
        - If the user explicitly provided images for Logo, Hero, Background or Banners, assume they will be written to disk by my tool at:
            - Logo → `/assets/logo.png`
            - Hero/Background → `/assets/hero.jpg`
            - Banners → `/assets/banner.jpg`
            **Otherwise, do not assume the images will be written to disk, so include other images in the project.**
        - Do not invent non-existent local images (except the canonical names above). For product/gallery images, either:
            - Use remote, publicly accessible URLs; OR
            - Use the canonical local names in `/assets/products/...` and list them in README under “Expected Local Assets”.
        - Never output any `public/assets/*` file in your code blocks. Only reference their paths.

        C) **Theme derivation**
        - From the provided images, infer:
        - `primary` and `accent` colors (HEX).
        - corner radius trend (rounded vs. sharp).
        - preferred elevation/shadows (subtle vs. pronounced).
        - Apply these in the chosen styling system:
        - Tailwind: extend theme in tailwind.config.js (colors, borderRadius).
        - MUI: createTheme({{ palette, shape, shadows }}).
        - Chakra: extendTheme({{ colors, radii, shadows }}).
        - Bootstrap/CSS3: define CSS variables in :root and use them consistently.

        D) **Placement**
        - If a logo is present, use it in the navbar/hero and as favicon. If colors clash with dark mode, add a subtle background or inverted variant.
        - If a background photo is present, ensure text contrast (overlay gradient if needed) and responsive behavior (object-fit/cover).

        E) **Licensing / Safety**
        - Do not include copyrighted assets that you do not generate or receive explicitly. If an image looks branded, create a generic equivalent.        

        ## FILES YOU MUST OUTPUT (for React+Vite; adjust if framework changes)
        - `package.json` (scripts: dev/build/preview) - **tooling in devDependencies; runtime in dependencies**
        - `vite.config.js`
        - `index.html` (with the required script tag)
        - `src/main.jsx`, `src/App.jsx`
        - `src/index.css`
        - All pages routed under `src/pages/` (e.g., `src/pages/Home.jsx`)
        - All components used under `src/components/` (e.g., `src/components/Button.jsx`)
        - Any service/init you import (e.g., `src/services/i18n.js`)
        - If Tailwind: `tailwind.config.js`, `postcss.config.js`
        - If Bootstrap: ensure CSS import in `src/main.jsx`
        - If PWA with injectManifest: include `src/sw.js`
        - `public/icons/` with at least `icon-192.*` and `icon-512.*`
        - `public/robots.txt`
        - `README.md`

        ## SELF-CHECK (write these comments at the TOP of `src/main.jsx`):
        /*
        I confirm:
        - index.html has `<script type="module" src="/src/main.jsx">`.
        - All relative imports point to files that exist with the **correct extensions** (.jsx for JSX).
        - All imported npm modules are in the correct package.json sections (runtime → dependencies; tooling (vite, @vitejs/plugin-react, vite-plugin-pwa, tailwind/postcss/autoprefixer if used) → devDependencies), and required peers added.
        - PWA config matches chosen strategy; no mixed `workbox`/`injectManifest`; no `globDirectory`; no leading slashes in glob patterns
        - Only {styling} is used for styling
        - Service worker is registered **once** and manifest source is single
        - Icons live in `public/icons/` (no data URLs)
        - All image references provided by the user are saved into `public/assets/` and used accordingly (logo, background, moodboard, wireframe).
        - No base64 or data: URLs anywhere (HTML/CSS/JS/manifest).
        - All local images referenced with `/assets/...` and **not** emitted as files in the output.
        - All the images and URLsincluyed in the project has been checked and are valid.
        */
        """
    
    def _parse_generated_code(self, content: str) -> Dict[str, str]:
        """Parse the generated code and extract individual files"""
        content = content.lstrip('\ufeff').replace('\r\n','\n')
        files, in_block = {}, False
        current_path, current_content, fence_len = None, [], None

        open_re  = re.compile(r'^\s*(?P<fence>`{3,4})(?P<lang>[^\s`]+)?\s*title=(?P<path>.+?)\s*$')
        close_re = re.compile(r'^\s*(?P<fence>`{3,4})\s*$')

        lines = content.splitlines()
        i = 0
        while i < len(lines):
            line = lines[i]
            m_open = open_re.match(line)
            m_close = close_re.match(line)

            if m_open:
                # cierre implícito si estaba abierto
                if in_block and current_path:
                    files[current_path] = '\n'.join(current_content).rstrip()
                in_block = True
                fence_len = len(m_open.group('fence'))
                current_path = m_open.group('path').strip()
                current_content = []
            elif in_block and m_close and len(m_close.group('fence')) == fence_len:
                files[current_path] = '\n'.join(current_content).rstrip()
                in_block = False
                current_path, current_content, fence_len = None, [], None
            else:
                if in_block and current_path:
                    current_content.append(line)
            i += 1

        if in_block and current_path:
            files[current_path] = '\n'.join(current_content).rstrip()

        # Sanitizar rutas básicas
        safe = {}
        for p, c in files.items():
            p2 = p.replace('\\','/').lstrip('/').replace('../','')
            safe[p2] = c
        return safe

    def _create_default_structure(self, framework: str, styling: str) -> Dict[str, str]:
        """Create a default file structure when parsing fails"""
        if framework.lower() == "react":
            return {
                "package.json": self._get_react_package_json(),
                "index.html": self._get_react_index_html(),
                "src/App.jsx": self._get_react_app_js(),
                "src/main.jsx": self._get_react_index_js(),
                "vite.config.js": self._get_vite_config(),
                "README.md": self._get_react_readme()
            }
        elif framework.lower() == "vue.js":
            return {
                "package.json": self._get_vue_package_json(),
                "index.html": self._get_vue_index_html(),
                "src/App.vue": self._get_vue_app_vue(),
                "src/main.js": self._get_vue_main_js(),
                "README.md": self._get_vue_readme()
            }
        else:
            return {
                "index.html": self._get_vanilla_html(),
                "styles.css": self._get_vanilla_css(),
                "script.js": self._get_vanilla_js(),
                "README.md": self._get_vanilla_readme()
            }
    
    def _get_react_package_json(self) -> str:
        return '''{
  "name": "generated-react-app",
  "version": "1.0.0",
  "private": true,
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
    "autoprefixer": "^10.4.16",
    "eslint": "^8.55.0",
    "eslint-plugin-react": "^7.33.2",
    "eslint-plugin-react-hooks": "^4.6.0",
    "eslint-plugin-react-refresh": "^0.4.5",
    "postcss": "^8.4.32",
    "tailwindcss": "^3.3.6",
    "vite": "^5.0.8"
  }
}'''
    
    def _get_react_index_html(self) -> str:
        return '''<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <meta name="theme-color" content="#000000" />
    <meta name="description" content="Generated React Application" />
    <title>Generated React App</title>
  </head>
  <body>
    <noscript>You need to enable JavaScript to run this app.</noscript>
    <div id="root"></div>
  </body>
</html>'''
    
    def _get_react_app_js(self) -> str:
        return '''import React, { useState } from 'react';
import './App.css';

function App() {
  const [count, setCount] = useState(0);

  return (
    <div className="App">
      <header className="App-header">
        <h1>Generated React Application</h1>
        <p>This is a generated React application.</p>
        <button onClick={() => setCount(count + 1)}>
          Count: {count}
        </button>
      </header>
    </div>
  );
}

export default App;'''
    
    def _get_react_index_js(self) -> str:
        return '''import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App.jsx';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);'''
    
    def _get_react_readme(self) -> str:
        return '''# Generated React Application

This is a React application generated by the AI Agent.

## Getting Started

1. Install dependencies:
   ```bash
   npm install
   ```

2. Start the development server:
   ```bash
   npm run dev
   ```

3. Open [http://localhost:5173](http://localhost:5173) to view it in the browser.

## Available Scripts

- `npm run dev` - Runs the app in development mode
- `npm run build` - Builds the app for production
- `npm run lint` - Lints and fixes files
- `npm run preview` - Preview the production build

## Learn More

To learn React, check out the [React documentation](https://reactjs.org/).
'''

    def _get_vite_config(self) -> str:
        return '''import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
})'''
    
    def _get_vue_package_json(self) -> str:
        return '''{
  "name": "generated-vue-app",
  "version": "1.0.0",
  "private": true,
  "scripts": {
    "serve": "vue-cli-service serve",
    "build": "vue-cli-service build",
    "lint": "vue-cli-service lint"
  },
  "dependencies": {
    "core-js": "^3.8.3",
    "vue": "^3.2.13"
  },
  "devDependencies": {
    "@vue/cli-plugin-babel": "~5.0.0",
    "@vue/cli-plugin-eslint": "~5.0.0",
    "@vue/cli-service": "~5.0.0",
    "eslint": "^7.32.0",
    "eslint-plugin-vue": "^8.0.3"
  }
}'''
    
    def _get_vue_index_html(self) -> str:
        return '''<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width,initial-scale=1.0">
    <link rel="icon" href="<%= BASE_URL %>favicon.ico">
    <title>Generated Vue App</title>
  </head>
  <body>
    <noscript>
      <strong>We're sorry but this app doesn't work properly without JavaScript enabled. Please enable it to continue.</strong>
    </noscript>
    <div id="app"></div>
    <!-- built files will be auto injected -->
  </body>
</html>'''
    
    def _get_vue_app_vue(self) -> str:
        return '''<template>
  <div id="app">
    <h1>Generated Vue Application</h1>
    <p>This is a generated Vue.js application.</p>
    <button @click="count++">Count: {{ count }}</button>
  </div>
</template>

<script>
export default {
  name: 'App',
  data() {
    return {
      count: 0
    }
  }
}
</script>

<style>
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #2c3e50;
  margin-top: 60px;
}
</style>'''
    
    def _get_vue_main_js(self) -> str:
        return '''import { createApp } from 'vue'
import App from './App.vue'

createApp(App).mount('#app')'''
    
    def _get_vue_readme(self) -> str:
        return '''# Generated Vue.js Application

This is a Vue.js application generated by the AI Agent.

## Getting Started

1. Install dependencies:
   ```bash
   npm install
   ```

2. Start the development server:
   ```bash
   npm run serve
   ```

3. Open [http://localhost:8080](http://localhost:8080) to view it in the browser.

## Available Scripts

- `npm run serve` - Runs the app in development mode
- `npm run build` - Builds the app for production
- `npm run lint` - Lints and fixes files

## Learn More

To learn Vue.js, check out the [Vue.js documentation](https://vuejs.org/).
'''
    
    def _get_vanilla_html(self) -> str:
        return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Generated Web Application</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <div class="container">
        <h1>Generated Web Application</h1>
        <p>This is a generated web application.</p>
        <button id="counter">Count: 0</button>
    </div>
    <script src="script.js"></script>
</body>
</html>'''
    
    def _get_vanilla_css(self) -> str:
        return '''body {
    font-family: Arial, sans-serif;
    margin: 0;
    padding: 20px;
    background-color: #f5f5f5;
}

.container {
    max-width: 800px;
    margin: 0 auto;
    text-align: center;
    background-color: white;
    padding: 40px;
    border-radius: 10px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}

h1 {
    color: #333;
    margin-bottom: 20px;
}

button {
    background-color: #007bff;
    color: white;
    border: none;
    padding: 10px 20px;
    border-radius: 5px;
    cursor: pointer;
    font-size: 16px;
}

button:hover {
    background-color: #0056b3;
}'''
    
    def _get_vanilla_js(self) -> str:
        return '''let count = 0;
const counterButton = document.getElementById('counter');

counterButton.addEventListener('click', () => {
    count++;
    counterButton.textContent = `Count: ${count}`;
});'''
    
    def _get_vanilla_readme(self) -> str:
        return '''# Generated Web Application

This is a vanilla JavaScript web application generated by the AI Agent.

## Getting Started

1. Open `index.html` in your web browser
2. Or serve the files using a local server:
   ```bash
   python -m http.server 8000
   ```
   Then open [http://localhost:8000](http://localhost:8000)

## Files

- `index.html` - Main HTML file
- `styles.css` - CSS styles
- `script.js` - JavaScript functionality

## Features

- Responsive design
- Interactive counter
- Modern styling
''' 