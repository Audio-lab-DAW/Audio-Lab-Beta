"""Task XT-DL5: UI rules, hide and rename a control, the right-click Advanced entries (lane H). Needs XT-DL1 and XT-DL4 in the file.
Inserts taskXT_DL5_block.js before askChoice and bumps VERSION. No CSS (the hide rules make their own small stylesheet only when used).
  python3 tools/edits/taskXT_DL5.py [index.html]"""
import sys, os, re
P = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
H = os.path.dirname(os.path.abspath(__file__))
s = open(P, encoding='utf-8').read()
blk = open(os.path.join(H, 'taskXT_DL5_block.js'), encoding='utf-8').read()
assert 'task XT-DL5' not in s, 'already applied'
for d in ('task XT-DL1', 'task XT-DL4'):
    assert d in s, d + ' first'
for n in ('XT_RULE_PROTECT', 'XT_RL', 'xtRulesAll', 'xtRuleId', 'xtRuleCheck', 'xtRuleClean', 'xtRulesApply', 'xtRenArea', 'xtRenOn', 'xtRenOff', 'xtRuleSet',
          'xtRuleOf', 'xtRuleWhere', 'xtRuleArea', 'xtAdvItems', 'xtRuleHowBack', 'xtRuleHideAsk', 'xtRuleCustom', 'xtRulesCss', 'XT_HOOKS.rules', 'xtRuleSeen', 'UI.xtRules'):
    assert not re.search(r'\b' + re.escape(n) + r'\b', s), n + ' exists already'
for n in ('function xtTag(area)', 'function xtControlOf(el)', 'function xtChgList(stored)', 'function xtChgUndo(kind,id)', 'function openMenu(cx,cy,items)', 'function askText(title,val)'):
    assert s.count(n) == 1, n
A = 'function askChoice(title,text,btns,icon){'
assert s.count(A) == 1
m = re.findall(r"const VERSION='(\d+)\.(\d+)'", s); assert len(m) == 1
v = '%s.%03d' % (m[0][0], int(m[0][1]) + 1)
s = s.replace(A, blk.replace('v0.000', 'v' + v) + A)
s = re.sub(r"const VERSION='\d+\.\d+'", "const VERSION='%s'" % v, s)
open(P, 'w', encoding='utf-8').write(s); print('ok', v)
