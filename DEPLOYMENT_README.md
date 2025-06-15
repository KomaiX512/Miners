# 🚀 Complete Deployment Guide
## Social Media Content Recommendation System
### Module 1 (Main System) + Module 2 (Enhanced Goal Handler)

---

## 📋 Table of Contents
- [System Overview](#system-overview)
- [Prerequisites](#prerequisites)
- [Quick Installation](#quick-installation)
- [Manual Installation](#manual-installation)
- [Configuration](#configuration)
- [Running the System](#running-the-system)
- [Troubleshooting](#troubleshooting)
- [API Documentation](#api-documentation)

---

## 🏗️ System Overview

This is a comprehensive AI-powered social media content recommendation system consisting of two integrated modules:

### **Module 1: Main Recommendation System**
- Instagram/Twitter data scraping via Apify
- Time series analysis with Prophet
- Vector database with ChromaDB
- RAG implementation using Google Gemini
- Content plan generation and export
- Flask-based REST API

### **Module 2: Enhanced Goal Handler**
- Advanced goal-oriented content planning
- XGBoost machine learning for post estimation
- FastAPI-based query processing
- Real-time image generation
- File monitoring with automatic processing

---

## ✅ Prerequisites

### **System Requirements**
- **Python**: 3.8 or higher
- **Operating System**: Linux, macOS, or Windows
- **Memory**: Minimum 4GB RAM (8GB recommended)
- **Storage**: 2GB free space
- **Internet**: Required for AI services and data scraping

### **Required API Keys**
1. **Google Gemini API Key** (Essential)
   - Get from: https://makersuite.google.com/app/apikey
2. **Apify API Token** (For scraping)
   - Get from: https://apify.com/account/api
3. **News API Key** (Optional)
   - Get from: https://newsapi.org/

---

## ⚡ Quick Installation

### **Option 1: Automated Installation (Linux/macOS)**
```bash
# Clone the repository
git clone <your-repo-url>
cd <repo-name>

# Run automated installation
./install.sh
```

### **Option 2: Automated Installation (Windows)**
```cmd
REM Clone the repository
git clone <your-repo-url>
cd <repo-name>

REM Run automated installation
install.bat
```

### **Option 3: Python Setup (Cross-platform)**
```bash
# Clone the repository
git clone <your-repo-url>
cd <repo-name>

# Install using setup.py
pip install -e .
```

---

## 🔧 Manual Installation

If you prefer manual control over the installation process:

### **Step 1: Clone Repository**
```bash
git clone <your-repo-url>
cd <repo-name>
```

### **Step 2: Create Virtual Environment**
```bash
# Linux/macOS
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### **Step 3: Install Dependencies**
```bash
# Upgrade pip
pip install --upgrade pip

# Install requirements
pip install -r requirements.txt
```

### **Step 4: Create Directory Structure**
```bash
mkdir -p models cache logs data
mkdir -p main_intelligence next_posts recommendations
mkdir -p competitor_analysis engagement_strategies trending_topics
mkdir -p tasks/goal tasks/query
mkdir -p Module2/models Module2/cache Module2/logs
```

---

## ⚙️ Configuration

### **Environment Setup**
1. Copy the `.env.template` to `.env`:
   ```bash
   cp .env.template .env  # Linux/macOS
   copy .env.template .env  # Windows
   ```

2. Edit `.env` with your API keys:
   ```bash
   nano .env  # Linux/macOS
   notepad .env  # Windows
   ```

3. **Required Configuration**:
   ```env
   # Essential
   GEMINI_API_KEY=your_actual_gemini_api_key
   APIFY_API_TOKEN=your_actual_apify_token
   
   # Optional
   NEWS_API_KEY=your_news_api_key
   ```

### **Pre-configured Services**
The following are already configured and ready to use:
- ✅ **Cloudflare R2 Storage**: Fully configured
- ✅ **Database Connections**: Pre-setup
- ✅ **Logging System**: Ready to use

---

## 🚀 Running the System

### **Module 1: Main Recommendation System**

#### **Process Instagram Username**
```bash
python main.py --instagram username_here
```

#### **Process Twitter Username**
```bash
python main.py --twitter username_here
```

#### **Start Web API**
```bash
python api.py
# API will be available at: http://localhost:5000
```

#### **Continuous Processing Loop**
```bash
python main.py --loop
```

### **Module 2: Enhanced Goal Handler**

#### **Start Goal Handler**
```bash
cd Module2
python main.py
# This runs both goal monitoring and query API at port 8001
```

#### **Start Only Query Handler**
```bash
cd Module2
python query_handler.py
# FastAPI server at: http://localhost:8001
```

### **Running Both Modules Simultaneously**
```bash
# Terminal 1: Start Module 1 API
python api.py

# Terminal 2: Start Module 2
cd Module2 && python main.py

# Terminal 3: Run processing (optional)
python main.py --loop
```

---

## 🔧 Troubleshooting

### **Common Issues & Solutions**

#### **1. Import Errors**
```bash
# Error: ModuleNotFoundError
# Solution: Ensure virtual environment is activated
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows
pip install -r requirements.txt
```

#### **2. API Key Errors**
```bash
# Error: Invalid API key
# Solution: Check .env file configuration
cat .env  # Linux/macOS
type .env # Windows
# Ensure keys are properly set without quotes
```

#### **3. Port Already in Use**
```bash
# Error: Port 5000/8001 in use
# Solution: Change port in configuration or kill existing process
lsof -ti:5000 | xargs kill -9  # Linux/macOS
netstat -ano | findstr :5000   # Windows
```

#### **4. Memory Issues**
```bash
# Error: Out of memory
# Solution: Reduce batch sizes in config.py
# Or increase system RAM/swap
```

#### **5. Permission Issues (Linux/macOS)**
```bash
# Error: Permission denied
# Solution: Make scripts executable
chmod +x install.sh
chmod +x *.py
```

### **Debugging Commands**
```bash
# Test Module 1
python -c "from main import ContentRecommendationSystem; print('✅ Module 1 OK')"

# Test Module 2
python -c "import sys; sys.path.append('Module2'); from goal_rag_handler import EnhancedGoalHandler; print('✅ Module 2 OK')"

# Check dependencies
pip list | grep -E "(numpy|pandas|torch|langchain|chromadb)"

# View logs
tail -f logs/*.log  # Linux/macOS
type logs\*.log     # Windows
```

---

## 📡 API Documentation

### **Module 1 API (Port 5000)**

#### **Process Instagram Username**
```http
POST /process_instagram
Content-Type: application/json

{
  "username": "example_user",
  "force_fresh": false
}
```

#### **Process Twitter Username**
```http
POST /process_twitter
Content-Type: application/json

{
  "username": "example_user", 
  "force_fresh": false
}
```

#### **Get Content Plan**
```http
GET /content_plan/{username}
```

### **Module 2 API (Port 8001)**

#### **Process Posts**
```http
POST /process-posts
Content-Type: application/json

{
  "posts": [...],
  "platform": "instagram",
  "account_type": "personal"
}
```

#### **Scan New Posts**
```http
POST /scan-new-posts
Content-Type: application/json

{
  "goal_id": "unique_goal_id"
}
```

---

## 📊 System Architecture

```
┌─────────────────┐    ┌─────────────────┐
│   Module 1      │    │   Module 2      │
│  (Port 5000)    │    │  (Port 8001)    │
├─────────────────┤    ├─────────────────┤
│ • Data Scraping │    │ • Goal Handler  │
│ • Time Series   │    │ • XGBoost ML    │
│ • Vector DB     │    │ • Query API     │
│ • RAG System    │    │ • File Monitor  │
│ • Content Plans │    │ • Image Gen     │
└─────────────────┘    └─────────────────┘
         │                        │
         └────────────────────────┘
                   │
         ┌─────────────────┐
         │ Shared Storage  │
         │ (Cloudflare R2) │
         └─────────────────┘
```

---

## 🎯 Usage Examples

### **Example 1: Complete Instagram Analysis**
```bash
# Step 1: Process Instagram account
python main.py --instagram nike

# Step 2: Check generated content plan
ls -la main_intelligence/instagram/nike/

# Step 3: Use Module 2 for goal-specific analysis
cd Module2
# Place goal file in tasks/goal/nike_goal.json
python main.py
```

### **Example 2: API Integration**
```python
import requests

# Process account via API
response = requests.post('http://localhost:5000/process_instagram', 
                        json={'username': 'nike'})

# Get content plan
plan = requests.get('http://localhost:5000/content_plan/nike')
print(plan.json())
```

### **Example 3: Multi-Platform Processing**
```bash
# Process multiple platforms sequentially
python main.py --sequential --instagram nike --twitter nike
```

---

## 📈 Performance Optimization

### **For Large Scale Deployment**
1. **Increase worker processes**:
   ```bash
   uvicorn api:app --workers 4 --host 0.0.0.0 --port 5000
   ```

2. **Use Redis for caching** (optional):
   ```bash
   pip install redis
   # Add Redis configuration to config.py
   ```

3. **Database optimization**:
   ```bash
   # Use persistent ChromaDB storage
   # Configure in vector_database.py
   ```

---

## 📝 Development Notes

### **Adding New Features**
- Follow the existing module structure
- Add dependencies to `requirements.txt`
- Update configuration in `config.py`
- Add tests in appropriate test files

### **Code Quality**
```bash
# Run tests
pytest tests/

# Code formatting
black *.py Module2/*.py

# Type checking
mypy main.py
```

---

## 🆘 Support

### **Getting Help**
1. **Check logs**: `logs/` directory contains detailed error information
2. **Run diagnostics**: Use the troubleshooting commands above
3. **API testing**: Use tools like Postman or curl to test endpoints
4. **Documentation**: Review individual module README files

### **Common Commands Reference**
```bash
# Quick system check
python -c "import main, sys; sys.path.append('Module2'); import goal_rag_handler; print('✅ All OK')"

# Reset environment
rm -rf venv cache logs  # Linux/macOS
rmdir /s venv cache logs  # Windows
# Then run install script again

# Update dependencies
pip install -r requirements.txt --upgrade
```

---

## ✅ Deployment Checklist

- [ ] Python 3.8+ installed
- [ ] Repository cloned
- [ ] Virtual environment created
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] `.env` file configured with API keys
- [ ] Directory structure created
- [ ] Module 1 tested (`python main.py --help`)
- [ ] Module 2 tested (`cd Module2 && python main.py --help`)
- [ ] APIs accessible (ports 5000 and 8001)
- [ ] Sample processing completed successfully

**🎉 Your system is ready for production use!** 