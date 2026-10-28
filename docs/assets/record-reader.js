/* Presentation-only reading controls. The archived source text is untouched. */
(function(root){
  'use strict';
  const structured=/^\s*(?:【.*】|[-*•>]|\d+[.)]|[A-Z][.)]|\d{1,4}[-/.]\d|[A-Za-z가-힣 ]{1,20}:\s*$)/;
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
    if(lines.some(line=>/^【.*】\s*$/.test(line))){
      const chunks=[];let pending=[];
      for(const line of lines){
        if(/^【.*】\s*$/.test(line)){if(pending.length)chunks.push(reflowBlock(pending.join('\n')));chunks.push(line);pending=[];}
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
  let raw='',preserve=false,size=18,mode='fit',wide=false;
  try{const p=JSON.parse(localStorage.getItem('archive-reader-v1')||'{}');if(p.mode==='original')mode=p.mode;if(p.size>=15&&p.size<=24)size=p.size;wide=p.wide===true;}catch(_){}
  const el=id=>document.getElementById(id);
  function save(){try{localStorage.setItem('archive-reader-v1',JSON.stringify({mode,size,wide}));}catch(_){}}
  function render(){
    if(!el('readerBody'))return;
    el('readerBody').textContent=mode==='original'||preserve?raw:reflow(raw);
    el('reader').style.setProperty('--reader-font-size',size+'px');
    el('reader').classList.toggle('reader-wide',wide);
    if(el('readerLineMode'))el('readerLineMode').value=mode;
    if(el('readerSize'))el('readerSize').textContent=size+'px';
    if(el('readerWider')){el('readerWider').setAttribute('aria-pressed',String(wide));el('readerWider').textContent=wide?'기본 폭':'넓게 보기';}
    if(el('readerFontDown'))el('readerFontDown').disabled=size<=15;
    if(el('readerFontUp'))el('readerFontUp').disabled=size>=24;
  }
  function setText(text,options){raw=String(text||'');preserve=Boolean(options&&options.preserve);render();}
  root.ArchiveReader={setText,reflow};
  if(typeof module!=='undefined'&&module.exports)module.exports={reflow};
  if(typeof document!=='undefined')document.addEventListener('DOMContentLoaded',()=>{
    if(!el('reader'))return;
    el('readerLineMode').addEventListener('change',e=>{mode=e.target.value;save();render();});
    el('readerFontDown').addEventListener('click',()=>{size=Math.max(15,size-1);save();render();});
    el('readerFontUp').addEventListener('click',()=>{size=Math.min(24,size+1);save();render();});
    el('readerWider').addEventListener('click',()=>{wide=!wide;save();render();});
    render();
  });
})(typeof window!=='undefined'?window:globalThis);
