from pathlib import Path
from PIL import Image, ImageDraw
import sys

folder = Path(__file__).resolve().parent
frames = sorted(folder.glob('frame-*.png'))
count = int(sys.argv[1]) if len(sys.argv) > 1 else 24
frames = frames[-count:]
columns = 4
w, h = 336, 182
sheet = Image.new('RGB', (columns*w, ((len(frames)+columns-1)//columns)*h), 'white')
draw = ImageDraw.Draw(sheet)
for index, path in enumerate(frames):
    pic = Image.open(path).convert('RGB')
    pic.thumbnail((w, h-22))
    x, y = (index % columns)*w, (index // columns)*h
    sheet.paste(pic, (x+(w-pic.width)//2,y+22))
    draw.text((x+6, y+4), path.stem.removeprefix('frame-'), fill='black')
sheet.save(folder/'contact-sheet.jpg', quality=92)
print(f'{len(frames)} frames: {frames[0].name} to {frames[-1].name}')
