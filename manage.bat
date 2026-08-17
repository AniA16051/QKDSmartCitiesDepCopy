@echo off
REM Docker deployment management script for QKD Smart City Network (Windows)

setlocal enabledelayedexpansion

set COMMAND=%1

if "%COMMAND%"=="" (
    call :show_help
    exit /b 0
)

if /i "%COMMAND%"=="start" (
    call :start_services
    exit /b 0
)

if /i "%COMMAND%"=="stop" (
    call :stop_services
    exit /b 0
)

if /i "%COMMAND%"=="start-node" (
    call :start_user_node %2 %3 %4 %5 %6
    exit /b 0
)

if /i "%COMMAND%"=="stop-node" (
    call :stop_user_node %2
    exit /b 0
)

if /i "%COMMAND%"=="list" (
    call :list_nodes
    exit /b 0
)

if /i "%COMMAND%"=="logs" (
    call :view_logs %2
    exit /b 0
)

if /i "%COMMAND%"=="broker-logs" (
    call :view_broker_logs
    exit /b 0
)
if /i "%COMMAND%"=="dashboard-logs" (
    call :view_dashboard_logs
    exit /b 0
)
if /i "%COMMAND%"=="rebuild" (
    call :rebuild
    exit /b 0
)

if /i "%COMMAND%"=="reset" (
    call :reset
    exit /b 0
)

call :show_help
exit /b 1

:start_services
echo.
echo ======================================
echo   Starting QKD Smart City Network
echo ======================================
echo.
echo [*] Starting Mosquitto broker...
docker-compose up -d mosquitto
timeout /t 2 /nobreak

echo [*] Starting admin control center...
docker-compose up -d admin-node

echo [*] Starting dashboard...
docker-compose up -d dashboard
timeout /t 5 /nobreak

echo.
echo [+] All services started
docker-compose ps
echo.
echo ============================================
echo       DASHBOARD ACCESS INFORMATION
echo ============================================
echo.
echo Local Access:
echo   http://localhost:8501
echo.
echo Network Access:
echo   1. Find your IP: ipconfig
echo   2. Use: http://^<your-ip^>:8501
echo.
echo Default Credentials:
echo   Admin: admin / admin@qkd2026
echo   User:  user / user@qkd2026
echo.
echo ============================================
echo.
goto :eof

:stop_services
echo.
echo ======================================
echo   Stopping QKD Smart City Network
echo ======================================
echo.
docker-compose down

echo.
echo [+] All services stopped
goto :eof

:start_user_node
if "%2"=="" (
    echo [-] Error: node name required
    echo Usage: manage.bat start-node ^<node-name^> ^<sensor-type^> [options]
    echo Sensor types: traffic_flow, water_flow, surveillance
    exit /b 1
)

set NODE_NAME=%2
set SENSOR_TYPE=%3

echo [*] Starting user node: %NODE_NAME% (type: %SENSOR_TYPE%)

docker-compose run -d --name "%NODE_NAME%" ^
    -e BROKER_HOST=mosquitto ^
    -e BROKER_PORT=1883 ^
    -v ./docker/shared_keystore:/app/network/shared_keystore_data ^
    --network qkd_network ^
    --rm ^
    -f docker/Dockerfile.user ^
    python -m network.sensor_node --id "%NODE_NAME%" --type "%SENSOR_TYPE%" %4 %5 %6

echo [+] User node '%NODE_NAME%' started
goto :eof

:stop_user_node
if "%2"=="" (
    echo [-] Error: node name required
    echo Usage: manage.bat stop-node ^<node-name^>
    exit /b 1
)

set NODE_NAME=%2

echo [*] Stopping user node: %NODE_NAME%
docker stop "%NODE_NAME%" 2>nul

echo [+] User node '%NODE_NAME%' stopped
goto :eof

:list_nodes
echo.
echo ======================================
echo   Running Containers
echo ======================================
echo.
docker-compose ps
goto :eof

:view_logs
set SERVICE=%2
if "%SERVICE%"=="" set SERVICE=admin-node

echo.
echo ======================================
echo   Logs for %SERVICE%
echo ======================================
echo.
docker-compose logs -f %SERVICE%
goto :eof

:view_broker_logs
echo.
echo ======================================
echo   Mosquitto Broker Logs
echo ======================================
echo.
docker-compose logs -f mosquitto
goto :eof

:view_dashboard_logs
echo.
echo ======================================
echo   Dashboard Logs
echo ======================================
echo.
docker-compose logs -f dashboard
goto :eof

:rebuild
echo.
echo ======================================
echo   Rebuilding Docker Images
echo ======================================
echo.
docker-compose build --no-cache
echo.
echo [+] Rebuild complete
goto :eof

:reset
echo.
echo ======================================
echo   Resetting Deployment
echo ======================================
echo.
echo WARNING: This will delete all data!
set /p CONFIRM="Are you sure? (y/n): "

if /i "%CONFIRM%"=="y" (
    docker-compose down -v
    rmdir /s /q docker\mosquitto\data 2>nul
    rmdir /s /q docker\mosquitto\log 2>nul
    rmdir /s /q docker\shared_keystore 2>nul
    mkdir docker\mosquitto\data
    mkdir docker\mosquitto\log
    mkdir docker\shared_keystore
    echo [+] Reset complete
) else (
    echo [-] Reset cancelled
)
goto :eof

:show_help
echo.
echo QKD Smart City Network - Docker Management
echo.
echo Usage: manage.bat ^<command^> [options]
echo.
echo Commands:
echo   start               Start all services (MQTT, admin, dashboard)
echo   stop                Stop all services
echo   start-node          Start a new user node
echo                       Usage: manage.bat start-node ^<name^> ^<type^> [options]
echo                       Types: traffic_flow, water_flow, surveillance
echo   stop-node           Stop a specific user node
echo                       Usage: manage.bat stop-node ^<name^>
echo   list                List all running containers
echo   logs                View logs for a service (default: admin-node)
echo   broker-logs         View Mosquitto broker logs
echo   dashboard-logs      View dashboard logs
echo   rebuild             Rebuild all Docker images
echo   reset               Reset deployment (WARNING: deletes all data)
echo.
echo Examples:
echo   manage.bat start
echo   manage.bat start-node traffic-1 traffic_flow
echo   manage.bat start-node camera-1 surveillance --eavesdrop
echo   manage.bat list
echo   manage.bat logs admin-node
echo.
goto :eof
