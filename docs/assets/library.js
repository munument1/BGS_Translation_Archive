"use strict";
(() => {
  const $ = id => document.getElementById(id);
  const GAME = {
    daggerfall: { ko:"대거폴",en:"DAGGERFALL",roman:"II" },
    morrowind: { ko:"모로윈드",en:"MORROWIND",roman:"III" },
    oblivion: { ko:"오블리비언",en:"OBLIVION",roman:"IV" },
    skyrim: { ko:"스카이림",en:"SKYRIM",roman:"V" },
    battlespire: {ko:"배틀스파이어",en:"BATTLESPIRE",roman:"BS"},
    redguard: {ko:"레드가드",en:"REDGUARD",roman:"RG"},
    shadowkey: {ko:"섀도키",en:"SHADOWKEY",roman:"SK"},
    eso: {ko:"ESO 일반 서적",en:"ONLINE",roman:"ONLINE"},
    eso_journals: {ko:"ESO 일지·쪽지·편지",en:"ONLINE JOURNALS",roman:"ONLINE"}
  };
  const INITIALS = ["전체","ㄱ","ㄴ","ㄷ","ㄹ","ㅁ","ㅂ","ㅅ","ㅇ","ㅈ","ㅊ","ㅋ","ㅌ","ㅍ","ㅎ","A–Z","#"];
  const CHOSEONG = "ㄱㄲㄴㄷㄸㄹㅁㅂㅃㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎ";
  const GROUPS = {
    "ㄱ":"ㄱㄲ", "ㄴ":"ㄴ", "ㄷ":"ㄷㄸ", "ㄹ":"ㄹ", "ㅁ":"ㅁ",
    "ㅂ":"ㅂㅃ","ㅅ":"ㅅㅆ","ㅇ":"ㅇ","ㅈ":"ㅈㅉ","ㅊ":"ㅊ",
    "ㅋ":"ㅋ","ㅌ":"ㅌ","ㅍ":"ㅍ","ㅎ":"ㅎ"
  };
  const state = { items:[], filtered:[], game:"all", term:"", initial:"전체", sort:"title",
    savedOnly:false, limit:36, selected:null, fulltext:false, fulltextMap:null,
    loading:false, readerSize:16, favorites:new Set(), lastFocus:null, requestToken:0 };
  const collator = new Intl.Collator("ko");
  let toastTimer=0, searchTimer=0;
  try {
    const saved=JSON.parse(localStorage.getItem("tamriel-library-saved-v1") || "[]");
    if (Array.isArray(saved)) state.favorites = new Set(saved.filter(v=>typeof v==="string"));
    const theme = localStorage.getItem("tamriel-library-theme");
    if (theme==="light" || theme==="dark") document.body.dataset.theme=theme;
  } catch { /* Browser privacy mode: search and reading still work. */ }

  function notify(text) {
    const el=$("toast"); el.textContent=text; el.classList.add("is-visible");
    clearTimeout(toastTimer); toastTimer=setTimeout(()=>el.classList.remove("is-visible"),2500);
  }
  function persistFavorites() {
    try { localStorage.setItem("tamriel-library-saved-v1",JSON.stringify([...state.favorites])); } catch {}
  }
  function setFavorite(uid, toggle=true) {
    if (toggle) {
      if (state.favorites.has(uid)) state.favorites.delete(uid);
      else state.favorites.add(uid);
      persistFavorites();
    }
    document.querySelectorAll(".book-mark").forEach(button => {
      if (button.dataset.uid !== uid) return;
      const saved=state.favorites.has(uid);
      button.textContent=saved?"★":"☆";
      button.classList.toggle("is-saved",saved);
      button.setAttribute("aria-label",saved?"내 서재에서 제거":"내 서재에 저장");
      button.setAttribute("aria-pressed",String(saved));
    });
    if (state.selected?.uid===uid) {
      $("readerFavorite").textContent=state.favorites.has(uid)?"★":"☆";
      $("readerFavorite").setAttribute("aria-label",state.favorites.has(uid)?"내 서재에서 제거":"내 서재에 저장");
    }
  }
  function initialChar(title) {
    const c=(title || "").trim().charAt(0);
    if (/[가-힣]/.test(c)) return CHOSEONG[Math.floor((c.charCodeAt(0)-44032)/588)] || "#";
    if (/[ㄱ-ㅎ]/.test(c)) return c;
    if (/[a-z]/i.test(c)) return "A–Z";
    return "#";
  }
  function matchesInitial(book) {
    if(state.initial==="전체") return true;
    const initial=initialChar(book.title);
    return state.initial==="A–Z"||state.initial==="#"?initial===state.initial:
      (GROUPS[state.initial] || state.initial).includes(initial);
  }
  function textSearch(book, terms) {
    if(!terms.length)return true;
    let content=[book.title,book.title_en,book.author,book.preview,book.record_id,book.plugin].join(" ").toLowerCase();
    if(state.fulltext && state.fulltextMap) content += " "+(state.fulltextMap.get(book.uid)||"").toLowerCase();
    return terms.every(term=>content.includes(term));
  }
  function filterData() {
    const terms=state.term.trim().toLocaleLowerCase().split(/\s+/).filter(Boolean);
    const filtered=state.items.filter(book => (state.game==="all" || book.game===state.game) &&
      (!state.savedOnly || state.favorites.has(book.uid)) && matchesInitial(book) &&
      textSearch(book,terms));
    if(state.sort==="lengthDesc") filtered.sort((a,b)=>b.length-a.length || collator.compare(a.title,b.title));
    else if(state.sort==="lengthAsc") filtered.sort((a,b)=>a.length-b.length || collator.compare(a.title,b.title));
    else if(state.sort==="game") filtered.sort((a,b)=>Object.keys(GAME).indexOf(a.game)-Object.keys(GAME).indexOf(b.game) || collator.compare(a.title,b.title));
    else filtered.sort((a,b)=>collator.compare(a.title,b.title)||collator.compare(a.game,b.game));
    state.filtered=filtered;
  }
  function makeCard(book) {
    const article=document.createElement("article");
    article.className="book-card";
    const top=document.createElement("div"); top.className="book-card-top";
    const category=document.createElement("span"); category.className="book-category";
    category.textContent="THE ELDER SCROLLS "+GAME[book.game].roman+" · "+GAME[book.game].ko+(book.content_language==="en"?" · 미번역":"");
    const favorite=document.createElement("button");favorite.type="button";
    favorite.className="book-mark";favorite.dataset.uid=book.uid;
    favorite.addEventListener("click",e=>{e.stopPropagation();setFavorite(book.uid);if(state.savedOnly)render();});
    top.append(category,favorite);
    const title=document.createElement("h3"); title.className="book-card-title";title.textContent=book.title;
    const excerpt=document.createElement("p");excerpt.className="book-excerpt";
    excerpt.textContent=book.preview || "서적 설명을 불러오는 중입니다.";
    const bottom=document.createElement("div");bottom.className="book-card-bottom";
    const origin=document.createElement("span");origin.textContent=book.author || book.record_id;
    const open=document.createElement("span");open.textContent="읽어보기 ↗";
    bottom.append(origin,open);
    const action=document.createElement("button");action.type="button";action.className="book-open";
    action.textContent=book.title+" 읽기";
    action.addEventListener("click",()=>openBook(book.uid,true));
    article.append(top,title,excerpt,bottom,action);
    setTimeout(()=>setFavorite(book.uid,false),0);
    return article;
  }
  function render() {
    filterData();
    $("resultsCount").innerHTML="<strong>"+state.filtered.length.toLocaleString("ko-KR")+"</strong>권의 서적";
    const grid=$("booksGrid");
    const visible=state.filtered.slice(0,state.limit);
    grid.replaceChildren(...visible.map(makeCard));
    $("loadMore").hidden=state.limit>=state.filtered.length;
    $("loadMore").textContent="서적 더 보기 ↓ ("+Math.min(36,state.filtered.length-state.limit).toLocaleString("ko-KR")+"권)";
    const empty=state.filtered.length===0; $("emptyState").hidden=!empty;
    if(empty) {
      const unavailable=state.game==="skyrim" && !state.items.some(x=>x.game==="skyrim");
      $("emptyTitle").textContent=unavailable?"스카이림 자료 준비 중":"검색 결과가 없습니다.";
      $("emptyDescription").textContent=unavailable?"한국어 STRINGS와 게임 원본 BOOK 레코드를 연계하는 작업이 필요합니다.":"다른 검색어나 첫 글자, 작품 필터를 선택해 보세요.";
    }
    document.querySelectorAll("[data-filter]").forEach(node=>{
      const active=node.dataset.filter===state.game;
      node.classList.toggle("is-active",active);
      node.setAttribute("aria-pressed",String(active));
    });
    document.querySelectorAll("[data-select-game]").forEach(node=>node.classList.toggle("is-selected",node.dataset.selectGame===state.game));
    document.querySelectorAll("[data-initial]").forEach(node=>{
      const active=node.dataset.initial===state.initial;
      node.classList.toggle("is-active",active);node.setAttribute("aria-pressed",String(active));
    });
    $("favoritesToggle").classList.toggle("is-active",state.savedOnly);
    $("favoritesToggle").setAttribute("aria-pressed",String(state.savedOnly));
  }
  function changeGame(value,scroll=false) {
    state.game=value;state.initial="전체";state.limit=36;
    render();
    if(scroll)$("library").scrollIntoView({behavior:"smooth",block:"start"});
  }
  function setupIndex() {
    $("initialFilters").replaceChildren(...INITIALS.map(label=>{
      const b=document.createElement("button");b.type="button";
      b.className="initial-button";b.dataset.initial=label;b.textContent=label;
      b.addEventListener("click",()=>{state.initial=label;state.limit=36;render();});
      return b;
    }));
  }
  function parseBook(md) {
    let body=md.replace(/\r\n?/g,"\n");
    body=body.replace(/^# [^\n]*\n\n/,"").replace(/^[^\n]*\n\n/,"");
    body=body.replace(/\n\n(?:\[출처\]\([^)]+\)|출처: [^\n]+)\s*$/,"");
    body=body.replace(/[ \t]+\n/g,"\n");
    return body.trim();
  }
  function changeUrl(uid=null) {
    try {
      const url=new URL(location.href);
      if(uid)url.searchParams.set("book",uid);else url.searchParams.delete("book");
      if(state.game!=="all") url.searchParams.set("game",state.game);
      else url.searchParams.delete("game");
      history.pushState({}, "", url.pathname + url.search + url.hash);
    } catch{}
  }
  async function openBook(uid,updateHistory=false) {
    const book=state.items.find(b=>b.uid===uid);
    if(!book){notify("해당 서적을 찾지 못했습니다.");return;}
    const token=++state.requestToken;
    state.lastFocus=document.activeElement;
    state.selected=book;
    $("readerLayer").hidden=false;
    document.body.classList.add("reader-open");
    $("readerTitle").textContent=book.title;
    $("readerGame").textContent="THE ELDER SCROLLS "+GAME[book.game].roman+" · "+GAME[book.game].en;
    $("readerMetadata").replaceChildren();
    [book.author, GAME[book.game].ko,book.content_language==="en"?"영문 · 미번역":null,book.record_id].filter(Boolean).forEach(value=>{
      const span=document.createElement("span");span.textContent=value;$("readerMetadata").append(span);
    });
    $("readerContent").textContent="서적을 펼치는 중…";
    $("readerContent").lang=book.content_language||"ko";
    $("readerScroller").scrollTop=0;
    $("readerContent").style.setProperty("--reader-size",state.readerSize+"px");
    const source=$("readerSource");
    const validSource=book.source?.startsWith("https://github.com/")||book.source?.startsWith("https://www.imperial-library.info/content/");
    source.hidden=!validSource;
    if(validSource)source.href=book.source;else source.removeAttribute("href");
    setFavorite(uid,false);
    if(updateHistory)changeUrl(uid);
    $("readerClose").focus();
    try{
      const url=new URL("books/"+book.path.split("/").map(encodeURIComponent).join("/"),location.href);
      const response=await fetch(url);
      if(!response.ok)throw Error("서적 원문을 읽지 못했습니다 ("+response.status+")");
      const markdown=await response.text();
      if(token!==state.requestToken)return;
      $("readerContent").textContent=parseBook(markdown);
    }catch(error){if(token===state.requestToken){$("readerContent").textContent="서적 본문을 불러올 수 없습니다. 잠시 후 다시 시도해 주세요.";console.warn(error);}}
    const current=state.filtered.findIndex(b=>b.uid===uid);
    $("readerPrevious").disabled=current<=0;
    $("readerNext").disabled=current<0 || current>=state.filtered.length-1;
  }
  function closeReader(updateHistory=true) {
    ++state.requestToken;
    $("readerLayer").hidden=true;document.body.classList.remove("reader-open");state.selected=null;
    if(updateHistory)changeUrl();
    if(state.lastFocus?.isConnected)state.lastFocus.focus();
  }
  function stepBook(offset) {
    if(!state.selected)return;
    const i=state.filtered.findIndex(x=>x.uid===state.selected.uid);
    if(i>=0 && state.filtered[i+offset])openBook(state.filtered[i+offset].uid,true);
  }
  async function requestFulltext() {
    if(state.fulltextMap)return;
    if(state.loading)return;
    state.loading=true;
    $("resultsDescription").textContent="본문 검색 인덱스 불러오는 중…";
    try {
      const res=await fetch("./books/fulltext-index.json");
      if(!res.ok)throw Error("fulltext-index unavailable");
      const list=await res.json();
      const extra=await fetch("./books/additional_fulltext-index.json");
      if(extra.ok)list.push(...await extra.json());
      state.fulltextMap=new Map(list.map(x=>[x.uid,x.text]));
      $("resultsDescription").textContent="본문 전체 검색 활성화";
      render();
    }catch(err){
      $("fullTextToggle").checked=false;state.fulltext=false;
      $("resultsDescription").textContent="제목 검색";
      notify("본문 색인을 읽을 수 없어 제목 검색만 사용합니다.");
      console.warn(err);
    }finally{state.loading=false;}
  }
  function bind() {
    document.querySelectorAll("[data-filter]").forEach(el=>el.addEventListener("click",()=>changeGame(el.dataset.filter)));
    document.querySelectorAll("[data-select-game]").forEach(el=>el.addEventListener("click",()=>changeGame(el.dataset.selectGame,true)));
    $("searchInput").addEventListener("input",e=>{
      clearTimeout(searchTimer);searchTimer=setTimeout(()=>{state.term=e.target.value;state.limit=36;render();},160);
    });
    $("sortSelect").addEventListener("change",e=>{state.sort=e.target.value;state.limit=36;render();});
    $("favoritesToggle").addEventListener("click",()=>{state.savedOnly=!state.savedOnly;state.limit=36;render();});
    $("resetFilters").addEventListener("click",()=>{state.game="all";state.term="";state.initial="전체";state.savedOnly=false;state.limit=36;$("searchInput").value="";render();});
    $("fullTextToggle").addEventListener("change",async e=>{
      state.fulltext=e.target.checked;
      if(state.fulltext)await requestFulltext();else {state.limit=36;render();}
    });
    $("loadMore").addEventListener("click",()=>{state.limit+=36;render();});
    ["readerClose","readerCloseIcon","readerBackdrop"].forEach(id=>$(id).addEventListener("click",()=>closeReader()));
    $("readerFontDown").addEventListener("click",()=>{state.readerSize=Math.max(12,state.readerSize-2);$("readerContent").style.setProperty("--reader-size",state.readerSize+"px");});
    $("readerFontUp").addEventListener("click",()=>{state.readerSize=Math.min(26,state.readerSize+2);$("readerContent").style.setProperty("--reader-size",state.readerSize+"px");});
    $("readerPrevious").addEventListener("click",()=>stepBook(-1));
    $("readerNext").addEventListener("click",()=>stepBook(1));
    $("readerFavorite").addEventListener("click",()=>state.selected && setFavorite(state.selected.uid));
    $("readerCopy").addEventListener("click",async()=>{
      try{await navigator.clipboard.writeText(location.href);notify("서적 링크를 복사했습니다.");}
      catch{notify("주소창의 링크를 복사해 주세요.");}
    });
    $("themeToggle").addEventListener("click",()=>{
      const target=document.body.dataset.theme==="dark"?"light":"dark";
      document.body.dataset.theme=target;
      $("themeToggle").setAttribute("aria-label",target==="dark"?"밝은 테마로 변경":"어두운 테마로 변경");
      try{localStorage.setItem("tamriel-library-theme",target);}catch{}
    });
    window.addEventListener("keydown",e=>{
      if(e.key==="Escape" && !$("readerLayer").hidden){e.preventDefault();closeReader();return;}
      if(e.key==="/" && $("readerLayer").hidden && !["INPUT","TEXTAREA"].includes(document.activeElement.tagName)){e.preventDefault();$("searchInput").focus();return;}
      if(!$("readerLayer").hidden && e.key==="Tab"){
        const targets=[...$("readerLayer").querySelectorAll("button:not([disabled]),a:not([hidden])")].filter(el=>el.offsetParent!==null);
        if(!targets.length)return;
        const first=targets[0],last=targets[targets.length-1];
        if(e.shiftKey&&document.activeElement===first){e.preventDefault();last.focus();}
        else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first.focus();}
      }
    });
    window.addEventListener("popstate",()=>{
      const params=new URLSearchParams(location.search);
      const uid=params.get("book");
      if(uid&&state.items.some(x=>x.uid===uid))openBook(uid,false);
      else if(!$("readerLayer").hidden)closeReader(false);
    });
  }
  async function boot() {
    setupIndex();bind();
    try {
      const response=await fetch("./books/catalog.json");
      if(!response.ok)throw Error("카탈로그 HTTP "+response.status);
      const data=await response.json();
      if(!Array.isArray(data.books))throw Error("Invalid catalog");
      const additional=await fetch("./books/additional_catalog.json");
      if(additional.ok){
        const extra=await additional.json();
        if(Array.isArray(extra.books))data.books.push(...extra.books);
        data.counts={...data.counts,...extra.counts};
      }
      state.items=data.books.filter(b=>GAME[b.game] && b.uid && b.path && b.title);
      const counts=data.counts||{};
      $("heroTotal").textContent=state.items.length.toLocaleString("ko-KR");
      $("heroGames").textContent=new Set(Object.entries(counts).filter(([,n])=>n>0).map(([g])=>g==="eso_journals"?"eso":g)).size.toString();
      Object.keys(GAME).forEach(game=>{
        const count=$("count-"+game);
        if(count)count.textContent=(counts[game]||0)>0?(counts[game]||0).toLocaleString("ko-KR")+"권":"준비 중";
      });
      const params=new URLSearchParams(location.search);
      const requestedGame=params.get("game");
      if(requestedGame&&GAME[requestedGame])state.game=requestedGame;
      render();
      const requestedBook=params.get("book");
      if(requestedBook)await openBook(requestedBook,false);
    } catch(error) {
      console.error(error);
      $("resultsCount").textContent="도서 목록을 불러오지 못했습니다.";
      $("emptyState").hidden=false;
      $("emptyTitle").textContent="도서 목록을 불러올 수 없습니다.";
      $("emptyDescription").textContent="GitHub Pages 설정과 docs/books/catalog.json 생성 여부를 확인해 주세요.";
    }
  }
  boot();
})();
