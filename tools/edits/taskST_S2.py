"""Task ST-S2 (settings rebuild, step S2): remember the export options (last used; file name per project) and the piano roll options
(tool, snap, chord, ghost, lane last used; scale and root in the project). One block before askChoice, from taskST_S2_block.js.
  python3 tools/edits/taskST_S2.py [index.html]"""
import sys,os
P=sys.argv[1] if len(sys.argv)>1 else 'index.html'
B=open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'taskST_S2_block.js'),encoding='utf-8').read()
s=open(P,encoding='utf-8').read()
A='function askChoice(title,text,btns,icon){'
assert s.count(A)==1 and 'const STS2=' not in s
s=s.replace(A,B.rstrip('\n')+'\n'+A)
assert s.count("export:'export wav mp3 flac render bounce mixdown dither'")==1
s=s.replace("export:'export wav mp3 flac render bounce mixdown dither'","export:'export wav mp3 flac render bounce mixdown dither remember file name format bit depth'")
open(P,'w',encoding='utf-8').write(s);print('ok')
