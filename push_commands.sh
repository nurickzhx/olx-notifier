#!/usr/bin/env bash
# push_commands.sh – quick helper to initialise repo and push to GitHub
# ---------------------------------------------------------------
# 1. Initialise repository (run only once)
# git init
# git add olx_notifier.py requirements.txt Dockerfile config.json cities.txt
# git commit -m "Initial commit – OLX notifier"
#
# 2. Add remote (replace <YOUR_USERNAME> and <REPO_NAME>)
# git remote add origin https://github.com/<YOUR_USERNAME>/<REPO_NAME>.git
#
# 3. Push to GitHub (first push creates the master/main branch)
# git push -u origin master   # or main, depending on your default branch
#
# Subsequent changes:
# git add .
# git commit -m "Your message"
# git push
# ---------------------------------------------------------------
# Make script executable:
# chmod +x push_commands.sh
