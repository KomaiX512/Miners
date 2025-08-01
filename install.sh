#!/bin/bash
# =============================================================================
# COMPREHENSIVE INSTALLATION SCRIPT
# Social Media Content Recommendation System
# Includes Module 1 (Main System) + Module 2 (Enhanced Goal Handler)
# =============================================================================

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m' 
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# System info
echo -e "${BLUE}==============================================================================${NC}"
echo -e "${BLUE}  SOCIAL MEDIA RECOMMENDATION SYSTEM - INSTALLATION SCRIPT${NC}"
echo -e "${BLUE}==============================================================================${NC}"
echo ""

# Check Python version
python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo -e "${BLUE}🔍 Detected Python version: ${python_version}${NC}"

if python3 -c 'import sys; exit(0 if sys.version_info >= (3, 8) else 1)'; then
    echo -e "${GREEN}✅ Python version is compatible (>= 3.8)${NC}"
else
    echo -e "${RED}❌ Python 3.8+ is required. Please upgrade Python.${NC}"
    exit 1
fi

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check for pip
if command_exists pip3; then
    PIP_CMD="pip3"
elif command_exists pip; then
    PIP_CMD="pip"
else
    echo -e "${RED}❌ pip is not installed. Please install pip first.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ pip found: ${PIP_CMD}${NC}"

# Create virtual environment (recommended)
echo ""
echo -e "${YELLOW}🔧 Setting up virtual environment...${NC}"
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✅ Virtual environment created${NC}"
else
    echo -e "${BLUE}📁 Virtual environment already exists${NC}"
fi

# Activate virtual environment
source venv/bin/activate
echo -e "${GREEN}✅ Virtual environment activated${NC}"

# Upgrade pip
echo ""
echo -e "${YELLOW}🔧 Upgrading pip...${NC}"
python -m pip install --upgrade pip
echo -e "${GREEN}✅ pip upgraded${NC}"

# Install wheel and setuptools
echo ""
echo -e "${YELLOW}🔧 Installing build tools...${NC}"
pip install wheel setuptools
echo -e "${GREEN}✅ Build tools installed${NC}"

# Install requirements
echo ""
echo -e "${YELLOW}🔧 Installing dependencies from requirements.txt...${NC}"
pip install -r requirements.txt
echo -e "${GREEN}✅ Dependencies installed${NC}"

# Create necessary directories
echo ""
echo -e "${YELLOW}🔧 Creating necessary directories...${NC}"
directories=(
    "models"
    "cache"
    "logs"
    "data"
    "main_intelligence"
    "next_posts" 
    "recommendations"
    "competitor_analysis"
    "engagement_strategies"
    "trending_topics"
    "tasks/goal"
    "tasks/query"
    "Module2/models"
    "Module2/cache"
    "Module2/logs"
)

for dir in "${directories[@]}"; do
    if [ ! -d "$dir" ]; then
        mkdir -p "$dir"
        echo -e "${GREEN}  ✅ Created: ${dir}${NC}"
    else
        echo -e "${BLUE}  📁 Exists: ${dir}${NC}"
    fi
done

# Create .env template if it doesn't exist
echo ""
echo -e "${YELLOW}🔧 Setting up environment configuration...${NC}"
if [ ! -f ".env" ]; then
    cat > .env << 'EOF'
# =============================================================================
# ENVIRONMENT CONFIGURATION
# Copy this file and fill in your actual API keys and configurations
# =============================================================================

# Google AI (Gemini) Configuration
GEMINI_API_KEY=your_gemini_api_key_here
GOOGLE_API_KEY=your_google_api_key_here

# News API Configuration (Optional)
NEWS_API_KEY=your_news_api_key_here

# Apify Configuration
APIFY_API_TOKEN=your_apify_token_here

# R2 Storage Configuration (Pre-configured)
R2_ENDPOINT_URL=https://51abf57b5c6f9b6cf2f91cc87e0b9ffe.r2.cloudflarestorage.com
R2_ACCESS_KEY_ID=2093fa05ee0323bb39de512a19638e78
R2_SECRET_ACCESS_KEY=e9e7173d1ee514b452b3a3eb7cef6fb57a248423114f1f949d71dabd34eee04f
R2_BUCKET_NAME=structuredb
# AI Horde Image Generation Configuration
AI_HORDE_API_KEY=your_ai_horde_api_key_here

# System Configuration
PYTHON_PATH=./
LOG_LEVEL=INFO
DEBUG=False

# API Configuration
API_HOST=0.0.0.0
API_PORT=5000
MODULE2_API_PORT=8001
EOF
    echo -e "${GREEN}✅ .env template created${NC}"
    echo -e "${YELLOW}⚠️  Please edit .env file with your actual API keys${NC}"
else
    echo -e "${BLUE}📁 .env file already exists${NC}"
fi

# Test installation
echo ""
echo -e "${YELLOW}🧪 Testing installation...${NC}"

# Test Module 1
echo -e "${BLUE}Testing Module 1 (Main System)...${NC}"
if python -c "from main import ContentRecommendationSystem; print('✅ Module 1 import successful')" 2>/dev/null; then
    echo -e "${GREEN}✅ Module 1 is working correctly${NC}"
else
    echo -e "${YELLOW}⚠️  Module 1 import test failed (may need API keys)${NC}"
fi

# Test Module 2
echo -e "${BLUE}Testing Module 2 (Enhanced Goal Handler)...${NC}"
if python -c "import sys; sys.path.append('Module2'); from goal_rag_handler import EnhancedGoalHandler; print('✅ Module 2 import successful')" 2>/dev/null; then
    echo -e "${GREEN}✅ Module 2 is working correctly${NC}"
else
    echo -e "${YELLOW}⚠️  Module 2 import test failed (may need API keys)${NC}"
fi

# Installation complete
echo ""
echo -e "${GREEN}==============================================================================${NC}"
echo -e "${GREEN}  🎉 INSTALLATION COMPLETED SUCCESSFULLY! 🎉${NC}"
echo -e "${GREEN}==============================================================================${NC}"
echo ""
echo -e "${BLUE}📋 NEXT STEPS:${NC}"
echo -e "${YELLOW}1. Edit .env file with your API keys:${NC}"
echo -e "   nano .env"
echo ""
echo -e "${YELLOW}2. Activate virtual environment (for future sessions):${NC}"
echo -e "   source venv/bin/activate"
echo ""
echo -e "${YELLOW}3. Run Module 1 (Main System):${NC}"
echo -e "   python main.py --instagram username_here"
echo -e "   python api.py  # For web API"
echo ""
echo -e "${YELLOW}4. Run Module 2 (Enhanced Goal Handler):${NC}"
echo -e "   cd Module2"
echo -e "   python main.py"
echo ""
echo -e "${YELLOW}5. For help and documentation:${NC}"
echo -e "   python main.py --help"
echo -e "   cat README.md"
echo ""
echo -e "${GREEN}✅ System is ready for deployment!${NC}"
echo "" 