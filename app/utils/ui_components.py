"""
UI components and utilities for the Streamlit application.
"""

import streamlit as st
import requests
import base64
from typing import Dict, Any

from .config import get_config


def create_generation_config_section() -> None:
    """Create the generation configuration section."""
    config = get_config()
    
    # Create 4 columns for all selectors (removed AI Model)
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        framework = st.selectbox("Framework", config.FRAMEWORKS)
    
    with col2:
        styling = st.selectbox("Styling", config.STYLING_OPTIONS)
    
    with col3:
        features = st.multiselect("Features", config.FEATURE_OPTIONS)
    
    with col4:
        complexity = st.selectbox("Complexity", config.COMPLEXITY_OPTIONS)
    
    # Store in session state for use in main
    st.session_state.generation_config = {
        "framework": framework,
        "styling": styling,
        "features": features,
        "complexity": complexity,
        "model": "gpt-5-2025-08-07"  # Always use GPT-5
    }


def create_image_upload_section() -> None:
    """Create the image upload section."""
    with st.container():
        st.markdown('<div class="image-upload-section">', unsafe_allow_html=True)
        st.markdown("Add up to 3 images to provide visual context (logos, layouts, backgrounds, etc.)")
    
    # Initialize uploaded images in session state if not exists
    if "uploaded_images" not in st.session_state:
        st.session_state.uploaded_images = []
    
    # File uploader
    uploaded_files = st.file_uploader(
        "Choose images",
        type=['png', 'jpg', 'jpeg', 'gif', 'webp', 'svg'],
        accept_multiple_files=True,
        key="image_uploader"
    )
    
    # Handle uploaded files
    if uploaded_files:
        # Limit to 3 images
        if len(uploaded_files) > 3:
            st.warning("⚠️ Maximum 3 images allowed. Only the first 3 will be used.")
            uploaded_files = uploaded_files[:3]
        
        # Process and store images
        st.session_state.uploaded_images = []
        for i, uploaded_file in enumerate(uploaded_files):
            try:
                # Read image data
                image_data = uploaded_file.read()
                image_base64 = base64.b64encode(image_data).decode('utf-8')
                
                # Get file extension
                file_extension = uploaded_file.name.split('.')[-1].lower()
                mime_type = f"image/{file_extension}" if file_extension != 'svg' else "image/svg+xml"
                
                # Create a unique key for this image's metadata
                image_key = f"image_{i}_{uploaded_file.name.replace('.', '_')}"
                
                # Display image preview and metadata fields in a more compact layout
                st.markdown(f"**Image {i+1}: {uploaded_file.name}** ({len(image_data)} bytes)")
                
                col1, col2, col3 = st.columns([1, 2, 2])
                with col1:
                    st.image(uploaded_file, width=80)
                
                with col2:
                    # Metadata input fields
                    role = st.selectbox(
                        "Role/Purpose",
                        ["Reference", "Logo", "Background", "Layout", "Icon", "Banner", "Hero", "Other"],
                        index=0,
                        key=f"{image_key}_role"
                    )
                    
                    alt_text = st.text_input(
                        "Alt Text",
                        value="",
                        placeholder="Short description (e.g., 'Company Logo')",
                        key=f"{image_key}_alt"
                    )
                
                with col3:
                    notes = st.text_area(
                        "Notes",
                        value="",
                        placeholder="Additional context (e.g., 'Use as hero background')",
                        height=50,
                        key=f"{image_key}_notes"
                    )
                
                # Store image info with metadata
                image_info = {
                    "name": uploaded_file.name,
                    "data": image_base64,
                    "mime_type": mime_type,
                    "size": len(image_data),
                    "role": role,
                    "alt": alt_text,
                    "notes": notes
                }
                st.session_state.uploaded_images.append(image_info)
                
                st.divider()
                
            except Exception as e:
                st.error(f"Error processing {uploaded_file.name}: {str(e)}")
    else:
        # Clear session state when no files are uploaded
        st.session_state.uploaded_images = []
    
    # Show current images count
    if st.session_state.uploaded_images:
        st.success(f"✅ {len(st.session_state.uploaded_images)} image(s) uploaded successfully")
    else:
        st.info("💡 No images uploaded. You can still generate applications with just text.")
    
    st.markdown('</div>', unsafe_allow_html=True)


def create_main_content() -> None:
    """Create the main content area."""
    # Add moderate space between subtitle and content
    st.markdown("<br><br><br><br><br>", unsafe_allow_html=True)
    
    prompt = st.text_area(
        "Describe your web application",
        height=200,
        placeholder="Ask me to create a dashboard to track sales, a portfolio website with dark mode, or any web application you can imagine..."
    )
    
    # Generation Settings Section (Collapsible)
    with st.expander("⚙️ Generation Settings", expanded=False):
        with st.container():
            st.markdown('<div class="generation-settings">', unsafe_allow_html=True)
            create_generation_config_section()
            st.markdown('</div>', unsafe_allow_html=True)
    
    # Image Upload Section (Collapsible)
    with st.expander("📷 Upload Images (Optional)", expanded=False):
        create_image_upload_section()
    
    # Parser Section (Collapsible) - at the bottom
    with st.expander("🔧 Try Parser with Your Own Content", expanded=False):
        create_parser_section()
    
    # Add minimal space before the generate button
    #st.markdown("<br>", unsafe_allow_html=True)
    
    # Generate Application button at the bottom
    if st.button("🚀 Generate Application", type="primary"):
        if prompt.strip():
            create_generation_request(prompt)
        else:
            st.warning("Please enter a description for your application.")
    
    # Add space before generation stats
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # Generation Stats
    create_generation_stats()

def create_generation_request(prompt: str) -> None:
    """Create and send the generation request."""
    config = get_config()
    
    st.markdown("<br>", unsafe_allow_html=True)
    with st.spinner("✨ AI is crafting your amazing application... (it can take up to 5-10 minutes)"):
        try:
            # Get generation config from session state
            generation_config = st.session_state.get("generation_config", {})
            
            # Prepare the request
            generation_request = {
                "prompt": prompt,
                "framework": generation_config.get("framework", "React"),
                "styling": generation_config.get("styling", "Tailwind CSS"),
                "features": generation_config.get("features", []),
                "complexity": generation_config.get("complexity", "Simple"),
                "model": generation_config.get("model", "gpt-5-2025-08-07"),
                "images": st.session_state.get("uploaded_images", [])
            }
            
            # Store request info for potential future use
            st.session_state.last_generation_request = generation_request
            
            # Make the API call
            # Use separate connect/read timeouts to avoid premature timeouts on long generations
            response = requests.post(
                f"{config.API_BASE_URL}/generate",
                json=generation_request,
                timeout=(getattr(config, 'API_CONNECT_TIMEOUT', 10), getattr(config, 'API_READ_TIMEOUT', config.API_TIMEOUT))
            )
            
            if response.status_code == 200:
                result = response.json()
                st.session_state.generated_files = result.get("files", {})
                from .preview_utils import create_build_preview
                preview_html, ok = create_build_preview(st.session_state.generated_files)
                st.session_state.preview_html = preview_html
                st.session_state.last_generation_preview_ok = ok
                
                # Store response for potential future use
                st.session_state.last_generation_response = result
                if ok:
                    st.success("Application generated successfully!")
                else:
                    st.warning("Application generated, but the preview failed. See the error message above.")
            else:
                st.error(f"Error generating application: {response.text}")
                
        except Exception as e:
            st.error(f"Error: {str(e)}")


def create_generation_stats() -> None:
    """Create the generation stats section."""
    if "generated_files" in st.session_state and st.session_state.generated_files:
        files = st.session_state.generated_files
        from .preview_utils import extract_metadata_from_files
        metadata = extract_metadata_from_files(files)
        
        with st.container():
            st.markdown('<div class="metric-container">', unsafe_allow_html=True)
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Files Generated", len(files))
            with col2:
                st.metric("Has HTML", "Yes" if metadata['has_html'] else "No")
            with col3:
                st.metric("Has CSS", "Yes" if metadata['has_css'] else "No")
            
            if metadata['frameworks_detected']:
                st.write(f"**Detected frameworks:** {', '.join(metadata['frameworks_detected'])}")
            st.markdown('</div>', unsafe_allow_html=True)


def create_parser_section() -> None:
    """Create the parser section for testing raw LLM content."""
    config = get_config()
    raw = st.text_area("Paste raw LLM content (markdown with code fences)", height=200, key="parser_raw_input")
    colp1, colp2 = st.columns([1,1])
    with colp1:
        framework = st.selectbox("Framework for defaults", get_config().FRAMEWORKS, key="parser_fw")
    with colp2:
        styling = st.selectbox("Styling for defaults", get_config().STYLING_OPTIONS, key="parser_sty")
    if st.button("Parse Content", key="btn_parse_content"):
        try:
            resp = requests.post(
                f"{config.API_BASE_URL}/debug/parse",
                json={"content": raw, "framework": framework, "styling": styling},
                timeout=(getattr(config, 'API_CONNECT_TIMEOUT', 10), getattr(config, 'API_READ_TIMEOUT', config.API_TIMEOUT))
            )
            if resp.status_code == 200:
                parsed = resp.json()
                st.success(f"Parsed {parsed.get('count', 0)} file(s)")
                with st.expander("Parsed files", expanded=True):
                    st.json(parsed.get("files", {}))

                # If we have files, attempt an embedded preview using the same build pipeline
                files = parsed.get("files", {})
                if files:
                    from .preview_utils import create_build_preview
                    st.info("Building preview from parsed content... This may take a couple of minutes the first time (npm install & build).")
                    preview_html, ok = create_build_preview(files)
                    if ok:
                        st.success("Preview built successfully")
                    else:
                        st.warning("Preview built in simple mode due to build issues")
                    st.markdown(preview_html, unsafe_allow_html=True)


                    # Provide direct ZIP download for parsed files
                    from .preview_utils import create_zip_download
                    zip_data = create_zip_download(files)
                    st.download_button(
                        label="Download Parsed Files (ZIP)",
                        data=zip_data,
                        file_name="parsed_files.zip",
                        mime="application/zip",
                        key="download_parsed_zip"
                    )
            else:
                st.error(f"Parse failed: {resp.text}")
        except Exception as e:
            st.error(f"Parse error: {e}")


def create_results_display() -> None:
    """Create the results display section."""
    if "generated_files" in st.session_state and st.session_state.generated_files:
        st.divider()
        
        # Use generated files
        files = st.session_state.generated_files
        preview_html = st.session_state.preview_html
        
        # Create tabs for different views
        tab1, tab2, tab3, tab4 = st.tabs(["Live Preview", "Code Editor", "Dynamic Modifications", "Save & Download"])
        
        with tab1:
            create_live_preview_tab(files, preview_html)
        
        with tab2:
            create_code_editor_tab(files)
        
        with tab3:
            create_dynamic_modifications_tab()
        
        with tab4:
            create_save_download_tab(files)


def create_live_preview_tab(files: Dict[str, str], preview_html: str) -> None:
    """Create the live preview tab."""
    st.subheader("Live Preview")
    
    # Display the build-based preview
    st.markdown(preview_html, unsafe_allow_html=True)
    
    # Rebuild preview option
    if st.button("Rebuild Preview"):
        st.session_state.rebuild_preview = True
        st.rerun()


def create_code_editor_tab(files: Dict[str, str]) -> None:
    """Create the code editor tab."""
    st.subheader("Code Editor")
    
    # Display individual files
    for file_path, content in files.items():
        with st.expander(f"{file_path}"):
            st.code(content, language=file_path.split('.')[-1] if '.' in file_path else 'text')


def create_dynamic_modifications_tab() -> None:
    """Create the dynamic modifications tab."""
    st.subheader("Dynamic Modifications")
    st.write("Modify your application in real-time!")
    
    # Add modification options here
    st.info("Dynamic modification features coming soon!")


def create_save_download_tab(files: Dict[str, str]) -> None:
    """Create the save and download tab."""
    st.subheader("Save & Download")
    
    # Create ZIP download
    from .preview_utils import create_zip_download, extract_metadata_from_files
    zip_data = create_zip_download(files)
    st.download_button(
        label="Download ZIP",
        data=zip_data,
        file_name="generated_app.zip",
        mime="application/zip"
    )
    
    # Display metadata
    metadata = extract_metadata_from_files(files)
    st.write("**Application Metadata:**")
    st.json(metadata)
