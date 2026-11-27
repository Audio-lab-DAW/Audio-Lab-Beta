# DR4: crop today's screenshots into one picture per instrument family (embedded in the pick page as "Today")
from PIL import Image
import base64,io,json,os
T='today/';o=lambda n:Image.open(T+n).convert('RGB')
def comp(parts,gap=8):
    W=sum(p.width for p in parts)+gap*(len(parts)-1);H=max(p.height for p in parts)
    c=Image.new('RGB',(W,H),(10,10,12));x=0
    for p in parts:c.paste(p,(x,0));x+=p.width+gap
    return c
def stack(parts,gap=8):
    W=max(p.width for p in parts);H=sum(p.height for p in parts)+gap*(len(parts)-1)
    c=Image.new('RGB',(W,H),(10,10,12));y=0
    for p in parts:c.paste(p,(0,y));y+=p.height+gap
    return c
fa=o('full_arrange.png');mx=o('mixer_stereo.png');vz=o('visualizer.png');dm=o('devices_master.png')
F={}
F['M']=stack([comp([mx.crop((10,236,410,352)),mx.crop((1108,205,1245,352))]),comp([fa.crop((1328,852,1600,888)),fa.crop((196,70,222,170))])])
F['L']=comp([o('lufs_pop.png').crop((0,0,408,330)),o('dev_4_4.png').crop((35,0,600,250))])
F['S']=stack([o('dev_5_5.png').crop((35,0,580,250)),vz.crop((482,735,960,885))])
F['O']=comp([mx.crop((10,180,410,240)),mx.crop((1110,40,1245,205))])
F['G']=comp([o('devices_comp.png').crop((515,598,815,838)),o('dev_3_3.png').crop((35,0,560,250))])
F['E']=o('dev_2_2.png').crop((35,0,600,250))
F['V']=vz.crop((0,705,1600,885))
F['C']=o('cpu.png')
F['D']=comp([dm.crop((668,600,1190,838)),o('dev_6_6.png').crop((35,0,580,250))])
out={}
for k,im in F.items():
    if im.width>1100:im=im.resize((1100,int(im.height*1100/im.width)),Image.LANCZOS)
    im.save(T+'family_'+k+'.png');b=io.BytesIO();im.save(b,'JPEG',quality=78);out[k]='data:image/jpeg;base64,'+base64.b64encode(b.getvalue()).decode()
    print(k,im.size,len(b.getvalue()))
json.dump(out,open('today_b64.json','w'))
