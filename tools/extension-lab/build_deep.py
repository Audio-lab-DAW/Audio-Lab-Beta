#!/usr/bin/env python3
"""Task EX2, the deep layer. Builds two pages from deep-src/:

  deep-layer.html                  the deep layer alone (for testing; own header and picks bar)
  extensions-with-deep-layer.html  EX1's pick page (extensions-round-1.html, not modified) with the part
                                   'Deep layer' added before the questions; this is the file that is published
                                   to the pick page artifact.

Both are artifact bodies: no doctype or head of their own. All deep layer CSS is scoped under #dlRoot,
all its script lives in one closure, so it cannot disturb EX1's prototypes."""
import pathlib,re
d=pathlib.Path(__file__).parent;src=d/'deep-src'
R=lambda n:(src/n).read_text()

def scope(css,root='#dlRoot'):
    """Prefix every selector with the root; keeps @media blocks, leaves declarations alone."""
    css=re.sub(r'/\*.*?\*/','',css,flags=re.S)
    out=[];buf='';depth=0;atdepth=set()
    for ch in css:
        if ch=='{':
            sel=buf.strip();buf=''
            if sel.startswith('@'):out.append(sel+'{');atdepth.add(depth)
            else:out.append(','.join(root+' '+x.strip() for x in sel.split(','))+'{')
            depth+=1
        elif ch=='}':
            depth-=1;out.append(buf.strip()+'}\n');buf='';atdepth.discard(depth)
        else:buf+=ch
    return ''.join(out)

part_css=scope(R('part.css'))
script='<script>\n'+R('02-core.js')+R('03-tools.js')+'</script>\n'

# 1. alone
alone=(R('page-top.html')+'<style>\n'+R('page.css')+part_css+'</style>\n'+R('page-header.html')
       +R('part.html')+R('page-foot.html')+script)
(d/'deep-layer.html').write_text(alone)

# 2. inside EX1's page
ex1=(d/'extensions-round-1.html').read_text()
tokens=('#dlRoot{--pg:#0a0a0c;--card:#121216;--pfg:#ececf1;--pmut:#8b8b97;--pline:#25252c;--brand:#7fb0ff;--brandink:#06122a;'
        '--star:#ffd23a;--starink:#2a2000;--okc:#5fd39a;--warnc:#e3b341;--badc:#ff8f8f;'
        "--disp:Inter,system-ui,sans-serif;--text:Inter,system-ui,sans-serif;--data:'JetBrains Mono',ui-monospace,Menlo,monospace;font:14px/1.5 var(--text);color:var(--pfg)}\n"
        '#dlRoot p{max-width:none}\n.dljump{border:1px solid var(--ln);border-radius:10px;padding:10px 12px;background:var(--pn);max-width:none}\n')
glue='''<script>
/* task EX2: the deep layer joins EX1's picks line */
(function(){const base=pkLine;pkLine=function(){return base()+' | '+DeepLayer.picks()};
 const draw=()=>{document.getElementById('pkLine').textContent=pkLine()};
 document.addEventListener('deeplayer-picks',draw);document.getElementById('pkStar').addEventListener('click',()=>DeepLayer.takeAll());draw()})();
</script>
'''
jump='<p class="dljump"><b>New on this page (task EX2): the deep layer.</b> For people who want to go much further than Settings: a list of every setting, hide or move any control, commands and macros, your own CSS and your own scripts, with a safe mode behind it all. <a href="#deep">Jump to the deep layer</a>. Its picks join the same line in the bar below.</p>\n'
a='</style>';assert ex1.count(a)==1
ex1=ex1.replace(a,tokens+part_css+a)
a='</header>';assert ex1.count(a)==1
ex1=ex1.replace(a,a+'\n'+jump)
a='<!-- ================= picks ================= -->';assert ex1.count(a)==1
ex1=ex1.replace(a,'<!-- ================= deep layer (task EX2) ================= -->\n'+R('part.html')+'\n'+a)
assert ex1.rstrip().endswith('</script>')
ex1=ex1.rstrip()+'\n<script>window.DeepLayerHost=true</script>\n'+script+glue
(d/'extensions-with-deep-layer.html').write_text(ex1)
for n in ('deep-layer.html','extensions-with-deep-layer.html'):print(n,len((d/n).read_bytes()),'bytes')
