import upgrade as u, cairosvg, io, subprocess
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
font='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
import textwrap
for i,(title,material,origin,steps) in u.stories.items():
 out=Path('media')/f'{i}.mp4'
 proc=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pixel_format','rgb24','-video_size','640x360','-framerate','15','-i','-','-c:v','libx264','-pix_fmt','yuv420p','-movflags','+faststart',str(out)],stdin=subprocess.PIPE)
 for j,s in enumerate(steps):
  art=Image.open(io.BytesIO(cairosvg.svg2png(bytestring=u.scene(i,j).encode(),output_width=420,output_height=210))).convert('RGB')
  for f in range(60):
   im=Image.new('RGB',(640,360),'#f0e8d8'); d=ImageDraw.Draw(im); d.text((20,12),'DHARMA  /  '+title,font=ImageFont.truetype(font,20),fill='#193e32'); d.text((20,42),f'{origin}  |  Stage {j+1} of 6',font=ImageFont.truetype(font,14),fill='#193e32'); im.paste(art,(110,65)); d=ImageDraw.Draw(im); d.line((110+int(420*f/59),65,110+int(420*f/59),275),fill='#c39848',width=2); d.text((20,280),'\n'.join(textwrap.wrap(s,75)),font=ImageFont.truetype(font,15),fill='#193e32'); d.text((20,332),'Illustrated concept • not documentary footage',font=ImageFont.truetype(font,12),fill='#59675e'); d.rectangle((0,354,int(640*(j*60+f+1)/360),359),fill='#193e32'); proc.stdin.write(im.tobytes())
 proc.stdin.close(); assert proc.wait()==0
