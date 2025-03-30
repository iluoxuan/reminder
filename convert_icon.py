from PIL import Image
import cairosvg

# 将 SVG 转换为 PNG
cairosvg.svg2png(url='down_arrow.svg', write_to='down_arrow.png') 