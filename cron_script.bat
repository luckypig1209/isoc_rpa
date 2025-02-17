@echo off
cd /d C:\Mac\Home\Desktop\isoc_rpa
call C:\Users\zhuhaoran\miniconda3\Scripts\activate.bat base
set DISPLAY=:0
python main.py >> log.txt 2>&1
