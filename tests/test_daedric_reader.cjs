"use strict";
const assert=require("node:assert/strict");
const {tokenize,render}=require("../docs/assets/daedric-reader.js");

assert.deepEqual(tokenize("한글 [daedric]AYEM BD[/daedric] 끝"),[
  {text:"한글 ",daedric:false},
  {text:"AYEM BD",daedric:true},
  {text:" 끝",daedric:false},
]);
assert.deepEqual(tokenize("평범한 ABC"),[{text:"평범한 ABC",daedric:false}]);
assert.deepEqual(tokenize("[DAEDRIC]AB[/DAEDRIC]"),[{text:"AB",daedric:true}]);
const doc={
  createDocumentFragment(){return {children:[],appendChild(node){this.children.push(node);}};},
  createTextNode(text){return {kind:"text",text};},
  createElement(tag){return {kind:"element",tag,className:"",textContent:"",title:""};},
};
const el={ownerDocument:doc,replaceChildren(fragment){this.content=fragment.children;}};
render(el,"<img src=x onerror=evil()> [daedric]ABC[/daedric] 한국어");
assert.equal(el.content.length,3);
assert.equal(el.content[0].kind,"text");
assert.equal(el.content[0].text,"<img src=x onerror=evil()> ");
assert.equal(el.content[1].className,"reader-daedric");
assert.equal(el.content[1].textContent,"ABC");
assert.equal(el.content[2].text," 한국어");
console.log("Daedric reader safe tokenization tests: PASS");
