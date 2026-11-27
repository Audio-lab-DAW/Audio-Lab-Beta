# DR2: crops of the headless screenshots for the 'Today' cards of the pick page (page/today/*.jpg)
import os
from PIL import Image
D=os.path.dirname(os.path.abspath(__file__));T=D+'/today';O=D+'/page/today'
for tag in ('dark','light'):
    Image.open(f'{T}/arr_zoom_{tag}.png').crop((0,0,600,330)).convert('RGB').save(f'{O}/arrangement_{tag}.jpg',quality=86)
    Image.open(f'{T}/pianoroll_{tag}.png').crop((0,205,600,465)).convert('RGB').save(f'{O}/pianoroll_{tag}.jpg',quality=86)
    Image.open(f'{T}/browser_{tag}.png').crop((24,28,1100,620)).convert('RGB').save(f'{O}/browser_{tag}.jpg',quality=84)
    Image.open(f'{T}/presetmenu_{tag}.png').crop((770,14,1000,500)).convert('RGB').save(f'{O}/presetmenu_{tag}.jpg',quality=86)
    full=Image.open(f'{T}/full_{tag}.png');tr=Image.open(f'{T}/transport_{tag}.png')
    im=Image.new('RGB',(1600,30+tr.height));im.paste(full.crop((0,0,1600,30)),(0,0));im.paste(tr.convert('RGB'),(0,30));im.save(f'{O}/transport_{tag}.jpg',quality=88)
print(sorted(os.listdir(O)))
