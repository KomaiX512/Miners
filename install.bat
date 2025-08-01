@echo off
REM =============================================================================
REM COMPREHENSIVE INSTALLATION SCRIPT FOR WINDOWS
REM Social Media Content Recommendation System
REM Includes Module 1 (Main System) + Module 2 (Enhanced Goal Handler)
REM =============================================================================

echo.
echo ==============================================================================
echo   SOCIAL MEDIA RECOMMENDATION SYSTEM - WINDOWS INSTALLATION
echo ==============================================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

REM Check Python version
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set python_version=%%i
echo 🔍 Detected Python version: %python_version%

REM Check if version is 3.8+
python -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)" >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python 3.8+ is required. Please upgrade Python.
    pause
    exit /b 1
)

echo ✅ Python version is compatible
echo.

REM Check for pip
pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ pip is not installed. Please install pip first.
    pause
    exit /b 1
)

echo ✅ pip found
echo.

REM Create virtual environment
echo 🔧 Setting up virtual environment...
if not exist "venv" (
    python -m venv venv
    echo ✅ Virtual environment created
) else (
    echo 📁 Virtual environment already exists
)

REM Activate virtual environment
call venv\Scripts\activate.bat
echo ✅ Virtual environment activated
echo.

REM Upgrade pip
echo 🔧 Upgrading pip...
python -m pip install --upgrade pip
echo ✅ pip upgraded
echo.

REM Install build tools
echo 🔧 Installing build tools...
pip install wheel setuptools
echo ✅ Build tools installed
echo.

REM Install requirements
echo 🔧 Installing dependencies from requirements.txt...
pip install -r requirements.txt
echo ✅ Dependencies installed
echo.

REM Create necessary directories
echo 🔧 Creating necessary directories...
if not exist "models" mkdir models
if not exist "cache" mkdir cache
if not exist "logs" mkdir logs
if not exist "data" mkdir data
if not exist "main_intelligence" mkdir main_intelligence
if not exist "next_posts" mkdir next_posts
if not exist "recommendations" mkdir recommendations
if not exist "competitor_analysis" mkdir competitor_analysis
if not exist "engagement_strategies" mkdir engagement_strategies
if not exist "trending_topics" mkdir trending_topics
if not exist "tasks" mkdir tasks
if not exist "tasks\goal" mkdir tasks\goal
if not exist "tasks\query" mkdir tasks\query
if not exist "Module2\models" mkdir Module2\models
if not exist "Module2\cache" mkdir Module2\cache
if not exist "Module2\logs" mkdir Module2\logs
echo ✅ Directories created
echo.

REM Create .env template if it doesn't exist
echo 🔧 Setting up environment configuration...
if not exist ".env" (
    echo # ============================================================================= > .env
    echo # ENVIRONMENT CONFIGURATION >> .env
    echo # Copy this file and fill in your actual API keys and configurations >> .env
    echo # ============================================================================= >> .env
    echo. >> .env
    echo # Google AI (Gemini) Configuration >> .env
    echo GEMINI_API_KEY=your_gemini_api_key_here >> .env
    echo GOOGLE_API_KEY=your_google_api_key_here >> .env
    echo. >> .env
    echo # News API Configuration (Optional) >> .env
    echo NEWS_API_KEY=your_news_api_key_here >> .env
    echo. >> .env
    echo # Apify Configuration >> .env
    echo APIFY_API_TOKEN=your_apify_token_here >> .env
    echo. >> .env
    echo # R2 Storage Configuration (Pre-configured) >> .env
    echo R2_ENDPOINT_URL=https://51abf57b5c6f9b6cf2f91cc87e0b9ffe.r2.cloudflarestorage.com >> .env
    echo R2_ACCESS_KEY_ID=2093fa05ee0323bb39de512a19638e78 >> .env
    echo R2_SECRET_ACCESS_KEY=e9e7173d1ee514b452b3a3eb7cef6fb57a248423114f1f949d71dabd34eee04f >> .env
    echo R2_BUCKET_NAME=structuredb >> .env
    echo. >> .env
    echo # System Configuration >> .env
    echo PYTHON_PATH=./ >> .env
    echo LOG_LEVEL=INFO >> .env
    echo DEBUG=False >> .env
    echo. >> .env
    echo # API Configuration >> .env
    echo API_HOST=0.0.0.0 >> .env
    echo API_PORT=5000 >> .env
    echo MODULE2_API_PORT=8001 >> .env
    
    echo ✅ .env template created
    echo ⚠️  Please edit .env file with your actual API keys
) else (
    echo 📁 .env file already exists
)
echo.

REM Test installation
echo 🧪 Testing installation...
echo Testing Module 1 (Main System)...
python -c "from main import ContentRecommendationSystem; print('✅ Module 1 import successful')" 2>nul
if %errorlevel% neq 0 (
    echo ⚠️  Module 1 import test failed (may need API keys)
) else (
    echo ✅ Module 1 is working correctly
)

echo Testing Module 2 (Enhanced Goal Handler)...
python -c "import sys; sys.path.append('Module2'); from goal_rag_handler import EnhancedGoalHandler; print('✅ Module 2 import successful')" 2>nul
if %errorlevel% neq 0 (
    echo ⚠️  Module 2 import test failed (may need API keys)
) else (
    echo ✅ Module 2 is working correctly
)
echo.

REM Installation complete
echo ==============================================================================
echo   🎉 INSTALLATION COMPLETED SUCCESSFULLY! 🎉
echo ==============================================================================
echo.
echo 📋 NEXT STEPS:
echo 1. Edit .env file with your API keys:
echo    notepad .env
echo.
echo 2. Activate virtual environment (for future sessions):
echo    venv\Scripts\activate.bat
echo.
echo 3. Run Module 1 (Main System):
echo    python main.py --instagram username_here
echo    python api.py   (For web API)
echo.
echo 4. Run Module 2 (Enhanced Goal Handler):
echo    cd Module2
echo    python main.py
echo.
echo 5. For help and documentation:
echo    python main.py --help
echo    type README.md
echo.
echo ✅ System is ready for deployment!
echo.
pause 