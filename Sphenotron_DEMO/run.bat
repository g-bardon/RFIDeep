@echo [off]
python "sphenotron_main.py" -srcpath=%1
IF %ERRORLEVEL% NEQ 0
