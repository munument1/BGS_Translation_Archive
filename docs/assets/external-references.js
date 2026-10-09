"use strict";
(async()=>{
const root=document.getElementById("referenceGrid"),search=document.getElementById("referenceSearch"),count=document.getElementById("referenceCount"),error=document.getElementById("referenceError");
try {
const response=await fetch("./books/external_candidates.json");if(!response.ok)throw Error("reference HTTP "+response.status);
const data=await response.json();if(!Array.isArray(data.items))throw Error("Invalid references");
function render(){
const term=search.value.trim().toLocaleLowerCase();
const rows=data.items.filter(x=>[x.title_ko,x.title_en,x.category,x.summary_ko].join(" ").toLocaleLowerCase().includes(term));
count.textContent=rows.length+"종의 외부 서적 출처";
root.replaceChildren(...rows.map(x=>{
const card=document.createElement("article");card.className="reference-card";
const label=document.createElement("span");label.className="label";label.textContent="ELDER SCROLLS ONLINE · "+x.category;
const title=document.createElement("h3");title.textContent=x.title_ko;
const en=document.createElement("div");en.className="original";en.textContent=x.title_en;
const text=document.createElement("p");text.textContent=x.summary_ko;
const link=document.createElement("a");link.textContent="원문 사이트에서 읽기 ↗";link.target="_blank";link.rel="noopener noreferrer";
if(!x.url.startsWith("https://www.imperial-library.info/content/"))throw Error("Unapproved reference URL");
link.href=x.url;
card.append(label,title,en,text,link);return card;
}));
}
search.addEventListener("input",render);
render();
}catch(e){console.warn(e);count.textContent="목록을 불러오지 못했습니다.";error.hidden=false;}
})();