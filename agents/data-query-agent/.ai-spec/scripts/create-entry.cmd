@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0create-entry.ps1" %*
