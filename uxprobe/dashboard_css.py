"""Stylesheet for the HTML dashboard. Kept apart from the renderer so the
Python stays readable; nothing here is interpolated, it is pasted in whole.

Design system: a quiet, paper-and-ink surface with a light Japanese sensibility.
Washi ground, sumi ink, generous negative space, hairline rules instead of
boxes, vertical labels read top to bottom, square hanko-style seals for
outcomes, and traditional colours: kuchinashi yellow as the one accent,
vermilion only for the seal mark, beni / daidai / ai / moegi for severity.
System font stack, so nothing is downloaded and a report works offline. The
dark theme is the same palette at night.
"""

DASHBOARD_CSS = r"""
@property --h{syntax:'<length>';inherits:true;initial-value:0px}
@property --yaw{syntax:'<angle>';inherits:true;initial-value:-32deg}
*{margin:0;box-sizing:border-box}
:root{
  color-scheme:light;
  --bg:#f4efe6; --panel:#faf6ee; --panel-2:#efe9dd; --raise:#e6dfd0; --raise-2:#d8d0bf;
  --ink:#1f1d1a; --ink-soft:#3f3b35; --muted:#7a756b; --faint:#b3ad9f;
  --line:rgba(31,29,26,.1); --line-2:rgba(31,29,26,.17); --line-3:rgba(31,29,26,.28);
  --accent:#f5c33b; --accent-ink:#8a6a00; --accent-bg:#fbeec4; --on-accent:#1f1d1a;
  --seal:#d64533;
  --blocker:#c9313d; --major:#e8792c; --minor:#3b6ea8; --nitpick:#8c877c; --ok:#5f9e4a;
  --fr1:#f1cfa4; --fr2:var(--major); --fr3:var(--blocker);
  --fr0-side:#cbc3b2; --fr1-side:#c9a071; --fr2-side:#b25514; --fr3-side:#8f1f29;
  --stage:#ece6d9; --stage-ink:#1f1d1a;
  --shadow:none;
  --shadow-2:0 24px 60px -24px rgba(31,29,26,.35);
  --r:8px;
  --sans:-apple-system,BlinkMacSystemFont,"SF Pro Text","SF Pro Display","Segoe UI Variable Text","Segoe UI",Roboto,"Helvetica Neue",Helvetica,Arial,sans-serif;
  --mono:ui-monospace,"SF Mono",Menlo,Consolas,"Cascadia Mono",monospace;
  --ease:cubic-bezier(.25,.8,.25,1);
}
@media(prefers-color-scheme:dark){:root:not([data-theme="light"]){
  color-scheme:dark;
  --bg:#14130f; --panel:#1c1a16; --panel-2:#221f1a; --raise:#2b2822; --raise-2:#38342c;
  --ink:#ede7da; --ink-soft:#cfc8b8; --muted:#9b958a; --faint:#635d54;
  --line:rgba(237,231,218,.1); --line-2:rgba(237,231,218,.16); --line-3:rgba(237,231,218,.26);
  --accent:#f2c744; --accent-ink:#f2c744; --accent-bg:rgba(242,199,68,.16); --on-accent:#1f1d1a;
  --seal:#e2543f;
  --blocker:#e0505a; --major:#ef8c3c; --minor:#6f9bd6; --nitpick:#8c877c; --ok:#7fbc63;
  --fr1:#6b4a26; --fr0-side:#151410; --fr1-side:#3d2a14; --fr2-side:#9c5218; --fr3-side:#8f2a32;
  --stage:#1a1814; --stage-ink:#ede7da;
  --shadow-2:0 24px 60px -24px rgba(0,0,0,.8);
}}
:root[data-theme="dark"]{
  color-scheme:dark;
  --bg:#14130f; --panel:#1c1a16; --panel-2:#221f1a; --raise:#2b2822; --raise-2:#38342c;
  --ink:#ede7da; --ink-soft:#cfc8b8; --muted:#9b958a; --faint:#635d54;
  --line:rgba(237,231,218,.1); --line-2:rgba(237,231,218,.16); --line-3:rgba(237,231,218,.26);
  --accent:#f2c744; --accent-ink:#f2c744; --accent-bg:rgba(242,199,68,.16); --on-accent:#1f1d1a;
  --seal:#e2543f;
  --blocker:#e0505a; --major:#ef8c3c; --minor:#6f9bd6; --nitpick:#8c877c; --ok:#7fbc63;
  --fr1:#6b4a26; --fr0-side:#151410; --fr1-side:#3d2a14; --fr2-side:#9c5218; --fr3-side:#8f2a32;
  --stage:#1a1814; --stage-ink:#ede7da;
  --shadow-2:0 24px 60px -24px rgba(0,0,0,.8);
}
html,body{height:100%}
body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.6 var(--sans);font-weight:400;
  -webkit-font-smoothing:antialiased;text-rendering:optimizeLegibility}
::selection{background:var(--accent);color:var(--on-accent)}
a{color:inherit;text-decoration:none}
a.tx{color:var(--ink);text-decoration:underline;text-decoration-color:var(--line-3);text-underline-offset:4px;text-decoration-thickness:1px}
a.tx:hover{text-decoration-color:var(--ink)}
button{font:inherit;color:inherit}
:focus-visible{outline:2px solid var(--accent);outline-offset:3px}
kbd{font:500 .68rem/1 var(--sans);color:var(--muted);border:1px solid var(--line-2);border-radius:4px;padding:3px 6px;min-width:20px;text-align:center;display:inline-block}
.ic{width:16px;height:16px;flex:none;display:inline-block;vertical-align:middle}
.mono{font-family:var(--mono)}
.num{font-variant-numeric:tabular-nums}
/* small caps labels, letterspaced: the ledger voice */
.navlabel,.eyebrow,th,.jm-head>div,.mx th,.ro .k,.rp-card .lbl,.rp-kv .lbl,.rp-chrome .dev{font-size:.66rem;font-weight:600;letter-spacing:.16em;text-transform:uppercase;color:var(--muted)}
/* vertical labels, read top to bottom */
.vert{writing-mode:vertical-rl;text-orientation:mixed;white-space:nowrap}

/* washi: a fibrous, faint texture */
.grain{position:fixed;inset:0;z-index:80;pointer-events:none;opacity:.05;
  background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='200' height='200'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.55' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E")}
:root[data-theme="dark"] .grain{opacity:.06}
@media(prefers-color-scheme:dark){:root:not([data-theme="light"]) .grain{opacity:.06}}

/* ---------------------------------------------------------------- shell */
.app{display:grid;grid-template-columns:236px minmax(0,1fr);min-height:100vh}
.side{position:sticky;top:0;height:100vh;overflow:hidden auto;background:var(--bg);
  display:flex;flex-direction:column;padding:22px 18px 18px 22px;gap:2px;scrollbar-width:thin;border-right:1px solid var(--line-2)}
.side-top{display:flex;align-items:center;gap:8px;padding:0 0 22px}
.brand{display:flex;align-items:center;gap:11px;min-width:0}
.brand .mark{width:28px;height:28px;border-radius:5px;flex:none;display:grid;place-items:center;
  background:var(--seal);color:#fbf6ec;perspective:200px}
.brand .mark .logo{width:17px;height:17px;display:block;transition:transform .9s var(--ease)}
.brand:hover .mark .logo{transform:rotateY(360deg)}
.brand .word{font-weight:600;letter-spacing:-.01em;font-size:.98rem;white-space:nowrap}
.brand .word span{color:var(--muted);font-weight:400}
.side-toggle{margin-left:auto;flex:none;width:28px;height:28px;display:grid;place-items:center;
  border:0;border-radius:5px;background:transparent;color:var(--muted);cursor:pointer;transition:color .2s,background .2s}
.side-toggle:hover{color:var(--ink);background:var(--raise)}
.side-toggle .ic{width:16px;height:16px}
.navlabel{padding:18px 0 8px;display:flex;align-items:center;gap:10px}
.navlabel::after{content:"";flex:1;height:1px;background:var(--line)}
.nav{display:flex;flex-direction:column;gap:1px}
.nav a{display:flex;align-items:center;gap:10px;padding:7px 8px 7px 14px;border-radius:5px;position:relative;
  color:var(--ink-soft);font-weight:400;font-size:.92rem;cursor:pointer;transition:background .2s,color .2s;min-width:0}
.nav a::before{content:"";position:absolute;left:0;top:50%;width:3px;height:16px;border-radius:2px;background:var(--accent);transform:translateY(-50%) scaleY(0);transition:transform .25s var(--ease)}
.nav a .ic{width:17px;height:17px;flex:none;color:var(--faint)}
.nav a .n{margin-left:auto;font-variant-numeric:tabular-nums;color:var(--faint);font-size:.76rem}
.nav a .k{margin-left:auto;opacity:0;transition:opacity .2s}
.nav a:hover{color:var(--ink);background:var(--panel-2)}
.nav a:hover .k{opacity:1}
.js .nav a.active{color:var(--ink);font-weight:600;background:transparent}
.js .nav a.active::before{transform:translateY(-50%) scaleY(1)}
.js .nav a.active .ic{color:var(--ink)}
.nav a.pp{gap:9px}
.nav a.pp .ava{width:24px;height:24px;border-radius:5px}
.nav a.pp .nm{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
svg.st{width:12px;height:12px;flex:none;display:inline-block;vertical-align:-2px;color:var(--faint)}
.nav a.pp svg.st{margin-left:auto}
.st.completed{color:var(--ok)} .st.partial{color:var(--major)}
.st.abandoned,.st.failed{color:var(--blocker)} .st.unknown{color:var(--faint)}
svg.g{width:11px;height:11px;flex:none;display:inline-block;vertical-align:-1px}
.g.blocker{color:var(--blocker)} .g.major{color:var(--major)} .g.minor{color:var(--minor)} .g.nitpick{color:var(--nitpick)} .g.none{color:var(--faint)}
.side .foot{margin-top:auto;padding:14px 0 0;color:var(--muted);font-size:.76rem;line-height:1.6;border-top:1px solid var(--line)}
.side .foot .row{display:flex;justify-content:space-between;gap:8px}
.side .foot .row span:last-child{color:var(--ink);font-variant-numeric:tabular-nums;text-align:right}
.side .foot .name{color:var(--ink);font-weight:600;font-size:.84rem;margin-bottom:8px;word-break:break-word}
/* collapsed rail */
.app.collapsed{grid-template-columns:64px minmax(0,1fr)}
.app.collapsed .side{padding:22px 10px 18px;align-items:stretch}
.app.collapsed .side-top{flex-direction:column;gap:12px;padding:0 0 12px;align-items:center}
.app.collapsed .brand .word,.app.collapsed .navlabel,.app.collapsed .nav a .n,.app.collapsed .nav a .k,
.app.collapsed .nav a span.lbl,.app.collapsed .nav a .nm,.app.collapsed .nav a.pp .st,.app.collapsed .side .foot{display:none}
.app.collapsed .side-toggle{margin:0}
.app.collapsed .nav a{justify-content:center;padding:9px 0}
.app.collapsed .nav a::before{left:2px}
.app.collapsed .nav{gap:4px}

/* ---------------------------------------------------------------- top bar */
.main{min-width:0;display:flex;flex-direction:column}
.topbar{position:sticky;top:0;z-index:20;display:flex;align-items:center;gap:10px;
  padding:0 40px;height:56px;background:color-mix(in srgb,var(--bg) 94%,transparent);border-bottom:1px solid var(--line)}
.crumb{display:flex;align-items:center;gap:10px;color:var(--muted);font-size:.86rem;min-width:0;white-space:nowrap}
.crumb b{color:var(--ink);font-weight:600;overflow:hidden;text-overflow:ellipsis}
.crumb .sep{color:var(--faint)}
.tb-right{margin-left:auto;display:flex;align-items:center;gap:8px}
.search{display:flex;align-items:center;gap:8px;height:32px;padding:0 10px;border-radius:5px;border:1px solid var(--line-2);background:transparent;
  color:var(--muted);min-width:230px;transition:border-color .2s,background .2s}
.search:focus-within{border-color:var(--ink);background:var(--panel);color:var(--ink)}
.search .ic{width:15px;height:15px}
.search input{flex:1;border:0;background:transparent;color:var(--ink);font:inherit;font-size:.88rem;outline:0;min-width:0}
.search input::placeholder{color:var(--faint)}
.tbtn{height:32px;min-width:32px;padding:0 10px;display:inline-flex;align-items:center;gap:7px;border:1px solid var(--line-2);
  border-radius:5px;background:transparent;color:var(--ink-soft);cursor:pointer;font-size:.82rem;font-weight:500;transition:border-color .2s,color .2s;white-space:nowrap}
.tbtn:hover{border-color:var(--ink);color:var(--ink)}
.tbtn .ic{width:16px;height:16px}
.tbtn .sun,.tbtn .moon{display:none}
:root[data-theme="light"] .tbtn .moon{display:inline-block}
:root[data-theme="dark"] .tbtn .sun{display:inline-block}
:root:not([data-theme]) .tbtn .moon{display:inline-block}
@media(prefers-color-scheme:dark){:root:not([data-theme]) .tbtn .moon{display:none}:root:not([data-theme]) .tbtn .sun{display:inline-block}}
details.menu{position:relative}
details.menu summary{list-style:none;cursor:pointer}
details.menu summary::-webkit-details-marker{display:none}
details.menu .dd{position:absolute;right:0;top:40px;z-index:30;min-width:260px;background:var(--panel);border:1px solid var(--line-2);
  border-radius:6px;padding:6px;box-shadow:var(--shadow-2)}
details.menu .dd a{display:flex;align-items:center;gap:10px;padding:9px 10px;border-radius:4px;color:var(--ink);font-size:.86rem}
details.menu .dd a:hover{background:var(--panel-2)}
details.menu .dd a .ic{width:15px;height:15px;color:var(--muted)}
details.menu .dd a small{margin-left:auto;color:var(--muted);font-size:.72rem;font-variant-numeric:tabular-nums}

/* ---------------------------------------------------------------- views */
.content{padding:36px 40px 96px;width:100%}
.view{display:block}
.js .anchor{display:none}
.js .view{display:none}
.js .view.active{display:block;animation:fade .5s var(--ease)}
@keyframes fade{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}
.vhead{margin:0 0 30px;display:flex;align-items:flex-end;gap:24px;flex-wrap:wrap}
.vhead > div:first-child{display:grid;grid-template-columns:auto 1fr;column-gap:18px;align-items:start}
.vhead .eyebrow{grid-row:1/3;writing-mode:vertical-rl;text-orientation:mixed;white-space:nowrap;margin:0;padding-top:4px;border-left:1px solid var(--line-3);padding-left:10px;line-height:1}
.vhead h1{grid-column:2;font-size:2.4rem;font-weight:500;letter-spacing:-.03em;line-height:1.1}
.vhead p{grid-column:2;color:var(--muted);font-size:.96rem;margin-top:10px;max-width:62ch;line-height:1.6}
.eyebrow{display:flex;align-items:center;gap:8px;flex-wrap:wrap}
.eyebrow i{display:none}
.eyebrow b{color:var(--ink);font-weight:600;font-variant-numeric:tabular-nums}
.vhead .right{margin-left:auto;display:flex;gap:8px;align-items:center}

/* hero: the verdict, then the readouts as a ledger row */
.hero{padding:0}
.hero .eyebrow{letter-spacing:.04em;text-transform:none;font-size:.84rem;font-weight:400;color:var(--muted)}
.hero .eyebrow .right{margin-left:auto}
.hero-grid{display:grid;grid-template-columns:auto minmax(0,1fr) minmax(280px,360px);gap:28px;align-items:center;margin:26px 0 34px}
.hero-grid .vlabel{writing-mode:vertical-rl;text-orientation:mixed;white-space:nowrap;font-size:.66rem;font-weight:600;letter-spacing:.16em;text-transform:uppercase;color:var(--muted);
  border-left:1px solid var(--line-3);padding-left:10px;align-self:start;padding-top:6px;line-height:1}
.verdict{font-size:clamp(1.7rem,2.6vw,2.6rem);font-weight:500;letter-spacing:-.03em;line-height:1.15;margin:0;max-width:60ch}
.verdict .lead{display:block}
.verdict .top{display:block;margin-top:14px;font-size:1rem;font-weight:400;letter-spacing:0;line-height:1.6;color:var(--muted);max-width:74ch}
.verdict .top .pill{margin-right:8px;vertical-align:2px}
.verdict .top em{font-style:normal;color:var(--ink);font-weight:500}
.fp{margin:0;padding:0;position:relative;border-left:1px solid var(--line-2);padding-left:22px}
.fp svg{display:block;width:100%;height:auto}
.fp path.a{fill:var(--bg);stroke:none}
.fp path.a.fl{fill:var(--panel-2)}
.fp path.r{fill:none;stroke:var(--ink);stroke-width:1.4;stroke-linejoin:round;stroke-linecap:round;vector-effect:non-scaling-stroke}
.fp circle.peak{fill:var(--seal);stroke:none}
.fp figcaption{display:flex;justify-content:space-between;gap:10px;color:var(--muted);font-size:.72rem;margin-top:8px}
.fp figcaption b{color:var(--ink);font-weight:600}
.js .fp path.r{stroke-dasharray:1;stroke-dashoffset:1;transition:stroke-dashoffset 1.8s var(--ease)}
.js .fp.in path.r{stroke-dashoffset:0}
.js .fp circle.peak{opacity:0;transition:opacity .5s 1.5s}
.js .fp.in circle.peak{opacity:1}
.readouts{display:grid;grid-template-columns:repeat(5,1fr);border-top:1px solid var(--line-2);border-bottom:1px solid var(--line-2);margin-bottom:34px}
.ro{display:grid;grid-template-columns:auto 1fr;column-gap:14px;align-items:start;padding:20px 18px 18px 0;position:relative;min-width:0}
.ro + .ro{padding-left:22px;border-left:1px solid var(--line)}
.ro .k{grid-row:1/3;writing-mode:vertical-rl;text-orientation:mixed;white-space:nowrap;line-height:1;padding-top:4px}
.ro .v{grid-column:2;font-size:3rem;font-weight:300;line-height:1;letter-spacing:-.03em;font-variant-numeric:tabular-nums;display:flex;align-items:baseline;gap:3px}
.ro .v small{font-size:1.1rem;color:var(--faint);font-weight:400}
.ro .v.blocker{color:var(--blocker)} .ro .v.ok{color:var(--ok)} .ro .v.acc{color:var(--accent-ink)}
.ro .note{grid-column:2;color:var(--muted);font-size:.78rem;margin-top:8px}

/* sections: rules and air, not boxes */
.panel{background:transparent;border-top:1px solid var(--line-2);border-radius:0;min-width:0;position:relative;padding-bottom:6px}
.panel + .panel,.grid2 + .panel,.panel + .grid2{margin-top:22px}
.panel .ph{padding:16px 0 12px;display:flex;align-items:center;gap:12px;flex-wrap:wrap}
.panel .ph h3{font-size:1.1rem;font-weight:500;letter-spacing:-.015em;display:flex;align-items:center;gap:8px}
.panel .ph h3 .idx{display:none}
.panel .ph .sub{color:var(--muted);font-size:.86rem}
.panel .ph .right{margin-left:auto;display:flex;gap:8px;align-items:center;color:var(--muted);font-size:.8rem}
.panel .pb{padding:4px 0 14px}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:40px;margin-top:22px}
.grid2 .panel{margin:0}
/* segmented toggle: a hairline box, the active segment inked */
.seg{display:inline-flex;border:1px solid var(--line-2);border-radius:5px;overflow:hidden}
.seg button{border:0;background:transparent;color:var(--ink-soft);font-size:.78rem;font-weight:500;padding:5px 12px;cursor:pointer;
  display:inline-flex;align-items:center;gap:6px;transition:background .2s,color .2s}
.seg button + button{border-left:1px solid var(--line-2)}
.seg button.on{background:var(--accent);color:var(--on-accent);font-weight:600}
.seg button .ic{width:13px;height:13px}

/* distribution bars */
.dist{display:flex;height:8px;overflow:hidden;background:var(--raise);gap:2px}
.dist i{display:block;height:100%;transform-origin:left;transition:transform 1.1s var(--ease)}
.js .dist:not(.in) i{transform:scaleX(0)}
.sev-blocker{background:var(--blocker)} .sev-major{background:var(--major)}
.sev-minor{background:var(--minor)} .sev-nitpick{background:var(--nitpick)}
.seg-completed{background:var(--ok)} .seg-partial{background:var(--major)}
.seg-abandoned{background:var(--blocker)} .seg-failed{background:var(--faint)} .seg-unknown{background:var(--faint)}
.lg{display:flex;flex-wrap:wrap;gap:16px;margin-top:12px;font-size:.82rem;color:var(--muted)}
.lg span{display:inline-flex;align-items:center;gap:7px}
.lg svg{width:11px;height:11px;flex:none}
.lg b{color:var(--ink);font-weight:600;font-variant-numeric:tabular-nums}

/* ---------------------------------------------------------------- friction landscape (CSS 3D) */
.jpanel[data-mode="land"] .jm-wrap{display:none}
.jpanel[data-mode="map"] .land{display:none}
.land{position:relative;height:var(--land-h,320px);perspective:1500px;perspective-origin:50% 40%;overflow:hidden;
  background:var(--stage);border:1px solid var(--line);border-radius:6px;margin:4px 0 6px;cursor:grab;user-select:none;touch-action:none}
.land:active{cursor:grabbing}
.land .stage{position:absolute;left:52%;top:46%;transform-style:preserve-3d;--tilt:60deg;
  transform:translate(-50%,-50%) scale(var(--zoom,1)) rotateX(var(--tilt)) rotateZ(var(--yaw))}
.land .ground{position:absolute;left:0;top:0;transform:translateZ(-1px);border:1px solid var(--line-2);
  background-image:linear-gradient(var(--line) 1px,transparent 1px),linear-gradient(90deg,var(--line) 1px,transparent 1px);
  background-size:var(--u) var(--u)}
.land .bar{position:absolute;width:var(--u);height:var(--u);transform-style:preserve-3d;cursor:pointer;
  left:calc(var(--c)*var(--u));top:calc(var(--r)*var(--pitch));--col:var(--raise-2);--side:var(--fr0-side);
  transition:--h .9s var(--ease);transition-delay:calc(var(--i)*8ms)}
.land:not(.in) .bar{--h:0px}
.land.in .bar{--h:var(--hh)}
.land .bar.fr1{--col:var(--fr1);--side:var(--fr1-side)} .land .bar.fr2{--col:var(--fr2);--side:var(--fr2-side)} .land .bar.fr3{--col:var(--fr3);--side:var(--fr3-side)}
.land .bar.on,.land .bar:hover{--col:var(--accent);--side:color-mix(in srgb,var(--accent) 60%,#000)}
.land .bar>i{position:absolute;display:block;backface-visibility:hidden;background:var(--side)}
.land .bar .sh{left:-3px;top:-3px;width:calc(100% + 6px);height:calc(100% + 6px);border-radius:50%;background:radial-gradient(rgba(0,0,0,.4),transparent 68%);transform:translateZ(0.5px);backface-visibility:visible;opacity:calc(var(--hh) / 60px)}
.land .bar .t{left:2px;top:2px;width:calc(100% - 4px);height:calc(100% - 4px);background:var(--col);transform:translateZ(var(--h));
  background-image:linear-gradient(135deg,rgba(255,255,255,.2),transparent 60%)}
.land .bar .t::after{content:"";position:absolute;left:50%;top:50%;width:4px;height:4px;transform:translate(-50%,-50%);background:rgba(0,0,0,.35);opacity:0}
.land .bar.shot .t::after{opacity:1}
.land .bar .s{left:2px;width:calc(100% - 4px);height:var(--h);bottom:2px;transform-origin:50% 100%;transform:rotateX(-90deg)}
.land .bar .n{left:2px;width:calc(100% - 4px);height:var(--h);top:2px;transform-origin:50% 0;transform:rotateX(90deg);filter:brightness(.8)}
.land .bar .e{top:2px;height:calc(100% - 4px);width:var(--h);right:2px;transform-origin:100% 50%;transform:rotateY(90deg);filter:brightness(.88)}
.land .bar .w{top:2px;height:calc(100% - 4px);width:var(--h);left:2px;transform-origin:0 50%;transform:rotateY(-90deg);filter:brightness(.92)}
.land .lab{position:absolute;left:calc(-3.4*var(--u));top:calc(var(--r)*var(--pitch));width:calc(3.1*var(--u));height:var(--u);
  transform:translateZ(2px) rotateZ(calc(-1*var(--yaw))) rotateX(calc(-1*var(--tilt)));transform-origin:50% 50%;
  display:flex;align-items:center;justify-content:flex-end;pointer-events:none}
.land .lab span{display:inline-flex;align-items:center;gap:6px;background:var(--panel);border:1px solid var(--line-2);border-radius:4px;
  padding:3px 8px;font:500 11px var(--sans);color:var(--ink);white-space:nowrap;line-height:1.2}
.land .lab svg.st{width:11px;height:11px}
.land .tick{position:absolute;top:calc(var(--rows)*var(--pitch) + .35*var(--u));left:calc(var(--c)*var(--u));width:var(--u);height:var(--u);
  transform:translateZ(1px) rotateZ(calc(-1*var(--yaw))) rotateX(calc(-1*var(--tilt)));display:grid;place-items:center;
  font:500 10px var(--sans);color:var(--muted);pointer-events:none;font-variant-numeric:tabular-nums}
.land .hint{position:absolute;right:14px;bottom:10px;font:400 .74rem var(--sans);color:var(--muted);display:flex;gap:12px;align-items:center;pointer-events:none}
.land .hint i{width:8px;height:8px;border-radius:1px;display:inline-block;background:var(--fr2)}
.land .hint i.r{background:var(--fr3)}
.land .empty-land{position:absolute;inset:0;display:grid;place-items:center;color:var(--faint);font-size:.85rem}

/* ---------------------------------------------------------------- flat journey map */
.jm{display:grid;grid-template-columns:200px minmax(0,1fr) 150px;gap:0 18px;align-items:center}
.jm-head{display:contents}
.jm-head > div{padding-bottom:10px}
.jm-axis{position:relative;height:14px;border-bottom:1px solid var(--line-2)}
.jm-axis i{position:absolute;bottom:-1px;width:1px;height:5px;background:var(--line-3)}
.jm-axis i.maj{height:9px;background:var(--faint)}
.jm-axis b{position:absolute;bottom:6px;transform:translateX(-50%);font:500 .64rem var(--sans);color:var(--muted);font-variant-numeric:tabular-nums}
.jm-row{display:contents}
.jm-row > *{padding:8px 0;border-bottom:1px solid var(--line)}
.jm-row:last-child > *{border-bottom:0}
.jm-who{display:flex;align-items:center;gap:10px;min-width:0}
.jm-who .nm{font-weight:600;font-size:.9rem;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.jm-who .sub{color:var(--muted);font-size:.74rem;display:flex;align-items:center;gap:6px;text-transform:capitalize}
.jm-who .sub svg.st{width:11px;height:11px}
.jm-strip{display:grid;grid-template-columns:repeat(var(--n,1),minmax(0,1fr));gap:3px;height:28px;align-items:stretch;position:relative}
.jm-cell{min-width:0;border-radius:2px;background:var(--raise);position:relative;cursor:pointer;
  border:0;padding:0;transition:transform .2s,filter .2s;transform-origin:center bottom}
.jm-cell.fr1{background:var(--fr1)} .jm-cell.fr2{background:var(--fr2)} .jm-cell.fr3{background:var(--fr3)}
.jm-cell.shot::after{content:"";position:absolute;left:50%;bottom:4px;width:4px;height:3px;background:rgba(0,0,0,.35);transform:translateX(-50%)}
.jm-cell:hover,.jm-cell:focus-visible{transform:scaleY(1.18);filter:brightness(1.08);outline:0;z-index:2}
.jm-cell.on{box-shadow:0 0 0 2px var(--bg),0 0 0 4px var(--accent);z-index:2}
.js .jm-strip:not(.in) .jm-cell{transform:scaleY(0)}
.jm-strip.in .jm-cell{animation:rise .6s var(--ease) both;animation-delay:calc(var(--i) * 24ms)}
@keyframes rise{from{transform:scaleY(0);opacity:.4}to{transform:scaleY(1);opacity:1}}
.jm-empty{color:var(--faint);font-size:.8rem;display:flex;align-items:center;height:28px;padding-left:2px}
.jm-tail{display:flex;align-items:center;gap:10px;justify-content:flex-end}
.jm-tail .dur{font-size:.76rem;color:var(--muted);min-width:44px;text-align:right;font-variant-numeric:tabular-nums}
.jm-legend{display:flex;gap:18px;flex-wrap:wrap;align-items:center;padding:12px 0 8px;color:var(--muted);font-size:.78rem;border-top:1px solid var(--line);margin-top:8px}
.jm-legend span{display:inline-flex;align-items:center;gap:6px}
.jm-legend i{width:10px;height:10px;border-radius:1px;background:var(--raise-2);display:inline-block}
.jm-legend i.fr1{background:var(--fr1)} .jm-legend i.fr2{background:var(--fr2)} .jm-legend i.fr3{background:var(--fr3)}
.jm-legend .hint{margin-left:auto;color:var(--faint)}
.tip{position:fixed;z-index:90;pointer-events:none;max-width:320px;background:var(--panel);color:var(--ink);
  border:1px solid var(--line-2);border-radius:6px;padding:10px 12px;font-size:.8rem;line-height:1.5;
  box-shadow:var(--shadow-2);opacity:0;transform:translateY(4px);transition:opacity .2s,transform .2s}
.tip.show{opacity:1;transform:none}
.tip .t{font-weight:600;display:flex;gap:8px;align-items:center;margin-bottom:3px}
.tip .t .num{color:var(--muted);font-size:.72rem;font-weight:500}
.tip .s{color:var(--muted)}
.tip .q{color:var(--ink-soft);margin-top:6px;border-top:1px solid var(--line);padding-top:6px}

/* ensō-ish ring gauge (ease score) */
.gauge{position:relative;width:38px;height:38px;display:inline-grid;place-items:center;font-size:.7rem;font-weight:500;color:var(--ink);flex:none;font-variant-numeric:tabular-nums}
.gauge svg{position:absolute;inset:0;width:38px;height:38px;transform:rotate(-90deg)}
.gauge circle{fill:none;stroke-width:2.5}
.gauge .tr{stroke:var(--raise-2)}
.gauge .fl{stroke:var(--accent);stroke-linecap:round;transition:stroke-dashoffset 1.2s var(--ease)}
.gauge.low .fl{stroke:var(--blocker)} .gauge.mid .fl{stroke:var(--major)} .gauge.high .fl{stroke:var(--ok)}
.gauge.na{color:var(--faint)}
/* evidence signal bars */
.sig{display:inline-flex;gap:2px;align-items:flex-end;height:10px;margin-right:5px}
.sig i{width:3px;background:currentColor;opacity:.25;border-radius:1px}
.sig i:nth-child(1){height:4px} .sig i:nth-child(2){height:7px} .sig i:nth-child(3){height:10px}
.sig.s1 i:nth-child(1),.sig.s2 i:nth-child(-n+2),.sig.s3 i{opacity:1}
/* hanko: a square seal */
.stamp{display:inline-block;font-size:.62rem;font-weight:700;letter-spacing:.2em;text-transform:uppercase;padding:5px 8px 5px 10px;
  border:1.5px solid currentColor;border-radius:3px;transform:rotate(-3deg);color:var(--seal);line-height:1;opacity:.9;
  box-shadow:inset 0 0 0 1px var(--bg),inset 0 0 0 2px currentColor;mix-blend-mode:multiply}
:root[data-theme="dark"] .stamp{mix-blend-mode:screen}
@media(prefers-color-scheme:dark){:root:not([data-theme="light"]) .stamp{mix-blend-mode:screen}}
.stamp.completed{color:var(--ok)} .stamp.partial{color:var(--major)} .stamp.abandoned,.stamp.failed{color:var(--blocker)} .stamp.unknown{color:var(--faint)}

/* who hit what matrix */
.mx{width:100%;border-collapse:separate;border-spacing:0;font-size:.86rem}
.mx th{padding:6px 8px 10px;border-bottom:1px solid var(--line-2);text-align:left;vertical-align:bottom}
.mx th.p{text-align:center;width:56px}
.mx th.p .ava{width:24px;height:24px;border-radius:5px;margin:0 auto 5px}
.mx th.p span{display:block;font-size:.62rem;letter-spacing:.06em;color:var(--muted);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:56px}
.mx td{padding:9px 8px;border-bottom:1px solid var(--line);vertical-align:middle}
.mx tr:last-child td{border-bottom:0}
.mx tr:hover td{background:var(--panel-2)}
.mx td.w{color:var(--ink);max-width:0;width:100%}
.mx td.w .rk{color:var(--faint);font-size:.74rem;margin-right:10px;font-variant-numeric:tabular-nums}
.mx td.w .pill{margin-right:8px}
.mx td.w span.txt{white-space:nowrap;overflow:hidden;text-overflow:ellipsis;display:inline-block;max-width:calc(100% - 110px);vertical-align:middle}
.mx td.c{text-align:center}
.mx td.c svg.g{width:13px;height:13px}
.mx td.r{text-align:right;color:var(--muted);font-size:.78rem;white-space:nowrap;font-variant-numeric:tabular-nums}

/* ---------------------------------------------------------------- tables: a ledger */
.scroll{overflow-x:auto;-webkit-overflow-scrolling:touch}
table{width:100%;border-collapse:collapse;font-size:.9rem}
thead th{background:transparent}
th,td{text-align:left;padding:14px 14px;border-bottom:1px solid var(--line);vertical-align:middle}
thead th{border-bottom:1px solid var(--line-2);padding-top:6px;padding-bottom:10px}
thead th:first-child,tbody td:first-child{padding-left:0}
thead th:last-child,tbody td:last-child{padding-right:0}
tbody tr:last-child td{border-bottom:0}
tbody tr:hover{background:var(--panel-2)}
td.num{font-variant-numeric:tabular-nums;color:var(--ink);font-weight:500}
.who{display:flex;align-items:center;gap:10px;min-width:160px}
td.task{min-width:11rem;max-width:18rem;color:var(--ink-soft);font-size:.86rem}
.ava{width:30px;height:30px;border-radius:5px;flex:none;display:grid;place-items:center;color:var(--ink);background:transparent;border:1px solid var(--line-2)}
.ava .ic{width:56%;height:56%}
.who .nm{font-weight:600} .who .dev{color:var(--muted);font-size:.76rem;text-transform:capitalize}
.fixcell{min-width:16rem;max-width:30rem;color:var(--ink-soft);font-size:.86rem}
.fixcell span{display:-webkit-box;-webkit-line-clamp:4;-webkit-box-orient:vertical;overflow:hidden}
.badge{display:inline-flex;align-items:center;gap:7px;font-size:.78rem;font-weight:500;padding:3px 0;white-space:nowrap;text-transform:capitalize}
.badge svg.st{width:12px;height:12px;color:currentColor}
.badge.completed{color:var(--ok)} .badge.partial{color:var(--major)}
.badge.abandoned,.badge.failed{color:var(--blocker)}
.meter{display:flex;align-items:center;gap:8px;font-size:.78rem}
.bnum{font-weight:600;color:var(--blocker);font-variant-numeric:tabular-nums}
.zero{color:var(--faint)}
.spark{display:inline-flex;gap:1px;align-items:flex-end;height:18px}
.spark i{display:block;width:3px;border-radius:1px;background:var(--raise-2);height:25%}
.spark i.fr1{background:var(--fr1);height:50%} .spark i.fr2{background:var(--fr2);height:75%} .spark i.fr3{background:var(--fr3);height:100%}
.abtn{display:inline-flex;align-items:center;gap:6px;color:var(--ink);font-size:.8rem;font-weight:500;border:1px solid var(--line-2);
  background:transparent;border-radius:5px;padding:5px 11px;white-space:nowrap;cursor:pointer;transition:border-color .2s,background .2s}
.abtn:hover{border-color:var(--ink);text-decoration:none}
.abtn.pri{background:var(--accent);color:var(--on-accent);border-color:transparent;font-weight:600}
.abtn.pri:hover{background:color-mix(in srgb,var(--accent) 85%,#000 5%)}
.abtn .ic{width:13px;height:13px}
.acts{display:flex;gap:6px;justify-content:flex-end}

/* ---------------------------------------------------------------- issues */
.fbar{position:sticky;top:56px;z-index:10;display:flex;flex-wrap:wrap;gap:8px;align-items:center;
  padding:12px 0 14px;background:color-mix(in srgb,var(--bg) 96%,transparent);border-bottom:1px solid var(--line-2);margin-bottom:4px}
.fbar .grp{display:flex;gap:0;align-items:center;border:1px solid var(--line-2);border-radius:5px;overflow:hidden}
.chipb{border:0;background:transparent;color:var(--ink-soft);font-size:.78rem;font-weight:500;padding:6px 11px;
  cursor:pointer;display:inline-flex;align-items:center;gap:7px;transition:background .2s,color .2s;white-space:nowrap}
.chipb + .chipb{border-left:1px solid var(--line)}
.chipb:hover{background:var(--panel-2);color:var(--ink)}
.chipb.on{background:var(--accent);color:var(--on-accent);font-weight:600}
.chipb svg.g{width:11px;height:11px}
.chipb .sig{margin-right:0}
.chipb.measured .sig{color:var(--ok)} .chipb.observed .sig{color:var(--ink-soft)} .chipb.impression .sig{color:var(--muted)}
.chipb .ava{width:18px;height:18px;border-radius:4px}
.fbar select{height:32px;border:1px solid var(--line-2);border-radius:5px;background:transparent;color:var(--ink);font:inherit;font-size:.8rem;padding:0 8px;cursor:pointer}
.fbar .tail{margin-left:auto;display:flex;align-items:center;gap:12px}
.fbar .count{color:var(--muted);font-size:.8rem;white-space:nowrap;font-variant-numeric:tabular-nums}
.fbar .count b{color:var(--ink)}
.fbar .clear{color:var(--ink);font-size:.8rem;background:none;border:0;cursor:pointer;padding:0 4px;text-decoration:underline;text-underline-offset:4px}
.band{display:flex;align-items:center;gap:12px;margin:34px 0 4px;font-size:1.05rem;font-weight:500;letter-spacing:-.01em;color:var(--ink)}
.band:first-child{margin-top:14px}
.band .count{border:1px solid var(--ink);color:var(--ink);border-radius:99px;padding:0 8px;font-size:.72rem;font-weight:600;font-variant-numeric:tabular-nums;line-height:1.5}
.band .desc{color:var(--muted);font-weight:400;font-size:.84rem}
.band::after{content:"";flex:1;height:1px;background:var(--line-2)}
.f{position:relative;background:transparent;border-bottom:1px solid var(--line);padding:22px 0 20px;margin:0;transition:background .2s}
.f:hover{background:color-mix(in srgb,var(--panel-2) 60%,transparent)}
.f .head{display:flex;gap:14px;align-items:baseline}
.f .rank{font-size:.8rem;font-weight:500;color:var(--faint);flex:none;min-width:2.2ch;font-variant-numeric:tabular-nums}
.f .what{color:var(--ink);font-weight:500;font-size:1.05rem;line-height:1.45;flex:1;letter-spacing:-.01em}
.f .copy{flex:none;align-self:flex-start;opacity:0;transition:opacity .2s}
.f:hover .copy,.f:focus-within .copy{opacity:1}
.f .who-row{display:flex;gap:5px;align-items:center;margin-top:12px;padding-left:calc(2.2ch + 14px)}
.f .who-row .ava{width:22px;height:22px;border-radius:4px;position:relative}
.f .who-row .ava svg.g.mini{position:absolute;right:-6px;bottom:-6px;width:12px;height:12px;background:var(--bg);border-radius:2px;padding:1px}
.f .who-row .lbl{color:var(--muted);font-size:.8rem;margin-left:6px;letter-spacing:0;text-transform:none;font-weight:400}
.pill{display:inline-flex;align-items:center;gap:6px;padding:0;font-size:.7rem;font-weight:600;letter-spacing:.12em;text-transform:uppercase;
  margin-right:10px;vertical-align:middle;color:var(--muted)}
.pill svg.g{width:13px;height:13px}
.pill.blocker{color:var(--blocker)} .pill.major{color:var(--major)} .pill.minor{color:var(--minor)} .pill.nitpick{color:var(--nitpick)}
.tags{display:flex;flex-wrap:wrap;gap:6px;margin:12px 0 0;padding-left:calc(2.2ch + 14px)}
.tag{font-size:.74rem;font-weight:500;padding:2px 9px;border-radius:3px;border:1px solid var(--line-2);color:var(--ink-soft);white-space:nowrap;display:inline-flex;align-items:center}
.tag.hot{border-color:var(--blocker);color:var(--blocker)}
.tag.star{background:var(--accent-bg);border-color:transparent;color:var(--accent-ink)}
.tag.grade-measured{border-color:color-mix(in srgb,var(--ok) 60%,transparent);color:color-mix(in srgb,var(--ok) 80%,var(--ink))}
.tag.grade-impression{border-style:dashed;color:var(--muted)}
.f .meta{color:var(--muted);font-size:.82rem;margin-top:10px;padding-left:calc(2.2ch + 14px)}
.f .fix{color:var(--ink-soft);font-size:.9rem;margin-top:10px;padding-left:calc(2.2ch + 14px);line-height:1.6;max-width:96ch}
.f .fix strong{color:var(--ink);font-weight:600}
details.ev{margin:10px 0 0;padding-left:calc(2.2ch + 14px)}
details.ev summary{cursor:pointer;color:var(--ink);font-size:.82rem;list-style:none;display:inline-flex;align-items:center;gap:6px;text-decoration:underline;text-underline-offset:4px;text-decoration-color:var(--line-3)}
details.ev summary::-webkit-details-marker{display:none}
details.ev summary::before{content:"+";font-weight:600}
details.ev[open] summary::before{content:"\2212"}
details.ev ul{margin:10px 0 0;padding-left:18px;color:var(--ink-soft);font-size:.86rem;max-width:96ch}
details.ev li{margin:4px 0}
.f.hide{display:none}
.band.hide{display:none}

/* ---------------------------------------------------------------- replay */
.rp-tabs{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:16px}
.rp-tab{display:inline-flex;align-items:center;gap:8px;padding:6px 12px 6px 7px;border:1px solid var(--line-2);border-radius:5px;
  background:transparent;color:var(--ink);cursor:pointer;font-size:.86rem;font-weight:500;transition:border-color .2s,background .2s}
.rp-tab .ava{width:22px;height:22px;border-radius:4px}
.rp-tab svg.st{width:13px;height:13px}
.rp-tab:hover{border-color:var(--ink)}
.rp-tab.on{background:var(--accent);color:var(--on-accent);border-color:transparent;font-weight:600}
.rp-tab.on .ava{border-color:rgba(0,0,0,.2);color:var(--on-accent)}
.rp{display:grid;grid-template-columns:minmax(0,1.55fr) minmax(300px,.85fr);gap:24px;align-items:stretch}
.rp-stage{background:var(--panel);border:1px solid var(--line-2);border-radius:6px;overflow:hidden;display:flex;flex-direction:column;min-width:0}
.rp-chrome{display:flex;align-items:center;gap:8px;padding:10px 14px;border-bottom:1px solid var(--line)}
.rp-chrome .url{margin-left:0;font-family:var(--mono);font-size:.72rem;color:var(--muted);flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.rp-shot{position:relative;background:var(--stage);flex:1;min-height:420px;max-height:min(64vh,720px);display:grid;place-items:center;overflow:hidden;padding:18px}
.rp-shot img{max-width:100%;max-height:100%;width:auto;height:auto;object-fit:contain;display:block;
  box-shadow:0 20px 50px -22px rgba(0,0,0,.45);animation:shot .5s var(--ease)}
.rp-shot.phone img{border-radius:24px;border:8px solid #1f1d1a;box-shadow:0 0 0 1px rgba(0,0,0,.2),0 24px 60px -20px rgba(0,0,0,.6)}
@keyframes shot{from{opacity:0;transform:scale(.985)}to{opacity:1;transform:none}}
/* registration marks: the probe's viewfinder, in seal red */
.rp-shot .vf{position:absolute;width:18px;height:18px;border:1.5px solid var(--seal);pointer-events:none}
.rp-shot .vf.tl{left:10px;top:10px;border-right:0;border-bottom:0}
.rp-shot .vf.tr{right:10px;top:10px;border-left:0;border-bottom:0}
.rp-shot .vf.bl{left:10px;bottom:10px;border-right:0;border-top:0}
.rp-shot .vf.br{right:10px;bottom:10px;border-left:0;border-top:0}
.rp-shot .none{color:var(--muted);font-size:.92rem;text-align:center;padding:40px;max-width:46ch}
.rp-shot .none b{display:block;color:var(--ink);font-size:.9rem;font-weight:600;margin-bottom:6px}
.rp-shot .none svg{width:44px;height:44px;color:var(--faint);margin:0 auto 12px;display:block}
.rp-shot .tag-n{position:absolute;left:18px;top:18px;font-size:.72rem;font-weight:600;color:var(--on-accent);background:var(--accent);padding:3px 9px;border-radius:3px;font-variant-numeric:tabular-nums}
.rp-shot .feel{position:absolute;right:18px;top:18px;font-size:.74rem;font-weight:500;color:#fff;background:rgba(0,0,0,.55);padding:3px 9px;border-radius:3px;text-transform:capitalize}
.rp-cap{padding:12px 16px;border-top:1px solid var(--line);display:flex;gap:12px;align-items:center;min-height:52px}
.rp-cap .act{color:var(--ink);font-size:.94rem;flex:1}
.rp-cap .fric{display:inline-flex;gap:3px;flex:none}
.rp-cap .fric i{width:14px;height:5px;border-radius:2px;background:var(--raise-2)}
.rp-cap .fric i.on1{background:var(--fr1)} .rp-cap .fric i.on2{background:var(--fr2)} .rp-cap .fric i.on3{background:var(--fr3)}
.rp-side{display:flex;flex-direction:column;gap:0;min-width:0}
.rp-card{padding:4px 0 20px;border-bottom:1px solid var(--line-2)}
.rp-card .lbl{margin-bottom:8px;display:block}
.rp-card .big{font-size:3.2rem;font-weight:300;letter-spacing:-.03em;line-height:1;color:var(--ink);font-variant-numeric:tabular-nums}
.rp-card .big small{color:var(--faint);font-size:1.1rem;font-weight:400}
.rp-card .intent{font-size:1.2rem;font-weight:500;line-height:1.4;color:var(--ink);margin-top:12px;letter-spacing:-.015em}
.rp-kv{display:grid;grid-template-columns:1fr 1fr;gap:18px;margin-top:16px}
.rp-kv > div{padding:0 0 0 12px;border-left:1px solid var(--line-2);font-size:.86rem;color:var(--ink-soft);line-height:1.55}
.rp-kv > div.bad{border-left-color:var(--blocker);color:var(--ink)}
.rp-kv .lbl{margin-bottom:5px;display:block}
.rp-thought{padding:20px 0 16px;flex:1;position:relative}
.rp-thought .q{font-size:1.12rem;line-height:1.6;color:var(--ink);position:relative;font-weight:400;letter-spacing:-.005em}
.rp-thought .q::before{content:"\201C";color:var(--seal);margin-right:1px}
.rp-thought .q::after{content:"\201D";color:var(--seal);margin-left:1px}
.rp-thought .cite{display:flex;align-items:center;gap:9px;margin-top:16px;color:var(--muted);font-size:.8rem}
.rp-thought .cite .ava{width:22px;height:22px;border-radius:4px}
.rp-thought .empty-q{color:var(--faint);font-size:.88rem}
.rp-bar{margin-top:22px;padding:16px 0 0;border-top:1px solid var(--line-2)}
.rp-ctl{display:flex;align-items:center;gap:8px;margin-bottom:16px}
.rp-ctl .pos{font-size:.84rem;color:var(--muted);margin-left:8px;min-width:80px;font-variant-numeric:tabular-nums}
.rp-ctl .pos b{color:var(--ink);font-weight:600}
.rp-ctl .hint{margin-left:auto;color:var(--muted);font-size:.76rem;display:flex;gap:12px;align-items:center}
.rp-ctl .hint span{display:inline-flex;gap:4px;align-items:center}
.ibtn{width:34px;height:34px;display:grid;place-items:center;border:1px solid var(--line-2);border-radius:99px;background:transparent;
  color:var(--ink);cursor:pointer;transition:border-color .2s,background .2s,transform .12s}
.ibtn:hover{border-color:var(--ink)}
.ibtn:active{transform:scale(.94)}
.ibtn.pri{background:var(--accent);color:var(--on-accent);border-color:transparent;width:40px;height:40px}
.ibtn .ic{width:16px;height:16px}
.ibtn .pause{display:none}
.ibtn.playing .play{display:none} .ibtn.playing .pause{display:inline-block}
.rp-tl{display:flex;gap:3px;height:30px;align-items:stretch;position:relative}
.rp-seg{flex:1 1 0;min-width:6px;border:0;padding:0;border-radius:2px;background:var(--raise);cursor:pointer;position:relative;
  transition:filter .2s,transform .2s;transform-origin:center bottom}
.rp-seg.fr1{background:var(--fr1)} .rp-seg.fr2{background:var(--fr2)} .rp-seg.fr3{background:var(--fr3)}
.rp-seg.shot::after{content:"";position:absolute;left:50%;bottom:4px;width:4px;height:3px;background:rgba(0,0,0,.35);transform:translateX(-50%)}
.rp-seg:hover{filter:brightness(1.08)}
.rp-seg.on{box-shadow:0 0 0 2px var(--bg),0 0 0 4px var(--accent)}
.rp-seg.on::before{content:"";position:absolute;left:50%;top:-12px;transform:translateX(-50%);border:5px solid transparent;border-top:6px solid var(--ink)}
.rp-seg.done{opacity:.5}
.rp-seg.on.done{opacity:1}
.rp-axis{position:relative;height:16px;margin-top:8px}
.rp-axis b{position:absolute;transform:translateX(-50%);font:500 .64rem var(--sans);color:var(--muted);top:2px;font-variant-numeric:tabular-nums}
.rp-axis i{position:absolute;top:0;width:1px;height:4px;background:var(--line-3)}
.rp-none{color:var(--muted);font-size:.92rem;padding:40px;text-align:center;border:1px dashed var(--line-2);border-radius:6px}

/* ---------------------------------------------------------------- gallery */
.gal{padding:18px 0 10px;border-top:1px solid var(--line-2)}
.gal h4{font-size:1.02rem;font-weight:500;letter-spacing:-.01em;margin-bottom:14px;display:flex;align-items:center;gap:10px}
.gal h4 .ava{width:24px;height:24px;border-radius:4px}
.gal h4 .n{color:var(--muted);font-weight:400;font-size:.8rem}
.gal h4 .abtn{margin-left:auto}
.strip{display:flex;gap:14px;overflow-x:auto;padding:2px 2px 12px;scroll-snap-type:x proximity;scrollbar-width:thin}
.strip figure{margin:0;flex:0 0 232px;scroll-snap-align:start}
.strip a,.strip button{display:block;width:100%;padding:0;border:0;background:none;cursor:zoom-in;text-align:left}
.strip img{width:100%;height:150px;object-fit:cover;object-position:top left;border-radius:4px;
  background:var(--panel-2);display:block;border:1px solid var(--line-2);transition:transform .3s var(--ease),border-color .2s}
.strip button:hover img{transform:translateY(-3px);border-color:var(--ink)}
.strip figcaption{color:var(--muted);font-size:.78rem;margin-top:8px;line-height:1.45;display:flex;gap:6px}
.strip figcaption .n{color:var(--ink);font-weight:600;flex:none;font-variant-numeric:tabular-nums}
.strip figcaption .fr{margin-left:auto;flex:none;display:inline-flex;gap:2px;align-items:center;padding-top:5px}
.strip figcaption .fr i{width:7px;height:4px;border-radius:1px;background:var(--raise-2)}
.strip figcaption .fr i.on1{background:var(--fr1)} .strip figcaption .fr i.on2{background:var(--fr2)} .strip figcaption .fr i.on3{background:var(--fr3)}

/* lightbox */
.lb{position:fixed;inset:0;z-index:130;display:none;flex-direction:column;background:rgba(20,19,15,.94)}
.lb.open{display:flex}
.lb-head{display:flex;align-items:center;gap:12px;padding:12px 18px;color:#fff}
.lb-head .t{font-weight:500;font-size:.92rem;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;flex:1}
.lb-head .pos{font-size:.78rem;color:rgba(255,255,255,.6);font-variant-numeric:tabular-nums}
.lb-head .ibtn{color:#fff;border-color:rgba(255,255,255,.3)}
.lb-head .ibtn:hover{border-color:#fff}
.lb-head .abtn{color:#fff;border-color:rgba(255,255,255,.3)}
.lb-body{flex:1;display:grid;place-items:center;padding:10px 70px 20px;min-height:0;position:relative}
.lb-body img{max-width:100%;max-height:100%;object-fit:contain;border-radius:4px;box-shadow:0 40px 100px -30px #000;animation:shot .3s var(--ease)}
.lb-nav{position:absolute;top:50%;transform:translateY(-50%);width:44px;height:44px;border-radius:99px;border:1px solid rgba(255,255,255,.3);
  background:transparent;color:#fff;cursor:pointer;display:grid;place-items:center}
.lb-nav:hover{background:var(--accent);color:var(--on-accent);border-color:transparent}
.lb-nav.prev{left:14px} .lb-nav.next{right:14px}
.lb-nav .ic{width:18px;height:18px}
.lb-foot{padding:10px 18px 18px;color:rgba(255,255,255,.75);font-size:.86rem;text-align:center;max-width:80ch;margin:0 auto}
.lb-foot b{color:#fff}

/* ---------------------------------------------------------------- voices */
.quote{padding:22px 0 18px;margin:0;position:relative;border-top:1px solid var(--line-2)}
.quote p{font-size:1.04rem;line-height:1.65;color:var(--ink);font-weight:400;letter-spacing:-.005em}
.quote p::before{content:"\201C";color:var(--seal);margin-right:1px}
.quote p::after{content:"\201D";color:var(--seal);margin-left:1px}
.quote .cite{display:flex;align-items:center;gap:9px;margin-top:16px;color:var(--muted);font-size:.82rem}
.quote .cite .ava{width:24px;height:24px;border-radius:4px}
.quote .cite .stamp{margin-left:auto}
.quote .arc{margin-top:14px;padding-top:12px;border-top:1px solid var(--line);color:var(--ink-soft);font-size:.86rem;line-height:1.6}
.quote .arc b{display:block;margin-bottom:6px;font-size:.66rem;font-weight:600;letter-spacing:.16em;text-transform:uppercase;color:var(--muted)}
.mood{display:flex;gap:2px;height:6px;margin-top:16px;overflow:hidden}
.mood i{flex:1;background:var(--raise);min-width:2px}
.mood i.up{background:var(--ok)} .mood i.mid{background:var(--minor)} .mood i.down{background:var(--major)} .mood i.bad{background:var(--blocker)}
.mood-lbl{display:flex;justify-content:space-between;color:var(--faint);font-size:.66rem;letter-spacing:.1em;text-transform:uppercase;margin-top:5px}
.worked{list-style:none;padding:0;margin:0;display:grid;gap:0 40px;grid-template-columns:repeat(auto-fill,minmax(320px,1fr))}
.worked li{padding:12px 0 12px 26px;position:relative;font-size:.88rem;color:var(--ink-soft);border-bottom:1px solid var(--line)}
.worked li::before{content:"";position:absolute;left:4px;top:19px;width:7px;height:7px;border-radius:99px;background:var(--ok)}
.worked .by{color:var(--muted);font-size:.78rem}
.qgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(360px,1fr));gap:0 40px}
.qgrid .quote{margin:0}

.empty{color:var(--muted);font-size:.9rem;padding:28px;text-align:center;border:1px dashed var(--line-2);border-radius:6px}
.content .foot{color:var(--muted);font-size:.8rem;margin-top:40px;padding-top:20px;border-top:1px solid var(--line-2);line-height:1.65;max-width:72ch;display:flex;gap:18px;align-items:flex-start}
.content .foot .stamp{flex:none;margin-top:2px;color:var(--seal)}

/* ---------------------------------------------------------------- modals */
.modal{position:fixed;inset:0;z-index:120;display:none;justify-content:center;align-items:flex-start;padding:44px 20px;overflow-y:auto;background:rgba(20,19,15,.5)}
.modal.open{display:flex}
.modal-card{background:var(--panel);border:1px solid var(--line-2);border-radius:8px;width:min(900px,100%);box-shadow:var(--shadow-2);margin:auto}
.modal-head{position:sticky;top:0;z-index:1;display:flex;align-items:center;gap:12px;padding:16px 22px;border-bottom:1px solid var(--line);background:var(--panel);border-radius:8px 8px 0 0}
.modal-head .t{font-weight:600;font-size:1rem;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;letter-spacing:-.01em}
.modal-close{margin-left:auto;flex:none;width:32px;height:32px;display:grid;place-items:center;border:1px solid var(--line-2);border-radius:99px;background:transparent;color:var(--ink);cursor:pointer}
.modal-close:hover{border-color:var(--ink)}
.modal-close .ic{width:16px;height:16px}
.modal-body{padding:22px 26px 30px}
.help .modal-card{width:min(560px,100%)}
.help table{font-size:.88rem}
.help td{padding:9px 6px;border-bottom:1px solid var(--line)}
.help td:first-child{width:130px;white-space:nowrap}
.help kbd{margin-right:3px}
.toast{position:fixed;left:50%;bottom:26px;transform:translate(-50%,10px);z-index:140;background:var(--ink);color:var(--bg);
  padding:10px 16px;border-radius:5px;font-size:.84rem;font-weight:500;opacity:0;transition:opacity .2s,transform .2s;pointer-events:none;box-shadow:var(--shadow-2)}
.toast.show{opacity:1;transform:translate(-50%,0)}

/* rendered session document */
.logdoc h2{font-size:1.4rem;font-weight:500;letter-spacing:-.02em;line-height:1.25;margin-bottom:6px}
.logdoc h2 .arrow{color:var(--faint);font-weight:400}
.logdoc h3{font-size:.66rem;letter-spacing:.16em;text-transform:uppercase;color:var(--muted);font-weight:600;margin:26px 0 10px;padding-bottom:8px;border-bottom:1px solid var(--line)}
.logdoc p{color:var(--ink-soft);margin:8px 0}
.logdoc p.one{font-size:1.02rem;color:var(--ink)}
.chips-row{display:flex;flex-wrap:wrap;gap:6px;margin:12px 0 4px}
.chip{font-size:.76rem;font-weight:500;color:var(--ink);border:1px solid var(--line-2);border-radius:3px;padding:3px 10px;text-transform:capitalize}
a.chip:hover{border-color:var(--ink)}
.logdoc .warn{margin:12px 0;padding:10px 14px;border-left:2px solid var(--blocker);color:var(--blocker);background:color-mix(in srgb,var(--blocker) 8%,transparent)}
.logdoc ul.kv{list-style:none;padding:0;margin:4px 0;display:grid;gap:6px}
.logdoc ul.kv li{color:var(--ink-soft);font-size:.9rem}
.logdoc ul.kv b{display:inline-block;min-width:64px;color:var(--muted);font-weight:600;margin-right:6px}
.logdoc ul.kv a{color:var(--ink);text-decoration:underline;text-underline-offset:3px}
.logdoc ul{padding-left:20px} .logdoc li{margin:4px 0;color:var(--ink-soft)}
.logdoc blockquote{margin:8px 0;padding:10px 16px;border-left:2px solid var(--seal);color:var(--ink);font-size:.95rem}
.logdoc table{width:100%;border-collapse:collapse;font-size:.82rem;margin:8px 0}
.logdoc th,.logdoc td{border-bottom:1px solid var(--line);padding:8px 9px;text-align:left;vertical-align:top}
.logdoc th{color:var(--muted);font-weight:600;font-size:.66rem;letter-spacing:.12em;text-transform:uppercase;position:static}
.logdoc td.num{color:var(--ink-soft);font-variant-numeric:tabular-nums}
.logdoc details{margin:10px 0}
.logdoc summary{cursor:pointer;color:var(--ink);font-size:.86rem;text-decoration:underline;text-underline-offset:4px;text-decoration-color:var(--line-3)}
.logdoc .think{margin-top:10px}
.logdoc .think img{display:block;width:100%;max-width:520px;border:1px solid var(--line-2);border-radius:4px;margin:8px 0}
.logdoc .lf{border-left:2px solid var(--line-2);padding:4px 0 4px 14px;margin:12px 0}
.logdoc .lf b{color:var(--ink)}
.logdoc .lfrow{margin-top:6px;font-size:.86rem;color:var(--ink-soft)}
.logdoc .lfrow b{color:var(--muted);font-weight:600;margin-right:6px}

/* ---------------------------------------------------------------- responsive, motion, print */
@media(max-width:1180px){.rp{grid-template-columns:1fr}.jm{grid-template-columns:150px minmax(0,1fr) 110px}.readouts{grid-template-columns:repeat(3,1fr)}.ro:nth-child(4){border-left:0;padding-left:0}.hero-grid{grid-template-columns:auto 1fr}.hero-grid .fp{grid-column:2}}
@media(max-width:840px){
  .app{grid-template-columns:1fr}
  .side{position:static;height:auto;flex-direction:row;flex-wrap:wrap;align-items:center;border-right:0;border-bottom:1px solid var(--line-2);padding:14px 16px}
  .side .foot,.navlabel,.nav.pl{display:none}
  .nav{flex-direction:row;flex-wrap:wrap}
  .nav a .n{margin-left:6px}
  .nav a .k{display:none}
  .readouts{grid-template-columns:repeat(2,1fr)}
  .ro:nth-child(odd){border-left:0;padding-left:0}
  .ro:last-child:nth-child(odd){grid-column:span 2}
  .grid2{grid-template-columns:1fr}
  .jm{grid-template-columns:110px minmax(0,1fr)}
  .jm-tail,.jm-head .tl{display:none}
  .search{min-width:0;width:150px}
  .content{padding:22px 18px 60px}
  .topbar{padding:0 18px}
  .fbar{position:static}
  .verdict{font-size:1.5rem}
  .hero-grid{grid-template-columns:1fr}
  .hero-grid .vlabel{display:none}
  .hero-grid .fp{grid-column:1}
  .vhead > div:first-child{grid-template-columns:1fr}
  .vhead .eyebrow{writing-mode:horizontal-tb;grid-row:auto;border-left:0;padding:0;margin-bottom:6px}
  .land .stage{--zoom:.62}
}
@media(prefers-reduced-motion:reduce){
  *,*::before,*::after{animation-duration:.001ms!important;animation-delay:0s!important;transition-duration:.001ms!important}
  .js .dist:not(.in) i,.js .jm-strip:not(.in) .jm-cell{transform:none}
  .land:not(.in) .bar{--h:var(--hh)}
}
@media print{
  .grain,.side,.topbar,.fbar,.rp-bar,.rp-tabs,.copy,.acts,.lb,.modal,.toast,.tip,.land,.seg{display:none!important}
  .jpanel[data-mode="land"] .jm-wrap{display:block!important}
  .app{display:block}
  .js .view{display:block!important;page-break-before:always;animation:none}
  .js .view:first-child{page-break-before:auto}
  .content{padding:0}
  body{background:#fff;color:#000}
  .panel,.f,.quote,.ro{break-inside:avoid}
  .f.hide{display:block}
}
"""
