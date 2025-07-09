@echo off
echo Testing CP Cap Integration on Windows...
echo.

echo 1. Testing league change to Ultra League (2500 CP)...
powershell -Command "Invoke-WebRequest -Uri 'http://localhost:5000/api/league/2500' -Method POST"
echo.

echo 2. Testing league change back to Great League (1500 CP)...
powershell -Command "Invoke-WebRequest -Uri 'http://localhost:5000/api/league/1500' -Method POST"
echo.

echo 3. Testing invalid CP cap (1000)...
powershell -Command "try { Invoke-WebRequest -Uri 'http://localhost:5000/api/league/1000' -Method POST } catch { Write-Host 'Expected error: ' $_.Exception.Message }"
echo.

echo 4. Testing battle API with CP cap...
powershell -Command "$body = @{p1_id='clodsire'; p2_id='lanturn'; p1_moves=@{fast='POISON_STING'; charged1='EARTHQUAKE'; charged2='STONE_EDGE'}; p2_moves=@{fast='WATER_GUN'; charged1='SURF'; charged2='THUNDERBOLT'}; p1_shields=2; p2_shields=2; cp_cap=1500} | ConvertTo-Json; Invoke-WebRequest -Uri 'http://localhost:5000/api/battle' -Method POST -Body $body -ContentType 'application/json'"
echo.

echo Testing complete!
pause 