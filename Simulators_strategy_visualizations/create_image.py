from PIL import Image, ImageDraw, ImageFont

def create_placeholder_image(width, height, text, path):
    img = Image.new('RGB', (width, height), color = (255, 255, 255))
    d = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 40)
    except IOError:
        font = ImageFont.load_default()
    d.text((10,10), text, fill=(0,0,0), font=font)
    img.save(path)

if __name__ == '__main__':
    create_placeholder_image(800, 400, "Architecture Overview", "Simulators_strategy_visualizations/assets/diagrams/architecture_overview.png")
