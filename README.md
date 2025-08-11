# 🚀 AI Agent - Web App Generator

> **Transform your ideas into fully functional web applications with AI-powered code generation**

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--5-orange.svg)](https://openai.com/)
[![Cloudflare](https://img.shields.io/badge/Cloudflare-Tunnels-blue.svg)](https://cloudflare.com/)

An intelligent AI agent that creates complete, production-ready web applications from simple text prompts. Built with modern technologies and featuring a beautiful, intuitive interface.

## ✨ Features

### 🎯 **Core Capabilities**
- **🤖 AI-Powered Generation**: Create complete web applications using OpenAI's GPT-5
- **🎨 Multiple Frameworks**: Support for React, Vue.js, Vanilla JavaScript, Python Flask, and FastAPI
- **🔧 Smart Code Parsing**: Automatically extracts and organizes generated code into proper file structures
- **👀 Real-time Preview**: View generated applications directly within the interface
- **⚡ Dynamic Modifications**: Modify generated applications in real-time with live preview updates
- **🌍 Global Sharing**: Share your applications with anyone, anywhere using Cloudflare tunnels

### 🎨 **Framework & Styling Support**
- **Frontend Frameworks**: React, Vue.js, Vanilla JavaScript
- **Backend Frameworks**: Python Flask, Python FastAPI
- **Styling Frameworks**: Tailwind CSS, Bootstrap, CSS3, Material-UI, Chakra UI
- **Build Tools**: Vite, Webpack, npm integration
- **Package Management**: Automatic dependency detection and installation

### 🖼️ **Multimodal AI Input**
- **📸 Image Upload**: Upload up to 3 images to provide visual context
- **🎯 Smart Image Analysis**: Specify image roles (logo, layout, background, etc.)
- **📝 Metadata Support**: Add alt text, notes, and purpose for each image
- **🔍 Visual Context**: AI uses images to understand design preferences and requirements

### 🎮 **Interactive Features**
- **📝 Live Code Editor**: Edit generated code with syntax highlighting
- **🎨 Theme Customization**: Apply different color themes (Dark, Light, Blue, Green, Purple)
- **📏 Dynamic Styling**: Adjust font sizes, colors, and spacing in real-time
- **💾 Save & Download**: Download applications as ZIP files or open in browser
- **📊 Application Metadata**: View detailed information about generated applications

### 🌐 **Global Deployment**
- **🚀 One-Command Deployment**: `python start_simple.py` deploys everything globally
- **🌍 Cloudflare Integration**: Automatic tunnel creation for global access
- **🔒 Secure Connections**: Encrypted tunnels with no setup required for recipients
- **📱 Cross-Platform**: Works on any device, anywhere in the world

### 🔧 **Advanced Features**
- **🔍 Search Functionality**: Built-in search capabilities
- **🌙 Dark Mode**: Automatic dark/light theme support
- **📱 Responsive Design**: Mobile-first, responsive layouts
- **🔐 User Authentication**: User login and registration systems
- **💾 Database Integration**: Database connectivity and management
- **🔄 Real-time Updates**: Live data updates and notifications
- **📤 File Upload**: File upload and management systems
- **🌐 Internationalization**: Multi-language support
- **📱 Progressive Web App**: PWA capabilities for mobile apps

## 🛠️ Technology Stack

### **Frontend**
- **Streamlit** - Beautiful, interactive web interface
- **React/Vue.js** - Modern frontend frameworks
- **Tailwind CSS/Bootstrap** - Utility-first CSS frameworks
- **Material-UI/Chakra UI** - Component libraries

### **Backend**
- **FastAPI** - High-performance Python API framework
- **Python Flask** - Lightweight web framework
- **OpenAI GPT-5** - Advanced AI model for code generation
- **LangChain** - AI orchestration and prompt management

### **Infrastructure**
- **Cloudflare Tunnels** - Global deployment and sharing
- **Vite** - Modern build tool for frontend applications
- **npm** - Package management for JavaScript dependencies
- **Docker** - Containerization support

## 📁 Project Structure

```
AI-Agent/
├── app/                    # Streamlit frontend
│   ├── main.py            # Main Streamlit application
│   ├── components/        # Reusable UI components
│   └── utils/             # Utility functions
│       ├── api_client.py  # API client for backend communication
│       ├── preview_utils.py # Preview and modification utilities
│       ├── ui_components.py # UI components and layout
│       └── config.py      # Configuration settings
├── api/                   # FastAPI backend
│   ├── main.py           # FastAPI application
│   ├── models/           # Pydantic models
│   ├── services/         # Business logic
│   │   ├── ai_service.py # OpenAI integration
│   │   └── generation_service.py # Code generation logic
│   └── utils/            # Configuration and utilities
├── .cloudflare/          # Cloudflare tunnel configuration
├── start.py              # Local application launcher
├── start_simple.py       # 🚀 One-command global deployment
├── cloudflare_status.py  # Status checking utility
├── requirements.txt      # Python dependencies
└── README.md            # Project documentation
```

## 🚀 Quick Start

### Prerequisites
- **Python 3.8+**
- **OpenAI API key** - [Get one here](https://platform.openai.com/api-keys)
- **Cloudflare tunnel daemon** - [Install here](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/ai-agent-web-generator.git
   cd ai-agent-web-generator
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   cp env.example .env
   # Edit .env and add your OpenAI API key
   ```

4. **Run locally**
   ```bash
   python start.py
   ```

5. **Deploy globally (One command)**
   ```bash
   python start_simple.py
   ```

## 📖 Usage Guide

### 🎯 **Basic Workflow**

1. **Describe Your Application**
   ```
   "Create a modern todo list app with drag-and-drop functionality, 
   dark mode support, and local storage persistence"
   ```

2. **Configure Options**
   - **Framework**: React, Vue.js, Vanilla JavaScript, Python Flask, FastAPI
   - **Styling**: Tailwind CSS, Bootstrap, CSS3, Material-UI, Chakra UI
   - **Features**: Authentication, Database, API Integration, etc.
   - **Complexity**: Simple, Medium, Complex

3. **Add Visual Context (Optional)**
   - Upload up to 3 images (logos, layouts, backgrounds)
   - Specify image roles and purposes
   - Add alt text and notes for AI context

4. **Generate & Preview**
   - Click "Generate Application"
   - View live preview embedded in the interface
   - Edit code with real-time updates

5. **Customize & Deploy**
   - Apply themes and styling modifications
   - Download as ZIP or open in browser
   - Share globally with Cloudflare URLs

### 🌐 **Global Sharing**

**One-Command Global Deployment:**
```bash
python start_simple.py
```

This automatically:
- Starts your AI Agent application
- Creates Cloudflare tunnels for all services
- Provides public URLs accessible worldwide
- No setup required for recipients

**Your Public URLs:**
- **📊 Streamlit UI**: Main application interface
- **🔌 API Backend**: Backend API service
- **👀 Preview Apps**: Generated web applications

### 🔧 **Advanced Features**

#### **Live Code Editor**
- Syntax highlighting for HTML, CSS, JavaScript, Python
- Real-time preview updates
- File-by-file editing capabilities
- Error detection and validation

#### **Dynamic Modifications**
- **Theme Selection**: Dark, Light, Blue, Green, Purple themes
- **Font Control**: Adjust text sizes dynamically
- **Custom CSS**: Add your own styles
- **Content Editing**: Modify titles and add new content

#### **Application Management**
- **Save & Download**: ZIP files with complete project structure
- **Browser Integration**: Open applications directly in browser
- **Metadata Display**: Framework detection, file count, dependencies
- **History Tracking**: View previous generations

## 🎯 Example Applications

### **E-commerce Product Page**
```
"Create a modern product page with image gallery, 
product details, reviews, add to cart functionality, 
and responsive design using React and Tailwind CSS"
```

### **Portfolio Website**
```
"Generate a professional portfolio website with sections 
for about, projects, skills, and contact. Include smooth 
animations and dark mode support"
```

### **Task Management App**
```
"Build a task management application with drag-and-drop 
kanban boards, user authentication, real-time updates, 
and database integration"
```

### **Social Media Dashboard**
```
"Create a social media dashboard with analytics charts, 
post scheduling, engagement metrics, and responsive 
design using Vue.js and Material-UI"
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file with:

```env
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-5-2025-08-07
APP_NAME=AI Agent - Web App Generator
DEBUG=true
ENVIRONMENT=development
API_HOST=localhost
API_PORT=8000
API_BASE_URL=http://localhost:8000
STREAMLIT_PORT=8501
STREAMLIT_HOST=localhost
SECRET_KEY=your_secret_key_here
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=sqlite:///./app.db
LOG_LEVEL=INFO
```

### API Endpoints

- `GET /health` - Health check
- `GET /models` - Available AI models
- `POST /generate` - Generate web application
- `GET /history` - Generation history
- `DELETE /history` - Clear history
- `GET /status/{generation_id}` - Generation status

## 🌟 Key Features in Detail

### **🤖 AI-Powered Code Generation**
- Uses OpenAI's GPT-5 for advanced code generation
- Understands natural language requirements
- Generates production-ready, well-structured code
- Supports multiple programming paradigms

### **🎨 Framework Flexibility**
- **React**: Modern component-based architecture
- **Vue.js**: Progressive JavaScript framework
- **Vanilla JavaScript**: Lightweight, no-framework approach
- **Python Flask**: Lightweight web framework
- **Python FastAPI**: High-performance API framework

### **💅 Styling Options**
- **Tailwind CSS**: Utility-first CSS framework
- **Bootstrap**: Popular CSS framework
- **CSS3**: Custom styling with modern CSS features
- **Material-UI**: Google's Material Design components
- **Chakra UI**: Accessible component library

### **🔧 Build System Integration**
- **Vite**: Fast build tool and dev server
- **Webpack**: Module bundler support
- **npm**: Package management
- **Hot Reload**: Real-time development experience

### **🌍 Global Deployment**
- **Cloudflare Tunnels**: Secure, encrypted connections
- **One-Command Setup**: `python start_simple.py`
- **Global Access**: Share with anyone, anywhere
- **No Configuration**: Recipients need no setup

## 🔍 Troubleshooting

### Common Issues

1. **OpenAI API Key Missing**
   - Ensure your `.env` file contains a valid OpenAI API key
   - Check that the key has sufficient credits

2. **Preview Not Loading**
   - Check browser console for iframe security issues
   - Ensure generated HTML is valid
   - Try refreshing the preview

3. **Build Failures**
   - Check for syntax errors in generated code
   - Verify all dependencies are installed
   - Review build logs for specific errors

4. **Cloudflare Tunnel Issues**
   - Ensure cloudflared is installed and in PATH
   - Check that PowerShell windows are still open
   - Verify services are running: `python cloudflare_status.py`

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **OpenAI** for providing the GPT-5 AI model
- **Streamlit** for the beautiful web framework
- **FastAPI** for the high-performance API framework
- **Cloudflare** for global tunnel access
- **The open-source community** for inspiration and tools

## 📞 Support

- **GitHub Issues**: [Report bugs or request features](https://github.com/yourusername/ai-agent-web-generator/issues)
- **Documentation**: Check the [Wiki](https://github.com/yourusername/ai-agent-web-generator/wiki)
- **Discussions**: Join our [GitHub Discussions](https://github.com/yourusername/ai-agent-web-generator/discussions)

## 🌟 Star History

[![Star History Chart](https://api.star-history.com/svg?repos=yourusername/ai-agent-web-generator&type=Date)](https://star-history.com/#yourusername/ai-agent-web-generator&Date)

---

**🚀 Ready to build amazing web applications? Start with `python start_simple.py` and deploy globally in one command!**

**⭐ If you find this project helpful, please give it a star on GitHub!**
