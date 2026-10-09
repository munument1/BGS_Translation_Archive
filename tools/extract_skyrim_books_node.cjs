#!/usr/bin/env node
"use strict";
/* Extract BOOK records by matching Skyrim ESM/ESL FULL/DESC IDs to localized
 * *_english.STRINGS / .DLSTRINGS. Source game files are READ ONLY.
 * JSONL parts are <=150 KiB for safe handoff; no proprietary plugin binaries
 * are ever written into the translation archive.
 */
const fs=require("node:fs"), path=require("node:path"), zlib=require("node:zlib");
const crypto=require("node:crypto");
const base=process.argv[2]||path.join(process.cwd(),"스카이림 번역파일");
const output=process.argv[3]||path.join(process.cwd(),"_skyrim_books_export");
const stringDir=path.join(base,"strings");
if(!fs.existsSync(stringDir))throw Error("Missing strings/ directory");
const allStrings=new Map(fs.readdirSync(stringDir).map(n=>[n.toLowerCase(),path.join(stringDir,n)]));
const plugins=fs.readdirSync(base).filter(n=>/\.(esm|esp|esl)$/i.test(n)).sort();
if(!plugins.length)throw Error("Missing ESM/ESL plugin files");
const td=new TextDecoder("utf-8",{fatal:true});
function decode(raw){try{return td.decode(raw)}catch{return new TextDecoder("windows-1252").decode(raw)}}
function unpackTable(file,isLength){
 const b=fs.readFileSync(file);
 if(b.length<8)throw Error("Truncated table "+file);
 const count=b.readUInt32LE(0), len=b.readUInt32LE(4),dataStart=8+count*8;
 if(count>500000||dataStart+len>b.length)throw Error("Invalid string table bounds "+file);
 const table=new Map();
 for(let i=0;i<count;i++){
  const id=b.readUInt32LE(8+i*8),p=dataStart+b.readUInt32LE(8+i*8+4);
  if(p<dataStart||p>=dataStart+len)throw Error("String offset out of bounds "+id);
  let raw;
  if(isLength){
   if(p+4>dataStart+len)throw Error("Short length prefix");
   const sz=b.readUInt32LE(p);
   if(sz>dataStart+len-p-4)throw Error("String overrun "+id);
   raw=b.subarray(p+4,p+4+sz);
   if(raw.length&&raw[raw.length-1]===0)raw=raw.subarray(0,raw.length-1);
  }else{
   const end=b.indexOf(0,p);
   if(end<0||end>=dataStart+len)throw Error("Unterminated string");
   raw=b.subarray(p,end);
  }
  table.set(id,decode(raw).replace(/\r\n?/g,"\n").trim());
 }
 return table;
}
function fields(b){
 const map=new Map();let p=0,extra=null;
 while(p+6<=b.length){
  const field=b.toString("ascii",p,p+4),sz=b.readUInt16LE(p+4);p+=6;
  if(field==="XXXX"){
   if(sz!==4||p+4>b.length)throw Error("Bad XXXX");
   extra=b.readUInt32LE(p);p+=4;continue;
  }
  const length=extra??sz;extra=null;
  if(p+length>b.length)throw Error("Broken subrecord");
  if(!map.has(field))map.set(field,b.subarray(p,p+length));
  p+=length;
 }
 if(p!==b.length)throw Error("Broken subrecord tail");
 return map;
}
function scanPlugin(plugin){
 const b=fs.readFileSync(plugin);
 let p=0,localized=false,hasTES4=false;
 const items=[];
 while(p+24<=b.length){
  const tag=b.toString("ascii",p,p+4),len=b.readUInt32LE(p+4);
  const flags=b.readUInt32LE(p+8),formId=b.readUInt32LE(p+12);
  if(tag==="GRUP"){
   if(len<24||p+len>b.length)throw Error("Bad group length "+p);
   p+=24;continue;
  }
  const end=p+24+len;
  if(end>b.length)throw Error("Bad record size "+p);
  if(tag==="TES4"){localized=Boolean(flags&0x80);hasTES4=true}
  if(tag==="BOOK"){
   let payload=b.subarray(p+24,end);
   if(flags&0x00040000){
    if(payload.length<4)throw Error("Broken compressed record");
    const want=payload.readUInt32LE(0);
    payload=zlib.inflateSync(payload.subarray(4));
    if(payload.length!==want)throw Error("Compressed size mismatch");
   }
   const field=fields(payload);
   const edid=field.has("EDID")?decode(field.get("EDID")).replace(/\0+$/,""):"";
   const get=(name)=> {
    const raw=field.get(name);
    if(!raw)return null;
    return localized&&raw.length===4?raw.readUInt32LE(0):decode(raw).replace(/\0+$/,"");
   };
   items.push({form_id:formId.toString(16).toUpperCase().padStart(8,"0"),editor_id:edid,
      title:get("FULL"),body:get("DESC")});
  }
  p=end;
 }
 if(!hasTES4||p!==b.length)throw Error("Invalid plugin file: "+path.basename(plugin));
 return {items,localized};
}
function chunks(books,outDir,max=150000){
 fs.mkdirSync(outDir,{recursive:true});
 let i=0,buf=[],size=0;
 const output=[];
 const flush=()=>{
  if(!buf.length)return;
  const name="skyrim_books_"+String(++i).padStart(3,"0")+".jsonl";
  fs.writeFileSync(path.join(outDir,name),buf.join(""),"utf8");
  output.push(name);buf=[];size=0;
 };
 for(const b of books){
  const line=JSON.stringify(b)+"\n";
  const bytes=Buffer.byteLength(line,"utf8");
  if(bytes>max)throw Error("Single BOOK row too big");
  if(size+bytes>max)flush();
  buf.push(line);size+=bytes;
 }
 flush();
 return output;
}
const all=[],audit={};
for(const fname of plugins){
 const stem=path.parse(fname).name.toLowerCase();
 const titlePath=allStrings.get(stem+"_english.strings");
 const bodyPath=allStrings.get(stem+"_english.dlstrings");
 if(!titlePath||!bodyPath){audit[fname]={status:"missing STRINGS",books:0};continue;}
 const titleTable=unpackTable(titlePath,false),bodyTable=unpackTable(bodyPath,true);
 const parsed=scanPlugin(path.join(base,fname));
 let valid=0,missing=0,untranslated=0;
 for(const b of parsed.items){
  const title=typeof b.title==="number"?titleTable.get(b.title)||b.editor_id||b.form_id:b.title||b.editor_id||b.form_id;
  const body=typeof b.body==="number"?bodyTable.get(b.body):b.body;
  if(!body){missing++;continue;}
  if(!/[가-힣]/.test(title+" "+body)){untranslated++;continue;}
  all.push({game:"skyrim",record:"BOOK",field:"DESC",plugin:fname,book_id:b.form_id,
   form_id:b.form_id,editor_id:b.editor_id,title_ko:title,ko:body,
   source_language:"en",content_language:"ko",status:"imported",
   source_ref:"local:"+fname+"+strings/"+path.basename(bodyPath)});
  valid++;
 }
 audit[fname]={status:"processed",books:parsed.items.length,valid,missing,untranslated,localized:parsed.localized};
}
if(!all.length)throw Error("No Korean books extracted: "+JSON.stringify(audit));
all.sort((a,b)=>a.plugin.localeCompare(b.plugin)||a.title_ko.localeCompare(b.title_ko,"ko")||a.book_id.localeCompare(b.book_id));
const files=chunks(all,output);
const summary={total:all.length,files,breakdown:audit};
fs.writeFileSync(path.join(output,"manifest.json"),JSON.stringify(summary,null,2),"utf8");
process.stdout.write(JSON.stringify(summary,null,2)+"\n");
