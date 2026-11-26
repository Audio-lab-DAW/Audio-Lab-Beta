import json,subprocess,io,os
src=open('/home/claude/gen/geo.py').read(); exec(src[:src.index('V=[')])
D="/home/claude/final/"; os.makedirs(D,exist_ok=True)
TIERS={ # name: (kw, used for)
 "L":({"ring_w":44,"nr":80,"er":46,"gap":15},"128 px and up (Dock, Finder, Launchpad, About)"),
 "M":({"ring_w":56,"taper":.25,"nr":88,"er":52,"gap":18},"48 to 64 px (Finder lists, taskbar, Settings picker)"),
 "S":({"ring_w":80,"taper":0.0,"nr":118,"er":68,"gap":26},"16 to 32 px (favicon, menus, small Windows icons)"),
}
def tier_svg(t,fg=W,bg=OC,acc=YE,tile=True):
    kw=TIERS[t][0]; tr=place(kw,1.0,(512,504)); els=mark(fg,bg,**kw)
    els=list(els); els[-1]=els[-1].replace(f'fill="{fg}"',f'fill="{acc}"',1); els[-3]=els[-3].replace(f'fill="{fg}"',f'fill="{acc}"',1)
    return svg(els,bg=bg,tr=tr)
if __name__=="__main__":
    for t in TIERS:
        s=tier_svg(t); open(D+t+".svg","w").write(s); rast(s).save(D+t+".png")
        print(t,{k:round(v,1) if isinstance(v,float) else v for k,v in measure(TIERS[t][0],place(TIERS[t][0],1.0,(512,504))).items()})
    g2=rast(open("/home/claude/geo/G2.svg").read())
    # comparison sheet: rows = G2 (before), final tiers at their real sizes
    from PIL import ImageDraw
    sz=[256,128,64,48,32,16]; sh=Image.new("RGB",(40+sum(s+20 for s in sz),2*300+40),(30,30,36)); d=ImageDraw.Draw(sh)
    def tierfor(s): return "L" if s>=128 else ("M" if s>=48 else "S")
    fin={t:Image.open(D+t+".png") for t in TIERS}
    for r,(lab,get) in enumerate([("G2 only",lambda s:g2),("Final tiers",lambda s:fin[tierfor(s)])]):
        x=20; y=20+r*300; d.text((x,y),lab,fill=(220,220,220))
        for s in sz:
            sh.paste(get(s).resize((s,s),Image.LANCZOS),(x,y+20),get(s).resize((s,s),Image.LANCZOS)); 
            if r: d.text((x,y+20+s+4),f"{s}px {tierfor(s)}",fill=(180,180,180))
            x+=s+20
    sh.save("/home/claude/sheet_final.png")
