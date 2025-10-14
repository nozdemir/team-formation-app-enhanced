@echo off
echo ============================
echo   HEROKU COST MANAGEMENT
echo ============================
echo.
echo Current Status:
echo Production (team-formation-app-new-05): RUNNING ($7/month)
echo Old versions: STOPPED ($0/month)
echo.
echo Total monthly cost: $7
echo GitHub Student credit: $13
echo Net result: FREE + $6 surplus!
echo.
echo ============================
echo Available Commands:
echo.
echo 1. heroku ps -a team-formation-app-new-05         (check production status)
echo 2. heroku ps:scale web=1 -a team-formation-app-gazi    (start old version for testing)
echo 3. heroku ps:scale web=0 -a team-formation-app-gazi    (stop old version to save money)
echo.
echo Replace 'gazi' with: gazi-2, working-app for other versions
echo.
echo ============================
pause