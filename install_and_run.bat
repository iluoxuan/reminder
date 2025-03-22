@echo off
echo 正在安装依赖包...
pip install -r requirements.txt

echo 正在生成示例二维码...
python create_qr.py

echo 正在运行程序...
python reminder_app.py

pause 