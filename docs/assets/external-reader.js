"use strict";
(() => {
  let books = new Map();
  let layer = null, ui = null, returnFocus = null, openUid = null;
  const labels = {battlespire:"배틀스파이어",redguard:"레드가드",shadowkey:"섀도키"};
  const coverage = {
    full:"한국어 번역 본문",
    fragment:"현재 확보된 원문에 대한 한국어 번역 · 일부 발췌",
    description_only:"한국어 도서 설명 · 서적 본문은 아직 없음"
  };
  const styling = [
    ".til-reader-layer[hidden]{display:none!important}",
    ".til-reader-layer{position:fixed;inset:0;z-index:900;display:flex;align-items:center;justify-content:center;background:rgba(0,0,0,.82);padding:18px}",
    ".til-reader-window{width:min(840px,100%);height:min(92vh,980px);background:var(--panel,#1a2022);color:var(--ink,#f1eada);border:1px solid var(--edge,#555);display:flex;flex-direction:column;box-shadow:0 24px 78px rgba(0,0,0,.45)}",
    ".til-reader-top{padding:14px 24px;border-bottom:1px solid var(--edge,#555);display:flex;align-items:center;justify-content:space-between;gap:18px}",
    ".til-reader-top span{color:var(--gold,#cdb280);font-size:12px;letter-spacing:.08em}",
    ".til-reader-close{width:40px;height:40px;font-size:23px;border:1px solid var(--edge,#555);background:transparent;color:inherit;cursor:pointer}",
    ".til-reader-scroll{flex:1;overflow:auto;padding:30px clamp(20px,5vw,65px) 65px;overscroll-behavior:contain}",
    ".til-reader-scroll h2{font-family:var(--display,serif);font-weight:600;font-size:clamp(28px,4vw,42px);line-height:1.35;margin:0 0 10px}",
    ".til-reader-eng{color:var(--muted,#aaa);font-size:13px;margin-bottom:18px}",
    ".til-reader-status{color:var(--gold,#cdb280);font-size:12px;border-bottom:1px solid var(--edge,#555);padding-bottom:25px;margin-bottom:28px}",
    ".til-reader-body{font-family:var(--display,serif);font-size:clamp(16px,2vw,18px);line-height:2.05;white-space:pre-wrap;overflow-wrap:anywhere;word-break:keep-all}",
    ".til-reader-source{margin-top:38px;display:block;color:var(--gold,#cdb280);font-size:13px}",
    ".til-book-button{border:1px solid var(--gold,#cdb280);color:var(--gold,#cdb280);background:transparent;padding:11px 17px;font-family:inherit;font-size:13px;cursor:pointer;align-self:flex-start;font-weight:700}",
    ".til-book-button:hover{background:var(--gold,#cdb280);color:var(--bg,#111719)}",
    "body.til-reader-open{overflow:hidden}",
    "@media(max-width:640px){.til-reader-layer{padding:0}.til-reader-window{height:100dvh;width:100%;border:none}.til-reader-scroll{padding-top:22px}}"
  ].join("\n");
  const add = (parent,tag,className,text) => {
    const element=document.createElement(tag);
    if(className)element.className=className;
    if(text!==undefined)element.textContent=text;
    parent.appendChild(element);
    return element;
  };
  const style=add(document.head,"style",null,styling);
  style.dataset.archiveReader="true";
  function build() {
    layer=add(document.body,"div","til-reader-layer");
    layer.hidden=true;
    const dialog=add(layer,"section","til-reader-window");
    dialog.setAttribute("role","dialog");
    dialog.setAttribute("aria-modal","true");
    dialog.setAttribute("aria-labelledby","tilReaderTitle");
    const top=add(dialog,"div","til-reader-top");
    const game=add(top,"span",null,"THE ELDER SCROLLS");
    const closeButton=add(top,"button","til-reader-close","×");
    closeButton.type="button";
    closeButton.setAttribute("aria-label","서적 닫기");
    const scroll=add(dialog,"div","til-reader-scroll");
    const title=add(scroll,"h2",null,"");
    title.id="tilReaderTitle";
    const english=add(scroll,"div","til-reader-eng","");
    const status=add(scroll,"div","til-reader-status","");
    const body=add(scroll,"article","til-reader-body","");
    body.setAttribute("aria-label","한국어 번역 내용");
    const source=add(scroll,"a","til-reader-source","원문 출처 보기 ↗");
    source.target="_blank";
    source.rel="noopener noreferrer";
    source.href="./imperial-library.html";
    closeButton.addEventListener("click",()=>close());
    layer.addEventListener("click",event=>{if(event.target===layer)close();});
    document.addEventListener("keydown",event=>{
      if(!layer.hidden && event.key==="Escape"){event.preventDefault();close();}
      if(!layer.hidden && event.key==="Tab"){
        // Keep keyboard focus inside the open reader.
        const focusable=[closeButton,source].filter(el=>el.offsetParent!==null);
        if(focusable.length && event.shiftKey && document.activeElement===focusable[0]){
          event.preventDefault();focusable[focusable.length-1].focus();
        }else if(focusable.length && !event.shiftKey && document.activeElement===focusable[focusable.length-1]){
          event.preventDefault();focusable[0].focus();
        }
      }
    });
    ui={game,closeButton,scroll,title,english,status,body,source};
  }
  function setBooks(entries){
    books=new Map((Array.isArray(entries)?entries:[]).filter(entry=>entry.uid&&entry.body_ko).map(entry=>[entry.uid,entry]));
  }
  function has(uid){return books.has(uid);}
  function get(uid){return books.get(uid)||null;}
  function open(uid,changeHistory=true){
    const book=books.get(uid);if(!book)return false;
    if(!layer)build();
    returnFocus=document.activeElement;
    openUid=uid;
    ui.game.textContent="THE ELDER SCROLLS · "+(labels[book.game]||book.game);
    ui.title.textContent=book.title_ko;
    ui.english.textContent=book.title_en;
    ui.status.textContent=coverage[book.coverage]||"한국어 번역";
    ui.body.textContent=book.body_ko;
    if(/^https:\/\/www\.imperial-library\.info\//.test(book.source_url)){
      ui.source.href=book.source_url;
      ui.source.hidden=false;
    }else ui.source.hidden=true;
    layer.hidden=false;
    document.body.classList.add("til-reader-open");
    ui.scroll.scrollTop=0;
    ui.closeButton.focus();
    if(changeHistory){
      const url=new URL(location.href);
      url.searchParams.set("book",uid);
      history.pushState({book:uid},"",url.pathname+url.search+url.hash);
    }
    return true;
  }
  function close(changeHistory=true){
    if(!layer || layer.hidden)return;
    layer.hidden=true;
    document.body.classList.remove("til-reader-open");
    openUid=null;
    if(changeHistory){
      const url=new URL(location.href);
      url.searchParams.delete("book");
      history.replaceState({},"",url.pathname+url.search+url.hash);
    }
    if(returnFocus?.isConnected)returnFocus.focus();
  }
  window.addEventListener("popstate",()=>{
    const uid=new URLSearchParams(location.search).get("book");
    if(uid&&has(uid))open(uid,false);else close(false);
  });
  window.TamrielExternalReader={setBooks,has,get,open,close};
})();
