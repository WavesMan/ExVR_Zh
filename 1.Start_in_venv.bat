@echo off

echo Entering a virtual venv
call venv\Scripts\activate
echo successfully activated venv
pause 

echo Starting ExVR
::python main.py
python main_zh.py
pause