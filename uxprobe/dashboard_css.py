"""Stylesheet for the HTML dashboard. Kept apart from the renderer so the
Python stays readable; nothing here is interpolated, it is pasted in whole."""

DASHBOARD_CSS = r"""
*{margin:0;box-sizing:border-box}
:root{
  color-scheme:dark;
  --bg:#0a0a0b; --panel:#0f0f11; --panel-2:#141519; --raise:#1a1c22; --raise-2:#22252c;
  --ink:#e8e9ec; --ink-soft:#b7bac1; --muted:#868b95; --faint:#585d67;
  --line:rgba(255,255,255,.06); --line-2:rgba(255,255,255,.11); --line-3:rgba(255,255,255,.18);
  --accent:#6e79ff; --accent-ink:#b3b8ff; --accent-bg:rgba(110,121,255,.13);
  --blocker:#f26470; --major:#e0a44e; --minor:#6f90e6; --nitpick:#7b818c; --ok:#46c98a;
  --fr1:color-mix(in srgb,var(--major) 42%,var(--raise)); --fr2:var(--major); --fr3:var(--blocker);
  --shadow:0 30px 80px -30px rgba(0,0,0,.75);
  --mono:"JetBrains Mono",ui-monospace,SFMono-Regular,Menlo,monospace;
  --sans:"Schibsted Grotesk",ui-sans-serif,-apple-system,"Segoe UI",Roboto,sans-serif;
  --ease:cubic-bezier(.2,.7,.2,1);
}
:root[data-theme="light"],
:root:not([data-theme="dark"]) { }
@media(prefers-color-scheme:light){:root:not([data-theme="dark"]){
  color-scheme:light;
  --bg:#f7f7f8; --panel:#ffffff; --panel-2:#f2f3f5; --raise:#e9ebee; --raise-2:#dfe2e7;
  --ink:#16181d; --ink-soft:#3c4149; --muted:#6a707b; --faint:#a0a5af;
  --line:rgba(10,12,20,.08); --line-2:rgba(10,12,20,.13); --line-3:rgba(10,12,20,.2);
  --accent:#4b57e6; --accent-ink:#3a45c9; --accent-bg:rgba(75,87,230,.09);
  --blocker:#d63a4a; --major:#b9761b; --minor:#3a5bd0; --nitpick:#6a707b; --ok:#0f9d63;
  --shadow:0 30px 80px -30px rgba(20,24,40,.35);
}}
:root[data-theme="light"]{
  color-scheme:light;
  --bg:#f7f7f8; --panel:#ffffff; --panel-2:#f2f3f5; --raise:#e9ebee; --raise-2:#dfe2e7;
  --ink:#16181d; --ink-soft:#3c4149; --muted:#6a707b; --faint:#a0a5af;
  --line:rgba(10,12,20,.08); --line-2:rgba(10,12,20,.13); --line-3:rgba(10,12,20,.2);
  --accent:#4b57e6; --accent-ink:#3a45c9; --accent-bg:rgba(75,87,230,.09);
  --blocker:#d63a4a; --major:#b9761b; --minor:#3a5bd0; --nitpick:#6a707b; --ok:#0f9d63;
  --shadow:0 30px 80px -30px rgba(20,24,40,.35);
}
html,body{height:100%}
body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.6 var(--sans);
  -webkit-font-smoothing:antialiased;text-rendering:optimizeLegibility}
::selection{background:var(--accent);color:#fff}
a{color:var(--accent-ink);text-decoration:none}
a:hover{text-decoration:underline}
button{font:inherit;color:inherit}
kbd{font:600 .68rem/1 var(--mono);color:var(--muted);background:var(--raise);border:1px solid var(--line-2);
  border-bottom-width:2px;border-radius:5px;padding:3px 5px;min-width:18px;text-align:center;display:inline-block}
.ic{width:16px;height:16px;flex:none;display:inline-block;vertical-align:middle}
.mono{font-family:var(--mono);font-variant-numeric:tabular-nums}
.num{font-family:var(--mono);font-variant-numeric:tabular-nums}

/* film grain, static so repaints stay cheap */
.grain{position:fixed;inset:0;z-index:80;pointer-events:none;opacity:.028;
  background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='140' height='140'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='2' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E")}
:root[data-theme="light"] .grain{opacity:.045}
@media(prefers-color-scheme:light){:root:not([data-theme="dark"]) .grain{opacity:.045}}

/* ---------------------------------------------------------------- shell */
.app{display:grid;grid-template-columns:252px minmax(0,1fr);min-height:100vh}
.side{position:sticky;top:0;height:100vh;border-right:1px solid var(--line);overflow:hidden auto;
  background:var(--panel);display:flex;flex-direction:column;padding:16px 12px;gap:4px;scrollbar-width:thin}
.side-top{display:flex;align-items:center;gap:8px;padding:2px 6px 12px}
.brand{display:flex;align-items:center;gap:10px;min-width:0}
.brand .mark{width:28px;height:28px;border-radius:8px;flex:none;display:grid;place-items:center;
  background:var(--accent);box-shadow:0 4px 14px -4px var(--accent)}
.brand .mark .logo{width:17px;height:17px;display:block}
.brand .word{font-weight:650;letter-spacing:-.01em;font-size:.95rem;white-space:nowrap}
.brand .word span{color:var(--muted);font-weight:450}
.side-toggle{margin-left:auto;flex:none;width:30px;height:30px;display:grid;place-items:center;
  border:1px solid var(--line-2);border-radius:8px;background:transparent;color:var(--muted);cursor:pointer;
  transition:color .12s,border-color .12s,background .12s}
.side-toggle:hover{color:var(--ink);border-color:var(--line-3);background:var(--panel-2)}
.side-toggle .ic{width:17px;height:17px}
.navlabel{color:var(--faint);font-size:.64rem;font-weight:600;text-transform:uppercase;
  letter-spacing:.14em;padding:12px 10px 4px;display:flex;align-items:center;gap:8px}
.navlabel::after{content:"";flex:1;height:1px;background:var(--line)}
.nav{display:flex;flex-direction:column;gap:2px}
.nav a{display:flex;align-items:center;gap:10px;padding:7px 10px;border-radius:8px;
  color:var(--ink-soft);font-weight:500;font-size:.86rem;cursor:pointer;
  border:1px solid transparent;transition:background .12s,color .12s;min-width:0}
.nav a .ic{width:17px;height:17px;flex:none;color:var(--faint)}
.nav a .n{margin-left:auto;font-variant-numeric:tabular-nums;color:var(--faint);
  font-size:.72rem;font-weight:600;font-family:var(--mono)}
.nav a .k{margin-left:auto;opacity:0;transition:opacity .12s}
.nav a:hover{background:var(--panel-2);color:var(--ink)}
.nav a:hover .k{opacity:1}
.js .nav a.active{background:var(--accent-bg);color:var(--accent-ink);border-color:var(--line-2)}
.js .nav a.active .ic,.js .nav a.active .n{color:var(--accent-ink)}
.nav a.pp{gap:9px;padding:6px 8px}
.nav a.pp .ava{width:24px;height:24px;border-radius:6px}
.nav a.pp .nm{overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:.82rem}
.nav a.pp .st{margin-left:auto;width:7px;height:7px;border-radius:99px;flex:none;background:var(--faint)}
.st.completed{background:var(--ok)} .st.partial{background:var(--major)}
.st.abandoned,.st.failed{background:var(--blocker)} .st.unknown{background:var(--faint)}
.side .foot{margin-top:auto;border-top:1px solid var(--line);padding:12px 10px 4px;
  color:var(--muted);font-size:.74rem;line-height:1.5}
.side .foot .row{display:flex;justify-content:space-between;gap:8px}
.side .foot .row span:last-child{color:var(--ink-soft);font-weight:500;font-family:var(--mono);
  font-variant-numeric:tabular-nums;text-align:right;font-size:.7rem}
.side .foot .name{color:var(--ink);font-weight:600;font-size:.82rem;margin-bottom:8px;word-break:break-word}
/* collapsed rail */
.app.collapsed{grid-template-columns:64px minmax(0,1fr)}
.app.collapsed .side{padding:16px 8px;align-items:stretch}
.app.collapsed .side-top{flex-direction:column;gap:12px;padding:2px 0 12px;align-items:center}
.app.collapsed .brand .word,.app.collapsed .navlabel,.app.collapsed .nav a .n,.app.collapsed .nav a .k,
.app.collapsed .nav a span.lbl,.app.collapsed .nav a .nm,.app.collapsed .nav a.pp .st,.app.collapsed .side .foot{display:none}
.app.collapsed .side-toggle{margin:0}
.app.collapsed .nav a{justify-content:center;padding:9px 0}
.app.collapsed .nav{gap:4px}

/* ---------------------------------------------------------------- top bar */
.main{min-width:0;display:flex;flex-direction:column}
.topbar{position:sticky;top:0;z-index:20;display:flex;align-items:center;gap:10px;
  padding:0 28px;height:54px;border-bottom:1px solid var(--line);background:var(--bg)}
.crumb{display:flex;align-items:center;gap:8px;color:var(--muted);font-size:.82rem;min-width:0;white-space:nowrap}
.crumb b{color:var(--ink);font-weight:600;overflow:hidden;text-overflow:ellipsis}
.crumb .sep{color:var(--faint)}
.tb-right{margin-left:auto;display:flex;align-items:center;gap:6px}
.search{display:flex;align-items:center;gap:8px;height:32px;padding:0 10px;border:1px solid var(--line-2);
  border-radius:8px;background:var(--panel);color:var(--muted);min-width:230px;transition:border-color .12s}
.search:focus-within{border-color:var(--accent);color:var(--ink)}
.search .ic{width:15px;height:15px}
.search input{flex:1;border:0;background:transparent;color:var(--ink);font:inherit;font-size:.84rem;outline:0;min-width:0}
.search input::placeholder{color:var(--faint)}
.tbtn{height:32px;min-width:32px;padding:0 9px;display:inline-flex;align-items:center;gap:7px;border:1px solid var(--line-2);
  border-radius:8px;background:transparent;color:var(--muted);cursor:pointer;font-size:.78rem;font-weight:550;
  transition:color .12s,border-color .12s,background .12s;white-space:nowrap}
.tbtn:hover{color:var(--ink);border-color:var(--line-3);background:var(--panel-2)}
.tbtn .ic{width:16px;height:16px}
.tbtn .sun,.tbtn .moon{display:none}
:root[data-theme="light"] .tbtn .moon{display:inline-block}
:root[data-theme="dark"] .tbtn .sun{display:inline-block}
:root:not([data-theme]) .tbtn .sun{display:inline-block}
@media(prefers-color-scheme:light){:root:not([data-theme]) .tbtn .sun{display:none}:root:not([data-theme]) .tbtn .moon{display:inline-block}}
details.menu{position:relative}
details.menu summary{list-style:none;cursor:pointer}
details.menu summary::-webkit-details-marker{display:none}
details.menu .dd{position:absolute;right:0;top:38px;z-index:30;min-width:220px;background:var(--panel);
  border:1px solid var(--line-2);border-radius:10px;padding:6px;box-shadow:var(--shadow)}
details.menu .dd a{display:flex;align-items:center;gap:10px;padding:8px 10px;border-radius:7px;color:var(--ink-soft);font-size:.82rem}
details.menu .dd a:hover{background:var(--panel-2);color:var(--ink);text-decoration:none}
details.menu .dd a .ic{width:15px;height:15px;color:var(--faint)}
details.menu .dd a small{margin-left:auto;color:var(--faint);font-family:var(--mono);font-size:.66rem}

/* ---------------------------------------------------------------- views */
.content{padding:24px 28px 72px;width:100%}
.view{display:block}
.js .view{display:none}
.js .view.active{display:block;animation:fade .22s var(--ease)}
@keyframes fade{from{opacity:0;transform:translateY(4px)}to{opacity:1;transform:none}}
.vhead{margin:2px 0 18px;display:flex;align-items:flex-end;gap:24px;flex-wrap:wrap}
.vhead h1{font-size:1.45rem;font-weight:650;letter-spacing:-.025em;line-height:1.2}
.vhead p{color:var(--muted);font-size:.86rem;margin-top:5px;max-width:66ch}
.vhead .eyebrow{font-family:var(--mono);font-size:.66rem;font-weight:600;letter-spacing:.14em;
  text-transform:uppercase;color:var(--accent-ink);margin-bottom:8px;display:flex;align-items:center;gap:10px}
.vhead .eyebrow i{width:18px;height:1px;background:var(--accent);display:inline-block}
.vhead .lead{color:var(--ink);font-size:1rem;line-height:1.55;max-width:74ch;margin-top:6px}
.vhead .lead b{font-weight:600}
.vhead .lead .num{color:var(--accent-ink);font-weight:600}
.vhead .lead .fr{color:var(--blocker);font-weight:600}
.vhead .right{margin-left:auto;display:flex;gap:8px;align-items:center}

/* KPI strip */
.kpis{display:grid;grid-template-columns:repeat(5,1fr);gap:1px;background:var(--line);
  border:1px solid var(--line);border-radius:12px;overflow:hidden;margin-bottom:18px}
.kpi{background:var(--panel);padding:15px 18px 14px;position:relative}
.kpi .k{color:var(--muted);font-size:.68rem;font-weight:600;text-transform:uppercase;letter-spacing:.08em}
.kpi .v{font-family:var(--mono);font-size:2rem;font-weight:600;letter-spacing:-.03em;
  margin-top:8px;line-height:1;font-variant-numeric:tabular-nums}
.kpi .v small{color:var(--faint);font-size:.9rem;font-weight:500}
.kpi .v.blocker{color:var(--blocker)} .kpi .v.ok{color:var(--ok)} .kpi .v.accent{color:var(--accent-ink)}
.kpi .note{color:var(--muted);font-size:.74rem;margin-top:7px}
.kpi .spark{position:absolute;right:16px;top:16px}

.panel{background:var(--panel);border:1px solid var(--line);border-radius:12px;min-width:0}
.panel + .panel,.grid2 + .panel,.panel + .grid2{margin-top:16px}
.panel .ph{padding:12px 18px;border-bottom:1px solid var(--line);display:flex;align-items:center;gap:10px;flex-wrap:wrap}
.panel .ph h3{font-size:.84rem;font-weight:600;letter-spacing:.005em}
.panel .ph .sub{color:var(--muted);font-size:.76rem}
.panel .ph .right{margin-left:auto;display:flex;gap:8px;align-items:center;color:var(--muted);font-size:.74rem}
.panel .pb{padding:16px 18px}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-top:16px}
.grid2 .panel{margin:0}

/* distribution bars */
.dist{display:flex;height:10px;border-radius:6px;overflow:hidden;background:var(--raise);gap:2px}
.dist i{display:block;height:100%;transform-origin:left;transition:transform .9s var(--ease)}
.js .dist:not(.in) i{transform:scaleX(0)}
.sev-blocker{background:var(--blocker)} .sev-major{background:var(--major)}
.sev-minor{background:var(--minor)} .sev-nitpick{background:var(--nitpick)}
.seg-completed{background:var(--ok)} .seg-partial{background:var(--major)}
.seg-abandoned{background:var(--blocker)} .seg-failed{background:var(--faint)} .seg-unknown{background:var(--faint)}
.lg{display:flex;flex-wrap:wrap;gap:14px;margin-top:12px;font-size:.78rem;color:var(--muted)}
.lg span{display:inline-flex;align-items:center;gap:7px}
.lg i{width:9px;height:9px;border-radius:3px;flex:none}
.lg b{color:var(--ink);font-weight:600;font-family:var(--mono);font-variant-numeric:tabular-nums}

/* ---------------------------------------------------------------- journey map */
.jm{display:grid;grid-template-columns:200px minmax(0,1fr) 150px;gap:0 16px;align-items:center}
.jm-head{display:contents}
.jm-head > div{color:var(--faint);font-size:.64rem;font-weight:600;text-transform:uppercase;letter-spacing:.12em;padding-bottom:10px}
.jm-axis{position:relative;height:14px;border-bottom:1px solid var(--line-2)}
.jm-axis i{position:absolute;bottom:-1px;width:1px;height:5px;background:var(--line-3)}
.jm-axis i.maj{height:9px;background:var(--faint)}
.jm-axis b{position:absolute;bottom:6px;transform:translateX(-50%);font:600 .6rem var(--mono);color:var(--faint)}
.jm-row{display:contents}
.jm-row > *{padding:7px 0;border-bottom:1px solid var(--line)}
.jm-row:last-child > *{border-bottom:0}
.jm-who{display:flex;align-items:center;gap:10px;min-width:0}
.jm-who .nm{font-weight:550;font-size:.84rem;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.jm-who .sub{color:var(--muted);font-size:.7rem;display:flex;align-items:center;gap:6px;text-transform:capitalize}
.jm-strip{display:grid;grid-template-columns:repeat(var(--n,1),minmax(0,1fr));gap:3px;height:30px;align-items:stretch}
.jm-cell{min-width:0;border-radius:3px;background:var(--raise);position:relative;cursor:pointer;
  border:0;padding:0;transition:transform .12s,filter .12s;transform-origin:center bottom}
.jm-cell.fr1{background:var(--fr1)} .jm-cell.fr2{background:var(--fr2)} .jm-cell.fr3{background:var(--fr3)}
.jm-cell.shot::after{content:"";position:absolute;left:50%;bottom:4px;width:3px;height:3px;border-radius:99px;
  background:rgba(255,255,255,.55);transform:translateX(-50%)}
.jm-cell:hover,.jm-cell:focus-visible{transform:scaleY(1.18);filter:brightness(1.25);outline:0;z-index:2}
.jm-cell.on{outline:2px solid var(--accent);outline-offset:1px;z-index:2}
.js .jm-strip:not(.in) .jm-cell{transform:scaleY(0)}
.jm-strip.in .jm-cell{animation:rise .5s var(--ease) both;animation-delay:calc(var(--i) * 22ms)}
@keyframes rise{from{transform:scaleY(0);opacity:.4}to{transform:scaleY(1);opacity:1}}
.jm-empty{color:var(--faint);font-size:.76rem;display:flex;align-items:center;height:30px;padding-left:2px;font-style:italic}
.jm-tail{display:flex;align-items:center;gap:10px;justify-content:flex-end}
.jm-tail .meter{flex:none}
.jm-tail .dur{font-family:var(--mono);font-size:.7rem;color:var(--muted);min-width:44px;text-align:right}
.jm-legend{display:flex;gap:16px;flex-wrap:wrap;align-items:center;margin-top:14px;padding-top:12px;border-top:1px solid var(--line);
  color:var(--muted);font-size:.74rem}
.jm-legend span{display:inline-flex;align-items:center;gap:6px}
.jm-legend i{width:12px;height:12px;border-radius:3px;background:var(--raise);display:inline-block}
.jm-legend i.fr1{background:var(--fr1)} .jm-legend i.fr2{background:var(--fr2)} .jm-legend i.fr3{background:var(--fr3)}
.jm-legend .hint{margin-left:auto;color:var(--faint)}
.tip{position:fixed;z-index:90;pointer-events:none;max-width:320px;background:var(--panel);color:var(--ink);
  border:1px solid var(--line-2);border-radius:9px;padding:9px 11px;font-size:.78rem;line-height:1.45;
  box-shadow:var(--shadow);opacity:0;transform:translateY(4px);transition:opacity .12s,transform .12s}
.tip.show{opacity:1;transform:none}
.tip .t{font-weight:600;display:flex;gap:8px;align-items:center;margin-bottom:3px}
.tip .t .num{color:var(--muted);font-size:.7rem}
.tip .s{color:var(--muted)}
.tip .q{color:var(--ink-soft);font-style:italic;margin-top:5px;border-top:1px solid var(--line);padding-top:5px}

/* who hit what matrix */
.mx{width:100%;border-collapse:separate;border-spacing:0;font-size:.82rem}
.mx th{font-size:.64rem;color:var(--faint);font-weight:600;text-transform:uppercase;letter-spacing:.08em;
  padding:6px 8px;border-bottom:1px solid var(--line);text-align:left;vertical-align:bottom}
.mx th.p{text-align:center;width:52px}
.mx th.p .ava{width:24px;height:24px;border-radius:6px;margin:0 auto 4px}
.mx th.p span{display:block;font-size:.6rem;letter-spacing:.02em;text-transform:none;font-weight:600;color:var(--muted);
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:52px}
.mx td{padding:7px 8px;border-bottom:1px solid var(--line);vertical-align:middle}
.mx tr:last-child td{border-bottom:0}
.mx tr:hover td{background:var(--panel-2)}
.mx td.w{color:var(--ink-soft);max-width:0;width:100%}
.mx td.w .rk{font-family:var(--mono);color:var(--faint);font-size:.7rem;margin-right:8px}
.mx td.w .pill{margin-right:8px}
.mx td.w span.txt{white-space:nowrap;overflow:hidden;text-overflow:ellipsis;display:inline-block;max-width:calc(100% - 110px);vertical-align:middle}
.mx td.c{text-align:center}
.mx td.c i{display:inline-block;width:12px;height:12px;border-radius:99px;background:var(--raise);border:1px solid var(--line-2)}
.mx td.c i.blocker{background:var(--blocker);border-color:transparent}
.mx td.c i.major{background:var(--major);border-color:transparent}
.mx td.c i.minor{background:var(--minor);border-color:transparent}
.mx td.c i.nitpick{background:var(--nitpick);border-color:transparent}
.mx td.c i.none{background:transparent;border-style:dashed;opacity:.5;width:8px;height:8px}
.mx td.r{text-align:right;font-family:var(--mono);color:var(--muted);font-size:.72rem;white-space:nowrap}

/* ---------------------------------------------------------------- tables */
.scroll{overflow-x:auto;-webkit-overflow-scrolling:touch}
table{width:100%;border-collapse:collapse;font-size:.86rem}
thead th{background:var(--panel)}
th,td{text-align:left;padding:12px 14px;border-bottom:1px solid var(--line);vertical-align:middle}
tbody tr:last-child td{border-bottom:0}
tbody tr:hover{background:var(--panel-2)}
th{color:var(--faint);font-weight:600;font-size:.66rem;text-transform:uppercase;letter-spacing:.08em}
td.num{font-family:var(--mono);font-variant-numeric:tabular-nums;color:var(--ink-soft)}
.who{display:flex;align-items:center;gap:10px;min-width:160px}
td.task{min-width:11rem;max-width:18rem;color:var(--ink-soft);font-size:.84rem}
.ava{width:30px;height:30px;border-radius:8px;flex:none;display:grid;place-items:center;color:#fff;background:var(--accent)}
.ava .ic{width:60%;height:60%}
.ava.blocker{background:var(--blocker)} .ava.major{background:var(--major)} .ava.ok{background:var(--ok)}
.who .nm{font-weight:550} .who .dev{color:var(--muted);font-size:.72rem;text-transform:capitalize}
.fixcell{min-width:16rem;max-width:30rem;color:var(--ink-soft);font-size:.83rem}
.fixcell span{display:-webkit-box;-webkit-line-clamp:4;-webkit-box-orient:vertical;overflow:hidden}
.badge{display:inline-flex;align-items:center;gap:6px;font-size:.74rem;font-weight:550;
  padding:3px 9px;border-radius:6px;border:1px solid var(--line-2);white-space:nowrap;text-transform:capitalize}
.badge .st{width:6px;height:6px;border-radius:99px;background:var(--muted)}
.badge.completed{color:var(--ok)} .badge.partial{color:var(--major)}
.badge.abandoned,.badge.failed{color:var(--blocker)}
.meter{display:flex;align-items:center;gap:8px;font-family:var(--mono);font-size:.78rem}
.meter .track{width:46px;height:5px;border-radius:99px;background:var(--raise);overflow:hidden;flex:none}
.meter .fill{height:100%;border-radius:99px;background:var(--accent)}
.meter.low .fill{background:var(--blocker)} .meter.mid .fill{background:var(--major)} .meter.high .fill{background:var(--ok)}
.bnum{font-family:var(--mono);font-weight:600;color:var(--blocker)}
.zero{color:var(--faint)}
.spark{display:inline-flex;gap:1px;align-items:flex-end;height:18px}
.spark i{display:block;width:3px;border-radius:1px;background:var(--raise-2);height:25%}
.spark i.fr1{background:var(--fr1);height:50%} .spark i.fr2{background:var(--fr2);height:75%} .spark i.fr3{background:var(--fr3);height:100%}
.abtn{display:inline-flex;align-items:center;gap:6px;color:var(--muted);font-size:.74rem;font-weight:550;border:1px solid var(--line-2);
  background:transparent;border-radius:7px;padding:4px 9px;white-space:nowrap;cursor:pointer;transition:color .12s,border-color .12s,background .12s}
.abtn:hover{color:var(--ink);border-color:var(--line-3);text-decoration:none;background:var(--panel-2)}
.abtn.pri{color:var(--accent-ink);border-color:color-mix(in srgb,var(--accent) 45%,transparent)}
.abtn.pri:hover{background:var(--accent-bg)}
.abtn .ic{width:13px;height:13px}
.acts{display:flex;gap:6px;justify-content:flex-end}

/* ---------------------------------------------------------------- issues */
.fbar{position:sticky;top:54px;z-index:10;display:flex;flex-wrap:wrap;gap:8px;align-items:center;
  padding:10px 0 12px;background:var(--bg);border-bottom:1px solid var(--line);margin-bottom:6px}
.fbar .grp{display:flex;gap:4px;align-items:center;padding:3px;border:1px solid var(--line);border-radius:9px;background:var(--panel)}
.chipb{border:0;background:transparent;color:var(--muted);font-size:.74rem;font-weight:550;padding:4px 9px;border-radius:6px;
  cursor:pointer;display:inline-flex;align-items:center;gap:6px;transition:background .12s,color .12s;white-space:nowrap}
.chipb:hover{color:var(--ink);background:var(--panel-2)}
.chipb.on{background:var(--raise);color:var(--ink)}
.chipb i{width:7px;height:7px;border-radius:99px;background:currentColor;opacity:.9}
.chipb.blocker i{background:var(--blocker)} .chipb.major i{background:var(--major)}
.chipb.minor i{background:var(--minor)} .chipb.nitpick i{background:var(--nitpick)}
.chipb.measured i{background:var(--ok)} .chipb.observed i{background:var(--muted)} .chipb.impression i{background:transparent;border:1px dashed var(--muted)}
.chipb .ava{width:18px;height:18px;border-radius:5px}
.fbar select{height:30px;border:1px solid var(--line-2);border-radius:8px;background:var(--panel);color:var(--ink-soft);
  font:inherit;font-size:.76rem;padding:0 8px;cursor:pointer}
.fbar .tail{margin-left:auto;display:flex;align-items:center;gap:10px}
.fbar .count{color:var(--muted);font-size:.76rem;font-family:var(--mono);white-space:nowrap}
.fbar .count b{color:var(--ink)}
.fbar .clear{color:var(--accent-ink);font-size:.74rem;background:none;border:0;cursor:pointer;padding:0 4px}
.band{display:flex;align-items:center;gap:8px;margin:22px 0 10px;font-size:.7rem;font-weight:600;
  text-transform:uppercase;letter-spacing:.12em;color:var(--muted)}
.band:first-child{margin-top:8px}
.band .count{background:var(--raise);border:1px solid var(--line-2);color:var(--ink);
  border-radius:99px;padding:1px 8px;font-size:.68rem;font-family:var(--mono)}
.band .desc{color:var(--faint);text-transform:none;letter-spacing:0;font-weight:500;font-size:.74rem}
.band::after{content:"";flex:1;height:1px;background:var(--line)}
.f{position:relative;background:var(--panel);border:1px solid var(--line);
  border-radius:11px;padding:15px 17px;margin:9px 0;transition:border-color .12s,background .12s}
.f:hover{border-color:var(--line-2);background:var(--panel-2)}
.f.blocker{--edge:var(--blocker)} .f.major{--edge:var(--major)}
.f.minor{--edge:var(--minor)} .f.nitpick{--edge:var(--nitpick)}
.f .head{display:flex;gap:12px;align-items:baseline}
.f .rank{font-family:var(--mono);font-size:.8rem;font-weight:600;color:var(--faint);flex:none;min-width:2.2ch}
.f .what{color:var(--ink);font-weight:550;font-size:.95rem;line-height:1.45;flex:1}
.f .copy{flex:none;align-self:flex-start;opacity:0;transition:opacity .12s}
.f:hover .copy,.f:focus-within .copy{opacity:1}
.f .who-row{display:flex;gap:5px;align-items:center;margin-top:10px;padding-left:calc(2.2ch + 12px)}
.f .who-row .ava{width:22px;height:22px;border-radius:6px;position:relative}
.f .who-row .ava i{position:absolute;right:-3px;bottom:-3px;width:9px;height:9px;border-radius:99px;border:2px solid var(--panel)}
.f .who-row .ava i.blocker{background:var(--blocker)} .f .who-row .ava i.major{background:var(--major)}
.f .who-row .ava i.minor{background:var(--minor)} .f .who-row .ava i.nitpick{background:var(--nitpick)}
.f .who-row .lbl{color:var(--muted);font-size:.74rem;margin-left:6px}
.pill{display:inline-block;padding:1px 7px;border-radius:5px;font-size:.62rem;font-weight:700;
  text-transform:uppercase;letter-spacing:.06em;margin-right:8px;vertical-align:middle;
  color:var(--edge,var(--muted));border:1px solid currentColor;font-family:var(--mono)}
.pill.blocker{color:var(--blocker)} .pill.major{color:var(--major)} .pill.minor{color:var(--minor)} .pill.nitpick{color:var(--nitpick)}
.tags{display:flex;flex-wrap:wrap;gap:6px;margin:10px 0 0;padding-left:calc(2.2ch + 12px)}
.tag{font-size:.7rem;font-weight:550;padding:2px 8px;border-radius:6px;background:var(--raise);
  border:1px solid var(--line);color:var(--ink-soft);white-space:nowrap;font-family:var(--mono)}
.tag.hot{background:transparent;border-color:var(--blocker);color:var(--blocker)}
.tag.star{background:transparent;border-color:var(--major);color:var(--major)}
.tag.grade-measured{border-color:color-mix(in srgb,var(--ok) 50%,transparent);color:var(--ok)}
.tag.grade-impression{border-style:dashed;color:var(--muted)}
.f .meta{color:var(--muted);font-size:.78rem;margin-top:10px;padding-left:calc(2.2ch + 12px)}
.f .fix{color:var(--ink-soft);font-size:.85rem;margin-top:9px;padding-left:calc(2.2ch + 12px)}
.f .fix strong{color:var(--ink);font-weight:600}
details.ev{margin:8px 0 0;padding-left:calc(2.2ch + 12px)}
details.ev summary{cursor:pointer;color:var(--muted);font-size:.78rem;font-weight:550;list-style:none;
  display:inline-flex;align-items:center;gap:6px}
details.ev summary::-webkit-details-marker{display:none}
details.ev summary::before{content:"+";color:var(--accent-ink);font-family:var(--mono);font-weight:700}
details.ev[open] summary::before{content:"\2212"}
details.ev ul{margin:8px 0 0;padding-left:16px;color:var(--ink-soft);font-size:.82rem}
details.ev li{margin:3px 0}
.f.hide{display:none}
.band.hide{display:none}

/* ---------------------------------------------------------------- replay */
.rp-tabs{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:14px}
.rp-tab{display:inline-flex;align-items:center;gap:8px;padding:6px 12px 6px 7px;border:1px solid var(--line-2);border-radius:9px;
  background:var(--panel);color:var(--ink-soft);cursor:pointer;font-size:.82rem;font-weight:550;transition:border-color .12s,background .12s,color .12s}
.rp-tab .ava{width:22px;height:22px;border-radius:6px}
.rp-tab .st{width:7px;height:7px;border-radius:99px}
.rp-tab:hover{border-color:var(--line-3);color:var(--ink)}
.rp-tab.on{border-color:var(--accent);background:var(--accent-bg);color:var(--accent-ink)}
.rp{display:grid;grid-template-columns:minmax(0,1.55fr) minmax(300px,.85fr);gap:16px;align-items:stretch}
.rp-stage{background:var(--panel);border:1px solid var(--line);border-radius:12px;overflow:hidden;display:flex;flex-direction:column;min-width:0}
.rp-chrome{display:flex;align-items:center;gap:8px;padding:9px 12px;border-bottom:1px solid var(--line);background:var(--panel-2)}
.rp-chrome i{width:9px;height:9px;border-radius:99px;background:var(--raise-2);display:inline-block}
.rp-chrome .url{margin-left:8px;font-family:var(--mono);font-size:.7rem;color:var(--muted);flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.rp-chrome .dev{font-size:.66rem;color:var(--faint);text-transform:uppercase;letter-spacing:.1em;font-weight:600}
.rp-shot{position:relative;background:#050506;flex:1;min-height:420px;max-height:min(64vh,720px);display:grid;place-items:center;overflow:hidden;
  background-image:radial-gradient(circle at center,rgba(255,255,255,.035) 0,transparent 60%)}
:root[data-theme="light"] .rp-shot{background-color:#e4e6ea}
.rp-shot img{max-width:100%;max-height:100%;width:auto;height:auto;object-fit:contain;display:block;
  box-shadow:0 20px 60px -20px rgba(0,0,0,.8);animation:shot .35s var(--ease)}
@keyframes shot{from{opacity:0;transform:scale(.985)}to{opacity:1;transform:none}}
.rp-shot .none{color:var(--faint);font-size:.9rem;text-align:center;padding:40px;max-width:46ch}
.rp-shot .none b{display:block;color:var(--muted);font-size:.7rem;letter-spacing:.12em;text-transform:uppercase;margin-bottom:8px}
.rp-shot .tag-n{position:absolute;left:12px;top:12px;font:600 .7rem var(--mono);color:#fff;background:rgba(0,0,0,.55);
  padding:3px 8px;border-radius:6px;backdrop-filter:none;border:1px solid rgba(255,255,255,.15)}
.rp-shot .feel{position:absolute;right:12px;top:12px;font-size:.74rem;font-weight:550;color:#fff;background:rgba(0,0,0,.55);
  padding:3px 9px;border-radius:6px;border:1px solid rgba(255,255,255,.15);text-transform:capitalize}
.rp-shot .cross{position:absolute;inset:0;pointer-events:none;opacity:.22}
.rp-shot .cross::before,.rp-shot .cross::after{content:"";position:absolute;background:var(--accent)}
.rp-shot .cross::before{left:0;right:0;top:50%;height:1px}
.rp-shot .cross::after{top:0;bottom:0;left:50%;width:1px}
.rp-cap{padding:12px 16px;border-top:1px solid var(--line);display:flex;gap:12px;align-items:center;min-height:52px}
.rp-cap .act{color:var(--ink);font-size:.9rem;font-weight:500;flex:1}
.rp-cap .fric{display:inline-flex;gap:3px;flex:none}
.rp-cap .fric i{width:14px;height:6px;border-radius:2px;background:var(--raise-2)}
.rp-cap .fric i.on1{background:var(--fr1)} .rp-cap .fric i.on2{background:var(--fr2)} .rp-cap .fric i.on3{background:var(--fr3)}
.rp-side{display:flex;flex-direction:column;gap:12px;min-width:0}
.rp-card{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:16px 18px}
.rp-card .lbl{color:var(--faint);font-size:.64rem;font-weight:600;text-transform:uppercase;letter-spacing:.12em;margin-bottom:5px}
.rp-card .big{font-family:var(--mono);font-size:2.2rem;font-weight:600;letter-spacing:-.03em;line-height:1;color:var(--ink)}
.rp-card .big small{color:var(--faint);font-size:1rem;font-weight:500}
.rp-card .intent{font-size:1.02rem;font-weight:600;line-height:1.4;color:var(--ink);margin-top:10px;letter-spacing:-.01em}
.rp-kv{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:14px}
.rp-kv > div{padding:10px 12px;border:1px solid var(--line);border-radius:9px;background:var(--panel-2);font-size:.82rem;color:var(--ink-soft);line-height:1.5}
.rp-kv > div.bad{border-color:color-mix(in srgb,var(--blocker) 45%,transparent);background:color-mix(in srgb,var(--blocker) 7%,transparent)}
.rp-kv .lbl{margin-bottom:4px}
.rp-thought{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:16px 18px;flex:1;position:relative}
.rp-thought .q{font-size:1rem;line-height:1.6;color:var(--ink);font-style:italic}
.rp-thought .q::before{content:"\201C";color:var(--accent);font-style:normal;font-weight:700;margin-right:2px}
.rp-thought .cite{display:flex;align-items:center;gap:9px;margin-top:12px;color:var(--muted);font-size:.78rem;font-weight:550}
.rp-thought .cite .ava{width:22px;height:22px;border-radius:6px}
.rp-thought .empty-q{color:var(--faint);font-style:italic;font-size:.85rem}
.rp-bar{margin-top:16px;background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:12px 16px 14px}
.rp-ctl{display:flex;align-items:center;gap:8px;margin-bottom:10px}
.rp-ctl .pos{font-family:var(--mono);font-size:.76rem;color:var(--muted);margin-left:6px;min-width:80px}
.rp-ctl .pos b{color:var(--ink)}
.rp-ctl .hint{margin-left:auto;color:var(--faint);font-size:.72rem;display:flex;gap:10px;align-items:center}
.rp-ctl .hint span{display:inline-flex;gap:4px;align-items:center}
.ibtn{width:32px;height:32px;display:grid;place-items:center;border:1px solid var(--line-2);border-radius:8px;background:transparent;
  color:var(--ink-soft);cursor:pointer;transition:background .12s,color .12s,border-color .12s}
.ibtn:hover{background:var(--panel-2);color:var(--ink);border-color:var(--line-3)}
.ibtn.pri{background:var(--accent);color:#fff;border-color:transparent}
.ibtn.pri:hover{background:color-mix(in srgb,var(--accent) 85%,#fff);color:#fff}
.ibtn .ic{width:16px;height:16px}
.ibtn .pause{display:none}
.ibtn.playing .play{display:none} .ibtn.playing .pause{display:inline-block}
.rp-tl{display:flex;gap:3px;height:34px;align-items:stretch}
.rp-seg{flex:1 1 0;min-width:6px;border:0;padding:0;border-radius:3px;background:var(--raise);cursor:pointer;position:relative;
  transition:filter .12s,transform .12s;transform-origin:center bottom}
.rp-seg.fr1{background:var(--fr1)} .rp-seg.fr2{background:var(--fr2)} .rp-seg.fr3{background:var(--fr3)}
.rp-seg.shot::after{content:"";position:absolute;left:50%;bottom:4px;width:3px;height:3px;border-radius:99px;background:rgba(255,255,255,.55);transform:translateX(-50%)}
.rp-seg:hover{filter:brightness(1.25)}
.rp-seg.on{outline:2px solid var(--accent);outline-offset:2px}
.rp-seg.done{opacity:.55}
.rp-seg.on.done{opacity:1}
.rp-axis{position:relative;height:16px;margin-top:6px}
.rp-axis b{position:absolute;transform:translateX(-50%);font:600 .6rem var(--mono);color:var(--faint);top:2px}
.rp-axis i{position:absolute;top:0;width:1px;height:4px;background:var(--line-3)}
.rp-none{color:var(--muted);font-size:.9rem;padding:40px;text-align:center;border:1px dashed var(--line-2);border-radius:12px}

/* ---------------------------------------------------------------- gallery */
.gal + .gal{margin-top:22px}
.gal h4{font-size:.85rem;font-weight:600;margin-bottom:10px;display:flex;align-items:center;gap:9px}
.gal h4 .ava{width:24px;height:24px;border-radius:6px}
.gal h4 .n{color:var(--muted);font-weight:500;font-family:var(--mono);font-size:.72rem}
.gal h4 .abtn{margin-left:auto}
.strip{display:flex;gap:12px;overflow-x:auto;padding-bottom:10px;scroll-snap-type:x proximity;scrollbar-width:thin}
.strip figure{margin:0;flex:0 0 232px;scroll-snap-align:start}
.strip a,.strip button{display:block;width:100%;padding:0;border:0;background:none;cursor:zoom-in;text-align:left}
.strip img{width:100%;height:150px;object-fit:cover;object-position:top left;border-radius:9px;
  border:1px solid var(--line);background:var(--panel-2);display:block;transition:border-color .12s,transform .2s var(--ease)}
.strip button:hover img{border-color:var(--line-3);transform:translateY(-2px)}
.strip figcaption{color:var(--muted);font-size:.74rem;margin-top:8px;line-height:1.4;display:flex;gap:6px}
.strip figcaption .n{font-family:var(--mono);color:var(--faint);flex:none}
.strip figcaption .fr{margin-left:auto;flex:none;display:inline-flex;gap:2px;align-items:center;padding-top:5px}
.strip figcaption .fr i{width:7px;height:5px;border-radius:1px;background:var(--raise-2)}
.strip figcaption .fr i.on1{background:var(--fr1)} .strip figcaption .fr i.on2{background:var(--fr2)} .strip figcaption .fr i.on3{background:var(--fr3)}

/* lightbox */
.lb{position:fixed;inset:0;z-index:130;display:none;flex-direction:column;background:rgba(4,5,8,.92)}
.lb.open{display:flex}
.lb-head{display:flex;align-items:center;gap:12px;padding:12px 18px;color:#fff}
.lb-head .t{font-weight:600;font-size:.9rem;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;flex:1}
.lb-head .pos{font-family:var(--mono);font-size:.74rem;color:rgba(255,255,255,.6)}
.lb-head .ibtn{color:#fff;border-color:rgba(255,255,255,.25)}
.lb-head .ibtn:hover{background:rgba(255,255,255,.1);color:#fff}
.lb-body{flex:1;display:grid;place-items:center;padding:10px 70px 20px;min-height:0;position:relative}
.lb-body img{max-width:100%;max-height:100%;object-fit:contain;border-radius:6px;box-shadow:0 40px 100px -30px #000;animation:shot .25s var(--ease)}
.lb-nav{position:absolute;top:50%;transform:translateY(-50%);width:44px;height:44px;border-radius:99px;border:1px solid rgba(255,255,255,.25);
  background:rgba(0,0,0,.5);color:#fff;cursor:pointer;display:grid;place-items:center}
.lb-nav:hover{background:rgba(255,255,255,.15)}
.lb-nav.prev{left:14px} .lb-nav.next{right:14px}
.lb-nav .ic{width:18px;height:18px}
.lb-foot{padding:10px 18px 18px;color:rgba(255,255,255,.75);font-size:.84rem;text-align:center;max-width:80ch;margin:0 auto}
.lb-foot b{color:#fff}

/* ---------------------------------------------------------------- voices */
.quote{background:var(--panel);border:1px solid var(--line);border-radius:11px;padding:16px 18px;margin:10px 0}
.quote p{color:var(--ink);font-size:.98rem;line-height:1.62}
.quote p::before{content:"\201C";color:var(--accent);font-weight:700;margin-right:2px}
.quote .cite{display:flex;align-items:center;gap:9px;margin-top:12px;color:var(--muted);font-size:.78rem;font-weight:550}
.quote .cite .ava{width:24px;height:24px;border-radius:6px}
.quote .cite .badge{margin-left:auto}
.quote .arc{margin-top:12px;padding-top:12px;border-top:1px solid var(--line);color:var(--ink-soft);font-size:.84rem}
.quote .arc b{color:var(--muted);font-size:.64rem;text-transform:uppercase;letter-spacing:.12em;display:block;margin-bottom:4px;font-weight:600}
.worked{list-style:none;padding:0;margin:0;display:grid;gap:8px;grid-template-columns:repeat(auto-fill,minmax(300px,1fr))}
.worked li{background:var(--panel);border:1px solid var(--line);border-radius:9px;
  padding:11px 13px 11px 34px;position:relative;font-size:.85rem;color:var(--ink-soft)}
.worked li::before{content:"\2713";position:absolute;left:13px;top:11px;color:var(--ok);font-weight:700}
.worked .by{color:var(--muted);font-size:.76rem}
.qgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(360px,1fr));gap:12px}
.qgrid .quote{margin:0}

.empty{color:var(--muted);font-size:.88rem;padding:26px;text-align:center;border:1px dashed var(--line-2);border-radius:12px}
.foot{color:var(--faint);font-size:.78rem;margin-top:26px;padding-top:16px;border-top:1px solid var(--line);line-height:1.65;max-width:70ch}

/* ---------------------------------------------------------------- modals */
.modal{position:fixed;inset:0;z-index:120;display:none;justify-content:center;align-items:flex-start;padding:44px 20px;overflow-y:auto;
  background:rgba(4,5,8,.7)}
.modal.open{display:flex}
.modal-card{background:var(--panel);border:1px solid var(--line-2);border-radius:14px;width:min(900px,100%);box-shadow:var(--shadow);margin:auto}
.modal-head{position:sticky;top:0;z-index:1;display:flex;align-items:center;gap:12px;
  padding:14px 20px;border-bottom:1px solid var(--line);background:var(--panel);border-radius:14px 14px 0 0}
.modal-head .t{font-weight:600;font-size:.92rem;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.modal-close{margin-left:auto;flex:none;width:32px;height:32px;display:grid;place-items:center;
  border:1px solid var(--line-2);border-radius:8px;background:var(--raise);color:var(--muted);cursor:pointer}
.modal-close:hover{color:var(--ink);border-color:var(--line-3)}
.modal-close .ic{width:16px;height:16px}
.modal-body{padding:22px 26px 30px}
.help .modal-card{width:min(560px,100%)}
.help table{font-size:.84rem}
.help td{padding:8px 6px;border-bottom:1px solid var(--line)}
.help td:first-child{width:130px;white-space:nowrap}
.help kbd{margin-right:3px}
.toast{position:fixed;left:50%;bottom:26px;transform:translate(-50%,10px);z-index:140;background:var(--ink);color:var(--bg);
  padding:9px 14px;border-radius:9px;font-size:.82rem;font-weight:550;opacity:0;transition:opacity .18s,transform .18s;pointer-events:none;
  box-shadow:var(--shadow)}
.toast.show{opacity:1;transform:translate(-50%,0)}

/* rendered session document */
.logdoc h2{font-size:1.15rem;font-weight:700;letter-spacing:-.01em;line-height:1.3;margin-bottom:6px}
.logdoc h2 .arrow{color:var(--faint);font-weight:400}
.logdoc h3{font-size:.8rem;text-transform:uppercase;letter-spacing:.1em;color:var(--muted);
  font-weight:600;margin:24px 0 10px;padding-bottom:8px;border-bottom:1px solid var(--line)}
.logdoc p{color:var(--ink-soft);margin:8px 0}
.logdoc p.one{font-size:1rem;color:var(--ink)}
.chips-row{display:flex;flex-wrap:wrap;gap:6px;margin:12px 0 4px}
.chip{font-size:.74rem;font-weight:500;color:var(--ink-soft);background:var(--raise);
  border:1px solid var(--line);border-radius:6px;padding:3px 9px;text-transform:capitalize;font-family:var(--mono)}
.logdoc .warn{margin:12px 0;padding:10px 12px;border-radius:8px;color:var(--blocker);
  border:1px solid color-mix(in srgb,var(--blocker) 40%,transparent);background:color-mix(in srgb,var(--blocker) 8%,transparent)}
.logdoc ul.kv{list-style:none;padding:0;margin:4px 0;display:grid;gap:6px}
.logdoc ul.kv li{color:var(--ink-soft);font-size:.88rem}
.logdoc ul.kv b{display:inline-block;min-width:64px;color:var(--muted);font-weight:600;margin-right:6px}
.logdoc ul{padding-left:20px} .logdoc li{margin:4px 0;color:var(--ink-soft)}
.logdoc blockquote{margin:8px 0;padding:10px 14px;border-left:3px solid var(--line-2);
  background:var(--panel-2);border-radius:0 8px 8px 0;color:var(--ink-soft);font-style:italic}
.logdoc table{width:100%;border-collapse:collapse;font-size:.8rem;margin:8px 0}
.logdoc th,.logdoc td{border:1px solid var(--line);padding:7px 9px;text-align:left;vertical-align:top}
.logdoc th{background:var(--panel-2);color:var(--muted);font-weight:600;font-size:.66rem;text-transform:uppercase;letter-spacing:.06em;position:static}
.logdoc td.num{font-family:var(--mono);color:var(--ink-soft)}
.logdoc details{margin:10px 0}
.logdoc summary{cursor:pointer;color:var(--accent-ink);font-weight:550;font-size:.84rem}
.logdoc .think{margin-top:10px}
.logdoc .think img{display:block;width:100%;max-width:520px;border:1px solid var(--line);border-radius:8px;margin:8px 0}
.logdoc .lf{border:1px solid var(--line);border-radius:9px;padding:11px 13px;margin:8px 0;background:var(--panel-2)}
.logdoc .lf b{color:var(--ink)}
.logdoc .lfrow{margin-top:6px;font-size:.84rem;color:var(--ink-soft)}
.logdoc .lfrow b{color:var(--muted);font-weight:600;margin-right:6px}

/* ---------------------------------------------------------------- responsive, motion, print */
@media(max-width:1180px){.rp{grid-template-columns:1fr}.jm{grid-template-columns:150px minmax(0,1fr) 110px}.kpis{grid-template-columns:repeat(3,1fr)}}
@media(max-width:840px){
  .app{grid-template-columns:1fr}
  .side{position:static;height:auto;flex-direction:row;flex-wrap:wrap;align-items:center;border-right:0;border-bottom:1px solid var(--line)}
  .side .foot,.navlabel,.nav.pl{display:none}
  .nav{flex-direction:row;flex-wrap:wrap}
  .nav a .n{margin-left:6px}
  .nav a .k{display:none}
  .kpis{grid-template-columns:repeat(2,1fr)}
  .kpi:last-child:nth-child(odd){grid-column:span 2}
  .grid2{grid-template-columns:1fr}
  .jm{grid-template-columns:110px minmax(0,1fr)}
  .jm-tail,.jm-head .tl{display:none}
  .search{min-width:0;width:150px}
  .content{padding:18px 16px 60px}
  .topbar{padding:0 16px}
  .fbar{position:static}
}
@media(prefers-reduced-motion:reduce){
  *,*::before,*::after{animation-duration:.001ms!important;animation-delay:0s!important;transition-duration:.001ms!important}
  .js .dist:not(.in) i,.js .jm-strip:not(.in) .jm-cell{transform:none}
}
@media print{
  .grain,.side,.topbar,.fbar,.rp-bar,.rp-tabs,.copy,.acts,.lb,.modal,.toast,.tip{display:none!important}
  .app{display:block}
  .js .view{display:block!important;page-break-before:always;animation:none}
  .js .view:first-child{page-break-before:auto}
  .content{padding:0}
  body{background:#fff;color:#000}
  .panel,.f,.quote,.kpi{break-inside:avoid;box-shadow:none}
  .f.hide{display:block}
}
"""
