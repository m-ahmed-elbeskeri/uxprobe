"""Runtime for the HTML dashboard: view routing, the session replay, the
journey map, issue filters, lightbox, shortcuts. Progressive enhancement only:
with JavaScript off every view is shown stacked and the page still reads."""

DASHBOARD_JS = r"""
(function(){
  if(document.documentElement.className.indexOf("js")<0){return;}
  var $=function(s,r){return (r||document).querySelector(s);};
  var $$=function(s,r){return [].slice.call((r||document).querySelectorAll(s));};
  var reduced=window.matchMedia&&window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var DATA={sessions:[]};
  try{DATA=JSON.parse($("#uxp-data").textContent);}catch(e){}
  var store={get:function(k){try{return localStorage.getItem(k);}catch(e){return null;}},
             set:function(k,v){try{localStorage.setItem(k,v);}catch(e){}}};

  /* ---------------------------------------------------------------- toast */
  var toastEl=$("#toast"),toastT=null;
  function toast(msg){if(!toastEl){return;}toastEl.textContent=msg;toastEl.classList.add("show");
    clearTimeout(toastT);toastT=setTimeout(function(){toastEl.classList.remove("show");},1600);}

  /* ---------------------------------------------------------------- theme */
  var themeBtn=$("#theme");
  var saved=store.get("uxprobe-theme");
  if(saved==="light"||saved==="dark"){document.documentElement.setAttribute("data-theme",saved);}
  function effectiveTheme(){
    var t=document.documentElement.getAttribute("data-theme");
    if(t){return t;}
    return (window.matchMedia&&window.matchMedia("(prefers-color-scheme: light)").matches)?"light":"dark";
  }
  if(themeBtn){themeBtn.addEventListener("click",function(){
    var next=effectiveTheme()==="dark"?"light":"dark";
    document.documentElement.setAttribute("data-theme",next);store.set("uxprobe-theme",next);
  });}

  /* ---------------------------------------------------------------- views */
  var navs=$$(".nav a[data-view]");
  var views=$$(".view");
  var ids=views.map(function(v){return v.getAttribute("data-name");});
  function viewEl(name){return views[ids.indexOf(name)]||null;}
  var seen={};
  function countUp(el){
    var target=parseFloat(el.getAttribute("data-count"));
    if(isNaN(target)){return;}
    if(reduced){el.textContent=Math.round(target).toString();return;}
    var t0=null,dur=800;
    function step(ts){if(!t0){t0=ts;}var p=Math.min(1,(ts-t0)/dur);
      el.textContent=Math.round(target*(1-Math.pow(1-p,3))).toString();
      if(p<1){requestAnimationFrame(step);}}
    requestAnimationFrame(step);
  }
  function enter(v){
    var key=v.getAttribute("data-name");
    if(seen[key]){return;}
    seen[key]=true;
    $$("[data-count]",v).forEach(countUp);
    requestAnimationFrame(function(){requestAnimationFrame(function(){
      $$(".dist",v).forEach(function(d){d.classList.add("in");});
      $$(".jm-strip",v).forEach(function(d){d.classList.add("in");});
      $$(".land",v).forEach(function(l){l.classList.add("in");land.settle(l);});
      $$(".fp",v).forEach(function(f){f.classList.add("in");});
    });});
  }
  var current="";
  function show(id,scroll){
    if(ids.indexOf(id)<0){id=ids[0]||"";}
    current=id;
    views.forEach(function(v){v.classList.toggle("active",v.getAttribute("data-name")===id);});
    navs.forEach(function(a){a.classList.toggle("active",a.getAttribute("data-view")===id);});
    var v=viewEl(id);
    if(v){enter(v);}
    if(scroll!==false){window.scrollTo(0,0);}
    if(id!=="replay"){replay.stop();}
  }
  function route(){
    var h=(location.hash||"").replace(/^#/,"");
    var parts=h.split("/");
    var id=parts[0];
    if(id==="replay"&&parts.length>1){
      replay.go(parseInt(parts[1],10)||0,parseInt(parts[2],10)||0,false);
    }
    show(ids.indexOf(id)>=0?id:(ids[0]||""));
  }
  function nav(id){if(history.replaceState){history.replaceState(null,"","#"+id);}show(id);}
  document.addEventListener("click",function(e){
    var a=e.target.closest("a[data-view]");
    if(a){e.preventDefault();nav(a.getAttribute("data-view"));}
    var r=e.target.closest("[data-replay]");
    if(r){e.preventDefault();var p=(r.getAttribute("data-replay")||"0").split(":");
      replay.go(parseInt(p[0],10)||0,parseInt(p[1],10)||0,true);}
  });
  window.addEventListener("hashchange",route);

  /* ---------------------------------------------------------------- sidebar */
  var app=$(".app"),toggle=$(".side-toggle");
  if(app&&toggle){
    if(store.get("uxprobe-side")==="collapsed"){app.classList.add("collapsed");}
    toggle.addEventListener("click",function(){
      var c=app.classList.toggle("collapsed");
      toggle.setAttribute("title",c?"Expand sidebar":"Collapse sidebar");
      store.set("uxprobe-side",c?"collapsed":"open");
    });
  }

  /* ---------------------------------------------------------------- modals */
  function openModal(m){m.classList.add("open");m.setAttribute("aria-hidden","false");document.body.style.overflow="hidden";}
  function closeModal(m){m.classList.remove("open");m.setAttribute("aria-hidden","true");document.body.style.overflow="";}
  function anyOpen(){return !!$(".modal.open, .lb.open");}
  var logm=$("#logmodal");
  if(logm){
    var lbody=$(".modal-body",logm),ltitle=$(".modal-head .t",logm);
    document.addEventListener("click",function(e){
      var b=e.target.closest("[data-log]");if(!b){return;}
      var src=document.getElementById(b.getAttribute("data-log"));if(!src){return;}
      lbody.innerHTML=src.innerHTML;ltitle.textContent=src.getAttribute("data-title")||"Session log";
      openModal(logm);lbody.scrollTop=0;
    });
    logm.addEventListener("click",function(e){if(e.target===logm){closeModal(logm);lbody.innerHTML="";}});
    $(".modal-close",logm).addEventListener("click",function(){closeModal(logm);lbody.innerHTML="";});
  }
  var help=$("#help");
  if(help){
    $$("[data-help]").forEach(function(b){b.addEventListener("click",function(){openModal(help);});});
    help.addEventListener("click",function(e){if(e.target===help){closeModal(help);}});
    $(".modal-close",help).addEventListener("click",function(){closeModal(help);});
  }
  function closeAll(){
    $$(".modal.open").forEach(closeModal);
    var lb=$(".lb.open");if(lb){closeModal(lb);}
    $$("details.menu[open]").forEach(function(d){d.removeAttribute("open");});
  }
  document.addEventListener("click",function(e){
    $$("details.menu[open]").forEach(function(d){if(!d.contains(e.target)){d.removeAttribute("open");}});
  });

  /* ---------------------------------------------------------------- copy ticket */
  document.addEventListener("click",function(e){
    var b=e.target.closest("[data-ticket]");if(!b){return;}
    var text=b.getAttribute("data-ticket")||"";
    function done(){toast("Ticket copied as Markdown");}
    if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(text).then(done,function(){fallback();});}
    else{fallback();}
    function fallback(){var ta=document.createElement("textarea");ta.value=text;ta.style.position="fixed";ta.style.opacity="0";
      document.body.appendChild(ta);ta.select();try{document.execCommand("copy");done();}catch(err){}document.body.removeChild(ta);}
  });

  /* ---------------------------------------------------------------- issues: filter, search, sort */
  var q=$("#q"),cards=$$("#v-issues .f"),fbar=$(".fbar"),countEl=$(".fbar .count"),sortSel=$("#sort");
  var filters={sev:{},grade:{},persona:{},band:{}};
  function active(kind){return Object.keys(filters[kind]).filter(function(k){return filters[kind][k];});}
  function applyFilters(){
    var term=(q?q.value:"").trim().toLowerCase();
    var sev=active("sev"),grade=active("grade"),per=active("persona"),band=active("band");
    var shown=0;
    cards.forEach(function(c){
      var ok=true;
      if(sev.length&&sev.indexOf(c.getAttribute("data-sev"))<0){ok=false;}
      if(ok&&grade.length&&grade.indexOf(c.getAttribute("data-grade"))<0){ok=false;}
      if(ok&&band.length&&band.indexOf(c.getAttribute("data-band"))<0){ok=false;}
      if(ok&&per.length){var ps=(c.getAttribute("data-personas")||"").split(" ");
        ok=per.some(function(p){return ps.indexOf(p)>=0;});}
      if(ok&&term){ok=(c.getAttribute("data-text")||"").indexOf(term)>=0;}
      c.classList.toggle("hide",!ok);if(ok){shown++;}
    });
    $$("#v-issues .band").forEach(function(b){
      var vis=false,n=b.nextElementSibling;
      while(n&&!n.classList.contains("band")){if(n.classList.contains("f")&&!n.classList.contains("hide")){vis=true;break;}n=n.nextElementSibling;}
      b.classList.toggle("hide",!vis);
    });
    if(countEl){countEl.innerHTML="<b>"+shown+"</b> of "+cards.length;}
    var anyF=sev.length||grade.length||per.length||band.length||term;
    if(fbar){fbar.classList.toggle("filtered",!!anyF);}
    var clr=$(".fbar .clear");if(clr){clr.style.display=anyF?"":"none";}
  }
  if(fbar){
    fbar.addEventListener("click",function(e){
      var b=e.target.closest(".chipb[data-filter]");
      if(b){var k=b.getAttribute("data-filter"),v=b.getAttribute("data-value");
        filters[k][v]=!filters[k][v];b.classList.toggle("on",!!filters[k][v]);applyFilters();return;}
      if(e.target.closest(".clear")){filters={sev:{},grade:{},persona:{},band:{}};
        $$(".chipb.on",fbar).forEach(function(x){x.classList.remove("on");});if(q){q.value="";}applyFilters();}
    });
  }
  if(q){
    q.addEventListener("input",function(){if(current!=="issues"&&q.value.trim()){nav("issues");}applyFilters();});
    q.addEventListener("keydown",function(e){if(e.key==="Escape"){q.value="";applyFilters();q.blur();}});
  }
  function sortCards(){
    if(!sortSel){return;}
    var mode=sortSel.value;
    var bands=$$("#v-issues .band");
    bands.forEach(function(b){
      var items=[],n=b.nextElementSibling;
      while(n&&!n.classList.contains("band")){if(n.classList.contains("f")){items.push(n);}n=n.nextElementSibling;}
      var key=function(c){
        if(mode==="reach"){return -parseFloat(c.getAttribute("data-reach")||0);}
        if(mode==="severity"){return ["blocker","major","minor","nitpick"].indexOf(c.getAttribute("data-sev"));}
        return -parseFloat(c.getAttribute("data-impact")||0);
      };
      items.sort(function(a,b2){var d=key(a)-key(b2);return d||(parseInt(a.getAttribute("data-rank"),10)-parseInt(b2.getAttribute("data-rank"),10));});
      var anchor=items.length?items[items.length-1].nextElementSibling:null;
      items.forEach(function(it){it.parentNode.insertBefore(it,anchor);});
    });
  }
  if(sortSel){sortSel.addEventListener("change",sortCards);}
  applyFilters();

  /* ---------------------------------------------------------------- tooltip (journey map) */
  var tip=$("#tip");
  function tipShow(html,x,y){if(!tip){return;}tip.innerHTML=html;tip.classList.add("show");tipMove(x,y);}
  function tipMove(x,y){if(!tip){return;}var w=tip.offsetWidth,h=tip.offsetHeight;
    var left=Math.min(x+14,window.innerWidth-w-12),top=y+16;if(top+h>window.innerHeight-8){top=y-h-12;}
    tip.style.left=left+"px";tip.style.top=top+"px";}
  function tipHide(){if(tip){tip.classList.remove("show");}}
  function esc(s){return String(s==null?"":s).replace(/[&<>"]/g,function(c){return {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c];});}
  function stepTip(s,i){
    var ses=DATA.sessions[s],st=ses&&ses.steps[i];if(!st){return "";}
    var fr=["smooth","a snag","real friction","stuck"][st.friction||0];
    return '<div class="t"><span class="num">'+esc(ses.first)+' &middot; step '+st.n+'</span>'+esc(fr)+(st.feeling?' &middot; '+esc(st.feeling):'')+'</div>'
      +'<div class="s">'+esc(st.intent||st.action||"")+'</div>'
      +(st.thought?'<div class="q">'+esc(st.thought.length>160?st.thought.slice(0,157)+"…":st.thought)+'</div>':'')
      +'<div class="s" style="margin-top:6px;color:var(--faint)">click to open in replay</div>';
  }
  document.addEventListener("mouseover",function(e){
    var c=e.target.closest(".jm-cell");if(!c){return;}
    tipShow(stepTip(+c.getAttribute("data-s"),+c.getAttribute("data-i")),e.clientX,e.clientY);
  });
  document.addEventListener("mousemove",function(e){if(tip&&tip.classList.contains("show")){tipMove(e.clientX,e.clientY);}});
  document.addEventListener("mouseout",function(e){if(e.target.closest&&e.target.closest(".jm-cell")){tipHide();}});
  document.addEventListener("click",function(e){
    var c=e.target.closest(".jm-cell");if(!c){return;}
    tipHide();replay.go(+c.getAttribute("data-s"),+c.getAttribute("data-i"),true);
  });

  /* ---------------------------------------------------------------- friction landscape */
  var land=(function(){
    var yaw=-32;
    function setYaw(stage,v){yaw=Math.max(-85,Math.min(25,v));stage.style.setProperty("--yaw",yaw+"deg");}
    function settle(l){
      var stage=$(".stage",l);if(!stage||l.dataset.settled){return;}l.dataset.settled="1";
      if(reduced){setYaw(stage,-32);return;}
      var from=-62,to=-32,t0=null,dur=1500;
      function step(ts){if(!t0){t0=ts;}var p=Math.min(1,(ts-t0)/dur);var e=1-Math.pow(1-p,3);
        if(l.dataset.drag){return;}setYaw(stage,from+(to-from)*e);if(p<1){requestAnimationFrame(step);}}
      requestAnimationFrame(step);
    }
    $$(".land").forEach(function(l){
      var stage=$(".stage",l);if(!stage){return;}
      var down=null,moved=false;
      l.addEventListener("pointerdown",function(e){if(e.button!==0){return;}down={x:e.clientX,y:yaw,bar:e.target.closest(".bar")};moved=false;l.setPointerCapture(e.pointerId);});
      l.addEventListener("pointermove",function(e){
        if(down){var dx=e.clientX-down.x;if(Math.abs(dx)>3){moved=true;l.dataset.drag="1";tipHide();}setYaw(stage,down.y+dx*0.35);return;}
        var b=e.target.closest(".bar");
        if(b){tipShow(stepTip(+b.getAttribute("data-s"),+b.getAttribute("data-i")),e.clientX,e.clientY);}else{tipHide();}
      });
      function up(e){if(!down){return;}var b=down.bar;down=null;
        if(!moved&&b){tipHide();replay.go(+b.getAttribute("data-s"),+b.getAttribute("data-i"),true);}
        moved=false;}
      l.addEventListener("pointerup",up);l.addEventListener("pointercancel",function(){down=null;});
      l.addEventListener("pointerleave",function(){tipHide();});
    });
    $$(".jpanel .seg button").forEach(function(b){b.addEventListener("click",function(){
      var panel=b.closest(".jpanel"),mode=b.getAttribute("data-mode");
      panel.setAttribute("data-mode",mode);$$(".seg button",panel).forEach(function(x){x.classList.toggle("on",x===b);});
      store.set("uxprobe-journey",mode);
      if(mode==="map"){$$(".jm-strip",panel).forEach(function(d){d.classList.add("in");});}
      else{$$(".land",panel).forEach(function(l){l.classList.add("in");settle(l);});}
    });});
    var pref=store.get("uxprobe-journey");
    if(pref==="map"){$$(".jpanel").forEach(function(p){p.setAttribute("data-mode","map");
      $$(".seg button",p).forEach(function(x){x.classList.toggle("on",x.getAttribute("data-mode")==="map");});});}
    return {settle:settle};
  })();

  /* ---------------------------------------------------------------- replay */
  var replay=(function(){
    var root=$("#replay-app");
    var st={s:0,i:0,playing:false,timer:null,built:-1};
    var STEP_MS=2800;
    if(!root){return {go:function(){},stop:function(){},next:function(){},prev:function(){},toggle:function(){},active:function(){return false;}};}
    var stage=$(".rp-shot",root),url=$(".rp-chrome .url",root),dev=$(".rp-chrome .dev",root),
        cap=$(".rp-cap .act",root),fric=$(".rp-cap .fric",root),side=$(".rp-side",root),
        tl=$(".rp-tl",root),axis=$(".rp-axis",root),pos=$(".rp-ctl .pos",root),playBtn=$(".rp-ctl .play-btn",root),
        tabs=$(".rp-tabs"),logBtn=$(".rp-ctl [data-log]",root),openBtn=$(".rp-ctl .open-shot",root);
    function ses(){return DATA.sessions[st.s];}
    function buildTabs(){
      if(!tabs){return;}
      $$(".rp-tab",tabs).forEach(function(t,idx){t.classList.toggle("on",idx===st.s);});
    }
    function buildTimeline(){
      var s=ses();if(!s){return;}
      tl.innerHTML=s.steps.map(function(x,i){
        return '<button class="rp-seg fr'+(x.friction||0)+(x.shot?' shot':'')+'" data-i="'+i+'" title="Step '+x.n+'" aria-label="Step '+x.n+'"></button>';
      }).join("");
      var n=s.steps.length,ticks="";
      var every=n>30?10:(n>12?5:1);
      for(var i=0;i<n;i++){var c=((i+0.5)/n*100).toFixed(3);
        if(i===0||(i+1)%every===0||i===n-1){ticks+='<i style="left:'+c+'%"></i><b style="left:'+c+'%">'+(i+1)+'</b>';}}
      axis.innerHTML=ticks;
      st.built=st.s;
    }
    var VF='<span class="vf tl"></span><span class="vf tr"></span><span class="vf bl"></span><span class="vf br"></span>';
    function noshot(){var t=$("#ic-noshot");return t?t.innerHTML:"";}
    function render(){
      var s=ses();
      if(!s){return;}
      if(st.built!==st.s){buildTimeline();buildTabs();}
      if(!s.steps.length){
        stage.classList.remove("phone");
        stage.innerHTML=VF+'<div class="none">'+noshot()+'<b>No steps recorded</b>This session produced no step log'+(s.error?': '+esc(s.error)+'.':'.')+' Open the session log for what the agent said.</div>';
        cap.textContent="";fric.innerHTML="";side.innerHTML='<div class="rp-card"><div class="lbl">Session</div><div class="intent">'+esc(s.name)+'</div><div class="rp-kv"><div><div class="lbl">Outcome</div>'+esc(s.outcome||"unknown")+'</div><div><div class="lbl">Agent</div>'+esc(s.agent||"")+'</div></div></div>';
        pos.innerHTML="<b>0</b> / 0";url.textContent="";dev.textContent=s.device||"";
        if(openBtn){openBtn.style.display="none";}
        if(logBtn){logBtn.setAttribute("data-log",s.log);}
        return;
      }
      st.i=Math.max(0,Math.min(s.steps.length-1,st.i));
      var x=s.steps[st.i];
      var src=x.shot?(s.dir+"/"+x.shot):"";
      var feel=x.feeling?'<span class="feel">'+esc(x.feeling)+'</span>':'';
      stage.classList.toggle("phone",/phone|tablet/i.test(s.device||""));
      if(src){
        stage.innerHTML=VF+'<img src="'+esc(src)+'" alt="'+esc(x.action||x.intent||"screenshot")+'"><span class="tag-n">'+esc(x.n)+' / '+s.steps.length+'</span>'+feel;
        url.textContent=x.shot;
        if(openBtn){openBtn.style.display="";openBtn.setAttribute("href",src);}
      }else{
        stage.innerHTML=VF+'<div class="none">'+noshot()+'<b>No screenshot for this step</b>'+esc(x.what||x.action||x.intent||"")+'</div><span class="tag-n">'+esc(x.n)+' / '+s.steps.length+'</span>'+feel;
        url.textContent="(no screenshot)";
        if(openBtn){openBtn.style.display="none";}
      }
      dev.textContent=s.device||"";
      cap.textContent=x.action||x.intent||"";
      var f=x.friction||0;
      fric.innerHTML=[1,2,3].map(function(k){return '<i class="'+(k<=f?'on'+f:'')+'"></i>';}).join("");
      fric.setAttribute("title","friction "+f+"/3");
      side.innerHTML=
        '<div class="rp-card"><div class="lbl">Step</div><div class="big">'+String(x.n).padStart(2,"0")+'<small> / '+s.steps.length+'</small></div>'
        +'<div class="lbl" style="margin-top:12px">Tried to</div><div class="intent">'+esc(x.intent||x.action||"—")+'</div>'
        +'<div class="rp-kv"><div><div class="lbl">Expected</div>'+esc(x.expected||"—")+'</div>'
        +'<div class="'+(f>=2?"bad":"")+'"><div class="lbl">Got</div>'+esc(x.what||"—")+'</div></div></div>'
        +'<div class="rp-thought">'+(x.thought?'<div class="q">'+esc(x.thought)+'</div>':'<div class="empty-q">No thinking-aloud note for this step.</div>')
        +'<div class="cite"><span class="ava">'+s.icon+'</span>'+esc(s.name)+(x.feeling?' <span class="badge" style="margin-left:auto">'+esc(x.feeling)+'</span>':'')+'</div></div>';
      $$(".rp-seg",tl).forEach(function(seg,i){seg.classList.toggle("on",i===st.i);seg.classList.toggle("done",i<st.i);});
      $$(".land .bar.on, .jm-cell.on").forEach(function(b){b.classList.remove("on");});
      $$('.land .bar[data-s="'+st.s+'"][data-i="'+st.i+'"], .jm-cell[data-s="'+st.s+'"][data-i="'+st.i+'"]').forEach(function(b){b.classList.add("on");});
      pos.innerHTML="<b>"+x.n+"</b> / "+s.steps.length;
      if(logBtn){logBtn.setAttribute("data-log",s.log);}
      var nx=s.steps[st.i+1];if(nx&&nx.shot){var im=new Image();im.src=s.dir+"/"+nx.shot;}
      if(current==="replay"&&history.replaceState){history.replaceState(null,"","#replay/"+st.s+"/"+st.i);}
    }
    function stop(){st.playing=false;clearTimeout(st.timer);if(playBtn){playBtn.classList.remove("playing");playBtn.setAttribute("aria-label","Play");}}
    function tick(){
      if(!st.playing){return;}
      var s=ses();if(!s||st.i>=s.steps.length-1){stop();return;}
      st.i++;render();st.timer=setTimeout(tick,STEP_MS);
    }
    function play(){
      var s=ses();if(!s||!s.steps.length){return;}
      if(st.i>=s.steps.length-1){st.i=0;render();}
      st.playing=true;if(playBtn){playBtn.classList.add("playing");playBtn.setAttribute("aria-label","Pause");}
      st.timer=setTimeout(tick,STEP_MS);
    }
    function go(s,i,navigate){
      stop();
      if(s<0||s>=DATA.sessions.length){s=0;}
      st.s=s;st.i=i||0;
      if(navigate){nav("replay");}
      render();
    }
    function toggle(){if(st.playing){stop();}else{play();}}
    function next(){stop();var s=ses();if(s&&st.i<s.steps.length-1){st.i++;render();}}
    function prev(){stop();if(st.i>0){st.i--;render();}}
    root.addEventListener("click",function(e){
      var seg=e.target.closest(".rp-seg");if(seg){stop();st.i=+seg.getAttribute("data-i");render();return;}
      if(e.target.closest(".play-btn")){toggle();return;}
      if(e.target.closest(".prev-btn")){prev();return;}
      if(e.target.closest(".next-btn")){next();return;}
      if(e.target.closest(".first-btn")){stop();st.i=0;render();return;}
      if(e.target.closest(".last-btn")){stop();var s=ses();if(s){st.i=s.steps.length-1;render();}return;}
    });
    if(tabs){tabs.addEventListener("click",function(e){var t=e.target.closest(".rp-tab");if(!t){return;}
      go(+t.getAttribute("data-s"),0,false);});}
    if(DATA.sessions.length){render();}
    return {go:go,stop:stop,next:next,prev:prev,toggle:toggle,
      home:function(){stop();st.i=0;render();},end:function(){stop();var s=ses();if(s){st.i=s.steps.length-1;render();}},
      active:function(){return current==="replay";}};
  })();

  /* ---------------------------------------------------------------- lightbox */
  var lb=$("#lb");
  var lbState={s:0,list:[],i:0};
  function lbRender(){
    var it=lbState.list[lbState.i];if(!it){return;}
    $(".lb-body",lb).innerHTML='<img src="'+esc(it.src)+'" alt="'+esc(it.caption)+'">'
      +'<button class="lb-nav prev" aria-label="Previous">'+$("#ic-left").innerHTML+'</button>'
      +'<button class="lb-nav next" aria-label="Next">'+$("#ic-right").innerHTML+'</button>';
    $(".lb-head .t",lb).textContent=it.who;
    $(".lb-head .pos",lb).textContent=(lbState.i+1)+" / "+lbState.list.length;
    $(".lb-foot",lb).innerHTML='<b>Step '+esc(it.n)+'.</b> '+esc(it.caption)+(it.thought?'<br><span style="opacity:.75;font-style:italic">'+esc(it.thought)+'</span>':'');
    var open=$(".lb-head .open-rp",lb);if(open){open.setAttribute("data-replay",lbState.s+":"+it.i);}
  }
  function lbOpen(s,i){
    var ses=DATA.sessions[s];if(!ses||!lb){return;}
    lbState.s=s;lbState.list=[];
    ses.steps.forEach(function(x,idx){if(x.shot){lbState.list.push({src:ses.dir+"/"+x.shot,caption:x.action||x.intent||"",n:x.n,i:idx,who:ses.name,thought:x.thought});}});
    lbState.i=Math.max(0,lbState.list.findIndex(function(x){return x.i===i;}));
    lbRender();openModal(lb);
  }
  function lbStep(d){if(!lbState.list.length){return;}lbState.i=(lbState.i+d+lbState.list.length)%lbState.list.length;lbRender();}
  if(lb){
    document.addEventListener("click",function(e){
      var b=e.target.closest("[data-shot]");if(!b){return;}
      var p=b.getAttribute("data-shot").split(":");lbOpen(+p[0],+p[1]);
    });
    lb.addEventListener("click",function(e){
      if(e.target.closest(".lb-nav.prev")){lbStep(-1);return;}
      if(e.target.closest(".lb-nav.next")){lbStep(1);return;}
      if(e.target.closest(".lb-close")){closeModal(lb);return;}
      if(e.target.closest(".open-rp")){closeModal(lb);return;}
      if(e.target===$(".lb-body",lb)){closeModal(lb);}
    });
  }

  /* ---------------------------------------------------------------- keyboard */
  document.addEventListener("keydown",function(e){
    var tag=(e.target.tagName||"").toLowerCase();
    var typing=tag==="input"||tag==="textarea"||tag==="select"||e.target.isContentEditable;
    if(e.key==="Escape"){closeAll();tipHide();return;}
    if(typing){return;}
    if(lb&&lb.classList.contains("open")){
      if(e.key==="ArrowLeft"){lbStep(-1);e.preventDefault();}
      if(e.key==="ArrowRight"){lbStep(1);e.preventDefault();}
      return;
    }
    if(anyOpen()){return;}
    if(e.key==="/"){if(q){e.preventDefault();q.focus();q.select();}return;}
    if(e.key==="?"){if(help){e.preventDefault();openModal(help);}return;}
    if(e.key==="t"&&!e.metaKey&&!e.ctrlKey){if(themeBtn){themeBtn.click();}return;}
    if(e.key==="["){if(toggle){toggle.click();}return;}
    var n=parseInt(e.key,10);
    if(n>=1&&n<=navs.length&&!e.metaKey&&!e.ctrlKey&&!e.altKey){nav(navs[n-1].getAttribute("data-view"));return;}
    if(replay.active()){
      if(e.key==="ArrowRight"||e.key==="j"){replay.next();e.preventDefault();}
      else if(e.key==="ArrowLeft"||e.key==="k"){replay.prev();e.preventDefault();}
      else if(e.key===" "){replay.toggle();e.preventDefault();}
      else if(e.key==="Home"){replay.home();e.preventDefault();}
      else if(e.key==="End"){replay.end();e.preventDefault();}
    }
  });

  route();
  // the browser scrolls to the view's own id after load; undo that so the hero is not under the top bar
  function top(){if(ids.indexOf((location.hash||"").replace(/^#/,"").split("/")[0])>=0){window.scrollTo(0,0);}}
  window.addEventListener("load",function(){top();setTimeout(top,0);});
})();
"""
