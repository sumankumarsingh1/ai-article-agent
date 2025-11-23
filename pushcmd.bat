
REM  "git push https://<GITHUB_ACCESS_TOKEN>@github.com/<GITHUB_USERNAME>/<REPOSITORY_NAME>.git"  

call ..\mpghpat.bat
call updatescaler.bat
git add *
git commit -m "Reorganized Modules"
git push origin main 
