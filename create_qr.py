from PIL import Image, ImageDraw, ImageFont
import os

def create_sample_qr():
    # 创建一个300x300的白色图片
    img = Image.new('RGB', (300, 300), 'white')
    draw = ImageDraw.Draw(img)
    
    # 绘制一个简单的二维码样式
    # 绘制三个定位点
    draw.rectangle([(50, 50), (100, 100)], fill='black')
    draw.rectangle([(200, 50), (250, 100)], fill='black')
    draw.rectangle([(50, 200), (100, 250)], fill='black')
    
    # 添加文字
    try:
        font = ImageFont.truetype("arial.ttf", 20)
    except:
        font = ImageFont.load_default()
    
    draw.text((100, 150), "示例二维码", fill='black', font=font)
    
    # 保存图片
    img.save('donate_qr.png')

if __name__ == '__main__':
    create_sample_qr() 