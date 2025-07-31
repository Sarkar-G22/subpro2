@echo off
echo 🚀 Starting Subtitle Generator Application...
echo.

echo 📦 Installing Python dependencies...
pip install -r requirements.txt
echo.

echo 📦 Installing Node.js dependencies...
npm install
echo.

echo 🐍 Starting Python Backend Server...
start "Backend Server" cmd /k "python server.py"

echo ⏳ Waiting for backend to start...
timeout /t 5 /nobreak >nul

echo ⚛️ Starting React Frontend...
start "Frontend Server" cmd /k "npm start"

echo.
echo ✅ Both servers are starting...
echo 🌐 Frontend: http://localhost:3000
echo 🌐 Backend: http://localhost:5000
echo.
echo Press any key to close this window...
pause >nul
