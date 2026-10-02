from PIL import Image,ImageDraw
import imageio.v2 as imageio
import numpy as np

def render(frames,path):
    images=[]; scale=24
    colors=['#f57a77','#7dcc98','#779af5']
    for s in frames:
        im=Image.new('RGB',(288,364),'#182432'); d=ImageDraw.Draw(im)
        for y in range(12):
            for x in range(12):
                wall=x in (0,11) or y in (0,11)
                d.rectangle((x*scale,y*scale,(x+1)*scale-1,(y+1)*scale-1), fill='#40505e' if wall else '#e6ddce')
        for i,(x,y) in enumerate(s['objects']):
            box=(x*scale+4,y*scale+4,(x+1)*scale-4,(y+1)*scale-4)
            if i==3:d.rectangle(box,fill='#8058a6')
            elif s['cooldown'][i]==0:d.ellipse(box,fill=colors[i])
        x,y=s['pos']; d.ellipse((x*scale+4,y*scale+3,x*scale+20,y*scale+20),fill='#222832' if s['alive'] else '#888888')
        d.text((8,294),f"step {s['age']}  E={s['energy']:.2f}  F={s['fatigue']:.2f}",fill='white')
        d.text((8,314),f"good colour={s['good']}  taste={s['taste']:+.2f}",fill='white')
        if 'modulation' in s:d.text((8,340),f"modulation m={s['modulation']:+.3f}",fill='white')
        images.append(np.asarray(im))
    imageio.mimsave(path,images,duration=80,loop=0)
