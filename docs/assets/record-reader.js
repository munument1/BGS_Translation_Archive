/* Presentation-only reading controls. The archived source text is untouched. */
(function(root){
  'use strict';
  const structured=/^\s*(?:【.*】|[-*•>]|\d+[.)]|[A-Z][.)]|\d{1,4}[-/.]\d|[A-Za-z가-힣 ]{1,20}:\s*$)/;
  function headingInfo(line){
    let match=line.trim().match(/^【([^】]+)】$/);
    if(match)return {title:match[1].trim(),kind:'primary'};
    match=line.trim().match(/^={2,}\s*(.+?)\s*={2,}$/);
    if(match&&/[A-Za-z0-9가-힣]/.test(match[1]))return {title:match[1].trim(),kind:'minor'};
    match=line.trim().match(/^(#{1,3})\s+(.+)$/);
    return match?{title:match[2].trim(),kind:match[1].length===1?'primary':'minor'}:null;
  }
  function joinLines(lines){
    return lines.reduce((out,line)=>{
      const next=line.trim();
      // A detached Korean particle at a fixed-width break belongs to the
      // preceding word; do not apply this rule at a sentence boundary.
      const continuation=/^(?:[을를은는이가와과도에]|으로|에서|에게|까지|부터)(?:\s|[,.!?])/.test(next)&&!/[.!?。！？]$/.test(out);
      return out+(continuation?'':' ')+next;
    },'').trim();
  }
  function reflowBlock(block){
    const lines=block.split('\n');
    if(lines.length<2)return block;
    if(lines.some(line=>headingInfo(line))){
      const chunks=[];let pending=[];
      for(const line of lines){
        if(headingInfo(line)){if(pending.length)chunks.push(reflowBlock(pending.join('\n')));chunks.push(line);pending=[];}
        else pending.push(line);
      }
      if(pending.length)chunks.push(reflowBlock(pending.join('\n')));
      return chunks.join('\n');
    }
    const lengths=lines.map(s=>s.trim().length);
    if(lines.some(line=>structured.test(line)||/\t| {3,}/.test(line))||Math.max(...lengths)<22||lengths.reduce((a,b)=>a+b,0)<70)return block;
    // Short verse and table-like rows remain intact, even in fitted mode.
    if(lines.filter(line=>line.trim().length<14).length>lines.length/3)return block;
    if(lines.some(line=>/^[\s|+_=\-.*\/\\]+$/.test(line)))return block;
    return joinLines(lines);
  }
  function reflow(text){return text.replace(/\r\n?/g,'\n').split(/(\n[ \t]*\n)/).map(part=>/^\n/.test(part)?part:reflowBlock(part)).join('');}
  function sectionize(text){
    const segments=[];const pattern=/^[ \t]*(?:【[^\r\n】]+】|={2,}[^\r\n]+?={2,}|#{1,3}[ \t]+[^\r\n]+)[ \t]*\r?(?=\n|$)/gm;let end=0,match,primarySeen=false;
    while((match=pattern.exec(text))){
      const info=headingInfo(match[0]);if(!info)continue;
      if(match.index>end)segments.push({type:'text',text:text.slice(end,match.index)});
      const level=info.kind==='minor'&&primarySeen?4:3;
      segments.push({type:'heading',text:match[0],title:info.title,level});end=pattern.lastIndex;
      if(info.kind==='primary')primarySeen=true;
    }
    if(end<text.length)segments.push({type:'text',text:text.slice(end)});
    return segments;
  }
  let raw='',preserve=false,sections=false,size=18,mode='fit',wide=false,outlineKey='';
  try{const p=JSON.parse(localStorage.getItem('archive-reader-v1')||'{}');if(p.mode==='original')mode=p.mode;if(p.size>=15&&p.size<=24)size=p.size;wide=p.wide===true;}catch(_){}
  const el=id=>document.getElementById(id);
  function save(){try{localStorage.setItem('archive-reader-v1',JSON.stringify({mode,size,wide}));}catch(_){}}
  function renderSections(text){
    const body=el('readerBody');const parts=sections?sectionize(text):[];
    const headings=parts.filter(p=>p.type==='heading');
    let contents=el('readerContents');
    if(!contents){
      contents=document.createElement('details');contents.id='readerContents';contents.className='reader-contents';contents.hidden=true;body.before(contents);
    }
    contents.hidden=headings.length<2;
    body.classList.toggle('is-sectioned',headings.length>0);
    if(!headings.length){body.textContent=text;contents.replaceChildren();outlineKey='';return;}
    const nodes=[];let index=0;
    for(const part of parts){
      if(part.type==='heading'){
        const heading=document.createElement('h'+part.level);heading.className='reader-section-heading';heading.id='reader-section-'+(++index);heading.tabIndex=-1;heading.textContent=part.text;nodes.push(heading);
      }else if(part.text.trim()){
        const paragraph=document.createElement('div');paragraph.className='reader-section-text';paragraph.textContent=part.text.replace(/^\n+|\n+$/g,'');nodes.push(paragraph);
      }
    }
    body.replaceChildren(...nodes);
    if(headings.length<2){contents.replaceChildren();return;}
    const signature=headings.map(p=>p.title).join('\n');
    if(signature!==outlineKey)contents.open=headings.length<=8;
    outlineKey=signature;
    const summary=document.createElement('summary');summary.textContent='문서 목차 · '+headings.length+'개 구획';
    const nav=document.createElement('nav');nav.setAttribute('aria-label','문서 소제목 목차');
    const list=document.createElement('ol');
    let parentRow=null,childList=null;
    headings.forEach((part,i)=>{
      const row=document.createElement('li');const button=document.createElement('button');button.type='button';button.textContent=part.title;button.setAttribute('aria-controls','reader-section-'+(i+1));
      button.addEventListener('click',()=>{const target=el('reader-section-'+(i+1));target.scrollIntoView({block:'start'});target.focus({preventScroll:true});});
      row.append(button);
      if(part.level>3&&parentRow){if(!childList){childList=document.createElement('ol');parentRow.append(childList);}childList.append(row);}
      else{list.append(row);parentRow=row;childList=null;}
    });
    nav.append(list);contents.replaceChildren(summary,nav);
  }
  function render(){
    if(!el('readerBody'))return;
    renderSections(mode==='original'||preserve?raw:reflow(raw));
    el('reader').style.setProperty('--reader-font-size',size+'px');
    el('reader').classList.toggle('reader-wide',wide);
    if(el('readerLineMode'))el('readerLineMode').value=mode;
    if(el('readerSize'))el('readerSize').textContent=size+'px';
    if(el('readerWider')){el('readerWider').setAttribute('aria-pressed',String(wide));el('readerWider').textContent=wide?'기본 폭':'넓게 보기';}
    if(el('readerFontDown'))el('readerFontDown').disabled=size<=15;
    if(el('readerFontUp'))el('readerFontUp').disabled=size>=24;
  }
  function setText(text,options){raw=String(text||'');preserve=Boolean(options&&options.preserve);sections=Boolean(options&&options.sections);render();}
  root.ArchiveReader={setText,reflow,sectionize};
  if(typeof module!=='undefined'&&module.exports)module.exports={reflow,sectionize};
  if(typeof document!=='undefined')document.addEventListener('DOMContentLoaded',()=>{
    if(!el('reader'))return;
    el('readerLineMode').addEventListener('change',e=>{mode=e.target.value;save();render();});
    el('readerFontDown').addEventListener('click',()=>{size=Math.max(15,size-1);save();render();});
    el('readerFontUp').addEventListener('click',()=>{size=Math.min(24,size+1);save();render();});
    el('readerWider').addEventListener('click',()=>{wide=!wide;save();render();});
    render();
  });
})(typeof window!=='undefined'?window:globalThis);
