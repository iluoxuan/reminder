@echo off
echo 正在安装依赖包...
pip install -r requirements.txt

echo 正在生成示例二维码...
python create_qr.py

echo 正在打包程序...
pyinstaller --noconfirm --onefile --windowed ^
    --add-data "donate_qr.png;." ^
    --add-data "language.json;." ^
    --icon "donate_qr.png" ^
    --name "提醒助手" ^
    reminder_app.py

echo 打包完成！
echo 可执行文件位于 dist 目录下的"提醒助手.exe"

pause 