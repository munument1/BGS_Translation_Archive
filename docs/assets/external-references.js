"use strict";
(async()=>{
  const root=document.getElementById("referenceGrid");
  const search=document.getElementById("referenceSearch");
  const count=document.getElementById("referenceCount");
  const error=document.getElementById("referenceError");
  const more=document.getElementById("referenceMore");
  const tabs=document.querySelectorAll("#referenceTabs [data-game]");
  const LABELS={
    battlespire:"배틀스파이어",redguard:"레드가드",shadowkey:"섀도키",
    eso:"엘더 스크롤 온라인",eso_journals:"ESO 일지·편지"
  };
  let all=[],game="all",visible=48,filtered=[];
  function card(x){
    const node=document.createElement("article");
    node.className="reference-card";
    const tag=document.createElement("span");tag.className="label";
    tag.textContent=LABELS[x.game] || x.game;
    const title=document.createElement("h3");
    title.textContent=x.title_ko||x.title_en;
    const english=document.createElement("div");english.className="original";
    english.textContent=x.title_ko?x.title_en:"영문 서적명 · 번역 검토 전";
    const desc=document.createElement("p");
    desc.textContent=x.source_description||"참고용 서적 제목 · 게임별 출처";
    const note=document.createElement("div");note.className="review-note";
    note.textContent=x.direct_link?
      "미번역 · 원문/번역 전문 미수록 · 개별 출처 링크":
      "미번역 · 원문/번역 전문 미수록 · 게임별 출처 링크";
    const link=document.createElement("a");
    link.target="_blank";link.rel="noopener noreferrer";
    const url=x.source_url;
    if(!url || !url.startsWith("https://www.imperial-library.info/"))throw Error("Invalid source URL");
    link.href=url;
    link.textContent=x.direct_link?"원문 서적 페이지 ↗":"게임별 원문 목록 ↗";
    node.append(tag,title,english,desc,note,link);
    return node;
  }
  function render(){
    const term=search.value.trim().toLocaleLowerCase();
    filtered=all.filter(x=>(game==="all"||x.game===game)&&
      (x.title_en+" "+(x.title_ko||"")+" "+(x.source_description||"")).toLocaleLowerCase().includes(term));
    count.textContent=filtered.length.toLocaleString("ko-KR")+"종의 서지 항목 (번역 전문 제외)";
    root.replaceChildren(...filtered.slice(0,visible).map(card));
    more.hidden=visible>=filtered.length;
    more.textContent="다음 "+Math.min(48,filtered.length-visible).toLocaleString("ko-KR")+"건 보기 ↓";
    tabs.forEach(b=>{
      const active=b.dataset.game===game;
      b.classList.toggle("is-active",active);
      b.setAttribute("aria-pressed",String(active));
      const amount=b.dataset.game==="all"?all.length:all.filter(x=>x.game===b.dataset.game).length;
      const label=b.textContent.replace(/\s*\(\d[\d,]*\)\s*$/,"").trim();
      b.textContent=label+" ("+amount.toLocaleString("ko-KR")+")";
    });
  }
  function setGame(id){game=id;visible=48;render();}
  search.addEventListener("input",()=>{visible=48;render();});
  tabs.forEach(b=>b.addEventListener("click",()=>setGame(b.dataset.game)));
  more.addEventListener("click",()=>{visible+=48;render();});
  try{
    let response=await fetch("./books/imperial_game_books_catalog.json");
    if(response.ok){
      const doc=await response.json();
      if(!Array.isArray(doc.entries)||doc.entries.length<70)throw Error("Unexpected bibliography length");
      all=doc.entries;
    } else {
      response=await fetch("./books/external_candidates.json");
      if(!response.ok)throw Error("Cannot load reference file");
      const previous=await response.json();
      all=previous.items.map(x=>({
        game:x.game,title_en:x.title_en,title_ko:x.title_ko||"",source_url:x.url,
        direct_link:true,source_description:x.summary_ko
      }));
      error.hidden=false;
      error.textContent="전체 서지 색인 생성 이전 자료를 표시합니다.";
    }
    render();
    const params=new URLSearchParams(location.search);
    if(params.has("game")&&params.get("game") in LABELS)setGame(params.get("game"));
  }catch(e){
    console.warn(e);count.textContent="목록을 읽지 못했습니다.";
    error.hidden=false;
    error.textContent="서적 색인을 불러오지 못했습니다. GitHub 저장소의 데이터 파일을 확인해 주세요.";
  }
})();