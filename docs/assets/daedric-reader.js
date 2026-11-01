/* Tamriel Library: safe rendering of opt-in [daedric]...[/daedric] text. */
(function(root) {
  "use strict";
  const marker=/(\[\/?daedric\])/gi;
  function tokenize(value) {
    let active=false;
    const result=[];
    for (const part of String(value).split(marker)) {
      if (/^\[daedric\]$/i.test(part)) {active=true;continue;}
      if (/^\[\/daedric\]$/i.test(part)) {active=false;continue;}
      if (part) result.push({text:part,daedric:active});
    }
    return result;
  }
  function render(element,value) {
    const doc=element.ownerDocument;
    const fragment=doc.createDocumentFragment();
    for (const token of tokenize(value)) {
      if (token.daedric) {
        const span=doc.createElement("span");
        span.className="reader-daedric";
        span.textContent=token.text;
        span.title="데이드릭 문자의 라틴 전사: "+token.text;
        fragment.appendChild(span);
      } else {
        fragment.appendChild(doc.createTextNode(token.text));
      }
    }
    element.replaceChildren(fragment);
  }
  root.TamrielDaedric={tokenize,render};
  if (typeof module!=="undefined" && module.exports) module.exports={tokenize,render};
})(typeof window!=="undefined"?window:globalThis);
