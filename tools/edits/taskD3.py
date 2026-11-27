# task D3 (v0.226): the type scale C1. Inter at 11, 12, 13 and 15 px, weights 400, 500 and 600, equal-width digits everywhere,
# mono only where time is shown.
#   python3 tools/edits/taskD3.py index.html [report.json] [--pins=tools/edits/taskD3_pins.json]
#   (--probe writes a copy with numbered markers instead; tools/ui-tests/taskD3_pins.py measures the line heights with it)
# Every font size, weight and family written in the CSS (style blocks, CSS kept in JS strings, style="" attributes) is replaced by one
# of a small set of tokens (defined once in tools/edits/taskD3_css.txt, pasted before `.dacv{display:flex;`). Nothing is typed by hand:
# the mapping below decides. Kept as they are: the logo wordmark and the splash (a picture that scales as a whole), glyphs used as
# icons, sizes that are not plain px (0, em, calc), and text drawn inside canvases and SVG pictures (only their weights above 600 go to 600).
import sys,re,json,os,collections
f=sys.argv[1] if len(sys.argv)>1 else 'index.html';s=open(f,encoding='utf-8').read()
here=os.path.dirname(os.path.abspath(__file__))
def rep(a,b):
    global s
    assert s.count(a)==1,(s.count(a),a[:80]);s=s.replace(a,b)
assert '--fs1' not in s,'already applied'
# ---- the mapping
def size_tok(px):   # nearest step; a tie goes to the smaller step so that less text grows
    if px<=11.5:return '--fs1'
    if px<=12.5:return '--fs2'
    if px<=14:return '--fs3'
    return '--fs4'
def weight_tok(w):
    w={'normal':400,'bold':700,'bolder':700,'lighter':400}.get(w,w);w=int(w)
    return '--fw4' if w<450 else '--fw5' if w<=550 else '--fw6'
# selectors that keep their type: the wordmark, the splash, and glyphs used as icons (carets, arrows, hearts, track pictures, emoji)
KEEP=re.compile(r'\.wm\b|\.wm[ALPS]\b|\.navAtom|\.spw\b|#splash b\b|#splash small|#splash\.ld|\.abW\b|#splash\.ab \.ab1|\.ab1 b|#splash\.ab b\.ab1'
                r'|\.car\b|\.spin button|\.tic\b|\.icg\b|\.tmrate button|\.scic\b|\.qwerty|\.qk\b')
# selectors that show time: bar and beat position, time code, time of day, work time, the time machine's clock
TIME=re.compile(r'(^|[\s,>])\.lcd\s*$|\.mpos\b|#phFlag|\.trx-tod|\.pv-tod|#tmw \.tmsl span|\.trx-work\s*$|\.pftime b')
def selector(i):
    b=s.rfind('{',max(0,i-4000),i);a=s.rfind('}',max(0,i-4000),i)
    if b==-1 or a>b:return None           # not inside a rule: a style="" attribute or a JS string
    j=max(s.rfind('}',0,b),s.rfind('{',0,b),s.rfind('`',0,b),s.rfind('*/',0,b)+1)
    return s[j+1:b].strip()[-400:]
def where(i):
    sel=selector(i)
    return sel if sel is not None else 'inline: '+s[max(0,i-160):i]
# ---- two labels were written in lower case and shown in capitals; they now start with a capital
rep('<b id="mtrPkV">–∞</b><small>peak</small>','<b id="mtrPkV">–∞</b><small>Peak</small>')
rep('<b id="mxPk">–</b><small>peak</small>','<b id="mxPk">–</b><small>Peak</small>')
REP=collections.OrderedDict(sizes=collections.Counter(),weights=collections.Counter(),fams=collections.Counter(),kept=[],odd=[],caps=[])
# ---- capital labels become sentence case: C1 has no capital section labels (they belong to C0), and 11 px capitals would be up to a third
# wider than the 8 to 10 px ones were. The text is then shown as it is written in the source; the tracking that went with the capitals goes too.
def caps(m):
    blk=m.group(0)
    if 'text-transform:uppercase' not in blk:return blk
    sel=s[max(0,m.start()-200):m.start()]
    if KEEP.search(sel.split('}')[-1]):return blk
    REP['caps'].append(sel.split('}')[-1].strip()[-70:])
    return re.sub(r'letter-spacing:\s*[^;}]+','letter-spacing:0',blk.replace('text-transform:uppercase','text-transform:none'))
s=re.sub(r'\{[^{}]*\}',caps,s)
# ---- every declaration that sets a font size or a line height gets a number (the same numbers in every mode)
PINS={}
MODE='apply'
for a_ in sys.argv[2:]:
    if a_=='--probe':MODE='probe'
    elif a_.startswith('--pins='):PINS={int(k):v for k,v in json.load(open(a_[7:])).items()}
DECL=[]   # for the probe: number, kind, old px, new px
out=[];pos=0;n=-1
PAT=re.compile(r'(?<![\w.-])(font-size|font-weight|font-family|line-height|font)(\s*:\s*)([^;}"\'\\`<]+)')
PX={'--fs1':11,'--fs2':12,'--fs3':13,'--fs4':15}
def lhpx(v):return ('%.2f'%v).rstrip('0').rstrip('.')+'px'
for m in PAT.finditer(s):
    prop,sep,val=m.group(1),m.group(2),m.group(3);imp='!important' if '!important' in val else '';v=val.replace('!important','').strip();w=where(m.start());new=None;tail=val[len(val.rstrip()):]
    if '${' in val or v=='inherit' or "'+" in val:
        if prop in('font','font-size','line-height') and v!='inherit':REP['odd'].append([prop,val[:60],w[-80:]])
        continue
    keep=bool(KEEP.search(w));mark=''
    if prop=='line-height':
        n+=1;DECL.append([n,'lh',v,None]);mark=';--d3l:%d%s'%(n,imp)
        if n in PINS and not re.fullmatch(r'[\d.]+px',v):new=lhpx(PINS[n])
    elif prop=='font-size':
        n+=1;mm=re.fullmatch(r'([\d.]+)px',v);mark=';--d3:%d%s'%(n,imp)
        if mm and not keep:
            t=size_tok(float(mm.group(1)));new='var(%s)'%t;REP['sizes'][mm.group(1)+' > '+t]+=1;DECL.append([n,'size',float(mm.group(1)),PX[t]])
        else:
            DECL.append([n,'size',float(mm.group(1)) if mm else v,float(mm.group(1)) if mm else v])
            if keep:REP['kept'].append([prop,v[:50],w[-70:]])
            elif v!='0':REP['odd'].append([prop,v[:60],w[-80:]])
        if n in PINS:
            new=(new or v)+imp+';line-height:'+lhpx(PINS[n])
    elif prop=='font-weight':
        if keep:REP['kept'].append([prop,v[:50],w[-70:]]);continue
        if re.fullmatch(r'\d{3}|normal|bold|bolder|lighter',v):t=weight_tok(v);new='var(%s)'%t;REP['weights'][v+' > '+t]+=1
        else:REP['odd'].append([prop,v[:60],w[-80:]])
    elif prop=='font-family':
        if keep:REP['kept'].append([prop,v[:50],w[-70:]]);continue
        mono='monospace' in v;t='--fft' if (mono and TIME.search(w)) else '--ffu';new='var(%s)'%t;REP['fams'][('mono' if mono else 'sans')+' > '+t]+=1
    else:
        mm=re.fullmatch(r'(?:(\d{3})\s+)?([\d.]+)px(/[\w.]+)?\s+(.+)',v)
        if not mm:REP['odd'].append([prop,v[:60],w[-80:]]);continue
        n+=1;mark=';--d3:%d%s;--d3l:%d%s'%(n,imp,n,imp)
        wt,px,lh,fam=mm.group(1) or '400',float(mm.group(2)),mm.group(3) or '',mm.group(4)
        if n in PINS and not re.fullmatch(r'/[\d.]+px',lh):lh='/'+lhpx(PINS[n])
        if keep:
            REP['kept'].append([prop,v[:50],w[-70:]]);DECL.append([n,'font',px,px])
            if n in PINS:new=(mm.group(1)+' ' if mm.group(1) else '')+mm.group(2)+'px'+lh+' '+fam
        else:
            mono='monospace' in fam or '--abmono' in fam;ft='--fft' if (mono and TIME.search(w)) else '--ffu'
            st=size_tok(px);wk=weight_tok(wt);new='var(%s) var(%s)%s var(%s)'%(wk,st,lh,ft);DECL.append([n,'font',px,PX[st],mono and ft=='--ffu'])
            if imp:new+=imp+';font-variant-numeric:tabular-nums'   # an !important shorthand would reset the equal-width digits
            REP['sizes'][mm.group(2)+' > '+st]+=1;REP['weights'][wt+' > '+wk]+=1;REP['fams'][('mono' if mono else 'sans')+' > '+ft]+=1
    if MODE=='probe':
        if mark:out.append(s[pos:m.end(3)-len(tail)]);out.append(mark+tail);pos=m.end(3)
        continue
    if new is None:continue
    out.append(s[pos:m.start(3)]);out.append(new+imp+tail);pos=m.end(3)
out.append(s[pos:]);s=''.join(out)
if MODE=='probe':
    open(f,'w',encoding='utf-8').write(s);json.dump(DECL,open(os.path.join(os.path.dirname(os.path.abspath(f)),'decl.json'),'w'));print('probe written,',n+1,'numbered declarations');sys.exit(0)
# ---- text drawn in canvases (JS font strings): only the weight. 650, 700, 800 and 900 become 600; sizes and families stay, they belong to the pictures
n_cv=[0]
def cvw(m):n_cv[0]+=1;return m.group(1)+'600 '
s=re.sub(r"""(['"`])(?:650|700|800|900) (?=(?:[\d.]+|\$\{[^}]{1,60}\}|'\+[^+']{1,60}\+')px[ /])""",cvw,s)
s=re.sub(r"""(['"`])(?:650|700|800|900) (?='\+|\$\{F\}|'\+\()""",cvw,s)
REP['canvas_weights']=n_cv[0]
# ---- the About window's own mono stack is no longer mono (its lines show no time)
rep('--abmono:ui-monospace,"SF Mono",Menlo,Consolas,monospace','--abmono:var(--ffu)')
# ---- the medium weight comes with the same font request (Inter is one variable file at Google; 800 stays for the wordmark)
rep('family=Inter:wght@400;600;800&display=swap','family=Inter:wght@400;500;600;800&display=swap')
# ---- the tokens and the base rules
css=open(os.path.join(here,'taskD3_css.txt'),encoding='utf-8').read().rstrip('\n')+'\n'
rep('.dacv{display:flex;',css+'.dacv{display:flex;')
js_path=os.path.join(here,'taskD3_block.js')
if os.path.isfile(js_path):rep('function askChoice(title,text,btns,icon){',open(js_path,encoding='utf-8').read().rstrip('\n')+'\nfunction askChoice(title,text,btns,icon){')
rep("const VERSION='0.225',BUILD='27 November 2026'","const VERSION='0.226',BUILD='27 November 2026'")
open(f,'w',encoding='utf-8').write(s)
rp=[a_ for a_ in sys.argv[2:] if not a_.startswith('--')]
if rp:json.dump(REP,open(rp[0],'w'),indent=1)
print('pins used',len(PINS));print('ok: sizes',sum(REP['sizes'].values()),'weights',sum(REP['weights'].values()),'families',sum(REP['fams'].values()),'kept',len(REP['kept']),'odd',len(REP['odd']),'canvas weights',n_cv[0])
