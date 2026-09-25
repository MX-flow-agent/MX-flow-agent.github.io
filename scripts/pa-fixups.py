#!/usr/bin/env python3
"""Re-apply the Flow Agent fixups to Performance Analyst's exported build.

PA-demo-v4.html is a compiled single-file export of the mix-modeler-lab demo.
Every re-export replaces the bundle and drops edits made to the built file, so
the site-level fixes live here and are re-applied after each export:

    python3 scripts/pa-fixups.py              # patch PA-demo-v4.html in place
    python3 scripts/pa-fixups.py --check      # report only; exit 1 if any fix is missing

Each fix matches on structure, not on minified names (those change on every
build), is skipped when already applied, and fails loudly when its anchor is
gone, so a changed source shows up here instead of silently on the site.

Fixes:
  rail-link       AIM rail opens Brief Curator on its Monitor (#monitor)
  autoscroll      a Portfolio Overview datacut scrolls Influencer Deep Dive
                  into view when it is stacked below (< 1280px)
  tooltip         info tooltips render only while shown and stay on screen
  kpi-cards       Executive Summary cards reflow; labels never leave the card
  trend-cards     Cumulative E/R Trend cards reflow on narrow screens
  legend          Portfolio Overview legend wraps
  portfolio       Portfolio Overview table keeps 600px and scrolls sideways
  bars            contribution bars keep room for their % label
  deep-dive       Performance Change / Contributors stack when narrow
  impact-column   Impact on E/R column narrows on phones
  top-bar         top bar labels give way to icons below 600px
  map-header      map section header wraps its segmented control
  long-list       Long-list rows share one min width (aligned, full borders)
  css             the fx-fit stylesheet those hooks rely on
"""
import re
import sys
from pathlib import Path

ID = r'[\w$]+'  # a minified identifier (may contain $)

CSS = '''<style id="fx-fit">
/* Fit pass: no text leaves its box at any width (320 – 1920 px). Hooks are the
   fx-* classes added to the components they name. Written by
   scripts/pa-fixups.py; edit there, not here. */
.fx-tip { max-width: min(20rem, calc(100vw - 16px)); }
.fx-wrap { overflow-wrap: break-word; }
.fx-kpis { grid-template-columns: repeat(auto-fit, minmax(min(100%, 150px), 1fr)); }
.fx-trend { grid-template-columns: repeat(auto-fit, minmax(min(100%, 96px), 1fr)); }
.fx-scroll-x { overflow-x: auto; }
.fx-po-table { min-width: 600px; }
.fx-contrib { grid-template-columns: repeat(auto-fit, minmax(min(100%, 240px), 1fr)); }
.fx-st-a { width: 7rem; }
.fx-st-b { width: 8rem; }
.fx-st-h { white-space: nowrap; }
.fx-bar-item { padding: 16px; }
@media (max-width: 599px) {
  .fx-bar-label { display: none; }
  .fx-bar-item { padding: 16px 10px; }
}
@media (max-width: 479px) {
  .fx-st-a { width: 5rem; }
  .fx-st-b { width: 5.5rem; }
  .fx-st-h { white-space: normal; line-height: 1.2; }
}
</style>'''


class Missing(Exception):
    pass


def one(pattern, s, what):
    """The single match of pattern in s, or Missing."""
    found = list(re.finditer(pattern, s))
    if len(found) != 1:
        raise Missing(f'{what}: expected 1 match, found {len(found)}')
    return found[0]


def react_alias(s):
    """The name the bundle uses for the React namespace (A.useState → A)."""
    names = re.findall(r'(' + ID + r')\.useLayoutEffect\(', s)
    if not names:
        raise Missing('React namespace: no useLayoutEffect call found')
    return max(set(names), key=names.count)


def fix_rail_link(s):
    if '["brief","Brief Curator","Brief_Curator.html#monitor"]' in s:
        return s, False
    m = one(r'\["brief","Brief Curator","Brief_Curator\.html(#[\w-]*)?"\]', s, 'rail link')
    return s[:m.start()] + '["brief","Brief Curator","Brief_Curator.html#monitor"]' + s[m.end():], True


def fix_autoscroll(s):
    if 'matchMedia("(min-width: 1280px)").matches||requestAnimationFrame' in s:
        return s, False
    panel = one(r'\.jsx\("div",\{ref:(' + ID + r'),style:(' + ID + r')!=null\?\{width:\2\}', s, 'Deep Dive panel ref')
    ref = panel.group(1)
    call = one(r'onSelectGroup:\((' + ID + r'),(' + ID + r')\)=>(' + ID + r')\(\1\)\(\2\)\}\)(?=,' + ID +
               r'\.jsx\("div",\{className:"hidden xl:block")', s, 'Portfolio Overview onSelectGroup')
    sel = one(r'\.jsx\(' + ID + r',\{analysisRecords:' + ID + r',selectedGroup:(' + ID + r')&&\(\1\.axis==="tier"',
              s[max(0, call.start() - 400):call.start()], 'Portfolio Overview selection').group(1)
    a, b, pick = call.group(1), call.group(2), call.group(3)
    new = ('onSelectGroup:(' + a + ',' + b + ')=>{const off=' + sel + '&&' + sel + '.axis===' + a + '&&' + sel + '.key===' + b +
           ';' + pick + '(' + a + ')(' + b + ');off||matchMedia("(min-width: 1280px)").matches||requestAnimationFrame(()=>{'
           'const el=' + ref + '.current;if(!el)return;const top=el.getBoundingClientRect().top;'
           'if(top>=0&&top<window.innerHeight*.5)return;window.scrollTo({top:window.scrollY+top-24,'
           'behavior:matchMedia("(prefers-reduced-motion: reduce)").matches?"auto":"smooth"})})}})')
    return s[:call.start()] + new + s[call.end():], True


def fix_tooltip(s):
    if 'fx-tip pointer-events-none' in s:
        return s, False
    R = react_alias(s)
    m = one(r'function (' + ID + r')\(\{text:e,children:t\}\)\{return (' + ID + r')\.jsxs\("span",\{className:"group relative inline-flex",'
            r'tabIndex:0,children:\[t,\2\.jsx\("span",\{role:"tooltip",className:"pointer-events-none invisible absolute top-full '
            r'left-0 z-50 mt-1\.5 w-max max-w-xs opacity-0 transition-opacity group-hover:visible group-hover:opacity-100 '
            r'group-focus-visible:visible group-focus-visible:opacity-100",style:\{', s, 'tooltip component')
    fn, k = m.group(1), m.group(2)
    new = ('function ' + fn + '({text:e,children:t}){const[fo,fso]=' + R + '.useState(!1),[fx,fsx]=' + R + '.useState(0),fr=' + R +
           '.useRef(null),fd=' + R + '.useRef(0);' + R + '.useLayoutEffect(()=>{if(!fo||!fr.current)return;const b=fr.current.'
           'getBoundingClientRect(),w=document.documentElement.clientWidth,l=b.left-fd.current,rt=l+b.width,d=rt>w-8?'
           'Math.max(8-l,w-8-rt):l<8?8-l:0;fd.current=d,fsx(d)},[fo]);const fon=()=>fso(!0),foff=()=>{fso(!1),fd.current=0,fsx(0)};'
           'return ' + k + '.jsxs("span",{className:"group relative inline-flex",tabIndex:0,onMouseEnter:fon,onMouseLeave:foff,'
           'onFocus:fon,onBlur:foff,children:[t,fo&&' + k + '.jsx("span",{role:"tooltip",ref:fr,className:"fx-tip '
           'pointer-events-none absolute top-full left-0 z-50 mt-1.5 w-max",style:{transform:`translateX(${fx}px)`,')
    return s[:m.start()] + new + s[m.end():], True


def fix_kpi_cards(s):
    if 'fx-kpis' in s.split('<style id="fx-fit">')[0]:
        return s, False
    grid = one(r'className:"mt-4 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5"', s, 'KPI grid')
    s = s[:grid.start()] + 'className:"fx-kpis mt-4 grid gap-3"' + s[grid.end():]
    card = one(r'(function ' + ID + r'\(\{label:e,value:t,badge:a,sub:r\}\)\{return ' + ID + r'\.jsxs\("div",\{className:)"flex flex-col gap-2"'
               r'(,style:\{padding:16,[^}]*\},children:\[' + ID + r'\.jsx\("span",\{)(style:\{)', s, 'KPI card')
    return s[:card.start()] + card.group(1) + '"flex min-w-0 flex-col gap-2"' + card.group(2) + 'className:"fx-wrap",' + card.group(3) + s[card.end():], True


def simple(marker, old, new, what):
    def fix(s):
        if marker in s.split('<style id="fx-fit">')[0]:
            return s, False
        m = one(re.escape(old), s, what)
        return s[:m.start()] + new + s[m.end():], True
    return fix


fix_trend_cards = simple('fx-trend', 'className:"grid grid-cols-3 gap-2"', 'className:"fx-trend grid gap-2"', 'trend cards')


def fix_legend(s):
    # Anchored on the legend's first item: other rows share these classes.
    tail = r'",style:\{\.\.\.' + ID + r'\.label,color:' + ID + r'\.default\},children:\[' + ID + r'\.jsx\(' + ID + r',\{color:' + ID + r',label:"Po\.Reach Contribution"'
    if re.search(r'className:"mt-3 flex flex-wrap items-center gap-4' + tail, s):
        return s, False
    m = one(r'className:"mt-3 flex items-center gap-4(?=' + tail + ')', s, 'Portfolio legend')
    return s[:m.start()] + 'className:"mt-3 flex flex-wrap items-center gap-4' + s[m.end():], True


def fix_portfolio(s):
    if 'fx-po-table' in s.split('<style id="fx-fit">')[0]:
        return s, False
    start = one(r'(' + ID + r')\.jsxs\("div",\{className:"mt-3 grid items-center rounded-\[3px\] px-3"', s, 'Portfolio header')
    k = start.group(1)
    end = one(r',' + ID + r'\.jsx\("p",\{className:"mt-3 border-t pt-3"', s[start.start():], 'Portfolio caption')
    body = s[start.start():start.start() + end.start()]
    if body.count('.jsx("div",{className:"grid px-3"') != 1:
        raise Missing('Portfolio rows: expected one rows grid')
    body = body.replace('className:"mt-3 grid items-center rounded-[3px] px-3"', 'className:"grid items-center rounded-[3px] px-3"', 1)
    wrapped = k + '.jsx("div",{className:"fx-scroll-x mt-3",children:' + k + '.jsxs("div",{className:"fx-po-table",children:[' + body + ']})})'
    return s[:start.start()] + wrapped + s[start.start() + end.start():], True


def fix_bars(s):
    if 'style:{minWidth:56,height:a,' in s:
        return s, False
    m = one(r'(function ' + ID + r'\(\{pct:e,color:t,height:a=20\}\)\{return ' + ID +
            r'\.jsxs\("div",\{className:"relative w-full overflow-hidden rounded-\[3px\]",style:\{)(height:a,)', s, 'contribution bar')
    return s[:m.start()] + m.group(1) + 'minWidth:56,' + m.group(2) + s[m.end():], True


def fix_deep_dive(s):
    changed = False
    for section in ('performance-change', 'performance-contributors'):
        at = one(r'id:"' + section + '"', s, section).end()
        window = s[at:at + 700]
        if 'className:"fx-contrib grid gap-3"' in window:
            continue
        g = window.find('className:"grid grid-cols-2 gap-3"')
        if g < 0:
            raise Missing(section + ': two-column grid not found')
        s = s[:at + g] + 'className:"fx-contrib grid gap-3"' + s[at + g + len('className:"grid grid-cols-2 gap-3"'):]
        changed = True
    return s, changed


def fix_impact_column(s):
    head = one(r'children:"Impact on E/R"', s, 'Impact on E/R header')
    fn = s.rfind('function ', 0, head.start())
    end = s.find('function ', head.end())
    body = s[fn:end]
    if 'fx-st-a' in body:
        return s, False
    new = re.sub(r'className:"w-28((?: shrink-0)?) text-right whitespace-nowrap"', r'className:"fx-st-a fx-st-h\1 text-right"', body)
    new = re.sub(r'className:"w-32((?: shrink-0)?) text-right whitespace-nowrap"', r'className:"fx-st-b fx-st-h\1 text-right"', new)
    new = re.sub(r'className:"w-28((?: shrink-0)?) text-right tabular-nums"', r'className:"fx-st-a\1 text-right tabular-nums"', new)
    new = re.sub(r'className:"w-32((?: shrink-0)?) text-right tabular-nums"', r'className:"fx-st-b\1 text-right tabular-nums"', new)
    if new == body:
        raise Missing('Impact on E/R column: fixed-width classes not found')
    return s[:fn] + new + s[end:], True


def fix_top_bar(s):
    if 'fx-bar-item' in s.split('<style id="fx-fit">')[0]:
        return s, False
    m = one(r'(function ' + ID + r'\(\{label:e,last:t,children:a\}\)\{return (' + ID + r')\.jsxs\("div",\{className:)"flex items-center justify-center"'
            r',style:\{height:56,padding:16,(gap:8,.{0,160}?\},children:\[e&&\2\.jsx\("span",\{)(style:\{)', s, 'top bar item')
    return (s[:m.start()] + m.group(1) + '"fx-bar-item flex items-center justify-center",title:e,style:{height:56,' + m.group(3) +
            'className:"fx-bar-label",' + m.group(4) + s[m.end():]), True


def fix_map_header(s):
    m = list(re.finditer(r'\.jsxs\("section",\{style:\{\.\.\.' + ID + r',padding:' + ID + r'\.card\},children:\[' + ID +
                         r'\.jsxs\("div",\{className:"flex (flex-wrap )?items-start justify-between gap-3"', s))
    todo = [x for x in m if not x.group(1)]
    if not m:
        raise Missing('map header: not found')
    if not todo:
        return s, False
    for x in reversed(todo):
        s = s[:x.start()] + x.group(0).replace('className:"flex items-start', 'className:"flex flex-wrap items-start') + s[x.end():]
    return s, True


def fix_long_list(s):
    if 'fxZw=' in s:
        return s, False
    m = one(r'\[(' + ID + r'),' + ID + r'\]=' + ID + r'\.useState\(' + ID + r'\),(' + ID + r')=(' + ID + r')\(\1\),', s, 'Long-list column state')
    cols, tpl, fn = m.group(1), m.group(2), m.group(3)
    one(re.escape(fn) + r'=e=>`24px minmax\(0,1fr\) \$\{e\.archetype\}px', s, 'Long-list column template')
    # Fixed columns + gaps (5×12) + padding (2×16) + a 104px floor for the name column:
    # the 560px desktop panel fits without sideways scroll.
    s = s[:m.end()] + 'fxZw=24+104+' + '+'.join(cols + '.' + c for c in ('archetype', 'tier', 'reach', 'er')) + '+60+32,' + s[m.end():]
    for row in ('sticky top-0 z-20 grid items-center gap-3 border-b px-4', 'grid items-center gap-3 border-b px-4 py-2.5'):
        r = one(r'className:"' + re.escape(row) + r'",style:\{gridTemplateColumns:' + re.escape(tpl) + ',', s, 'Long-list row: ' + row)
        s = s[:r.end()] + 'minWidth:fxZw,' + s[r.end():]
    return s, True


def fix_css(s):
    block = re.search(r'<style id="fx-fit">.*?</style>', s, re.S)
    if block:
        if block.group(0) == CSS:
            return s, False
        return s[:block.start()] + CSS + s[block.end():], True
    m = one(r'</head>', s, '</head>')
    return s[:m.start()] + CSS + '\n' + s[m.start():], True


FIXES = [
    ('rail-link', fix_rail_link), ('autoscroll', fix_autoscroll), ('tooltip', fix_tooltip),
    ('kpi-cards', fix_kpi_cards), ('trend-cards', fix_trend_cards), ('legend', fix_legend),
    ('portfolio', fix_portfolio), ('bars', fix_bars), ('deep-dive', fix_deep_dive),
    ('impact-column', fix_impact_column), ('top-bar', fix_top_bar), ('map-header', fix_map_header),
    ('long-list', fix_long_list), ('css', fix_css),
]


def main(argv):
    check = '--check' in argv
    args = [a for a in argv if not a.startswith('--')]
    path = Path(args[0]) if args else Path(__file__).resolve().parent.parent / 'PA-demo-v4.html'
    s = path.read_text(encoding='utf-8')
    failed = pending = 0
    for name, fix in FIXES:
        try:
            s, changed = fix(s)
        except Missing as e:
            print(f'  FAIL     {name:14} {e}')
            failed += 1
            continue
        status = ('missing' if check else 'applied') if changed else 'ok'
        pending += changed
        print(f'  {status:8} {name}')
    if check:
        print(f'{path.name}: {pending} fix(es) missing, {failed} anchor(s) not found')
        return 1 if pending or failed else 0
    if failed:
        print(f'{path.name}: not written, {failed} anchor(s) not found. Update the pattern in {Path(__file__).name}.')
        return 1
    if pending:
        path.write_text(s, encoding='utf-8')
    print(f'{path.name}: {pending} fix(es) applied')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
