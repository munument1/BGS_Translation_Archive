'use strict';
const assert = require('node:assert/strict');
const {reflow,sectionize} = require('../docs/assets/record-reader.js');
const prose='기록 제목\n\n이 문장은 오래된 게임 화면에 맞춰 짧은 줄로 고정되어 있지만\n태블릿에서는 화면의 넓이에 맞춰 자연스럽게 이어져야 합니다.\n두 번째 문장도 같은 문단 안에서 계속 읽을 수 있어야 합니다.\n\n다음 문단은 분리합니다.';
const fitted=reflow(prose);
assert.ok(fitted.includes('있지만 태블릿에서는'));
assert.ok(fitted.includes('\n\n다음 문단'));
assert.equal(fitted.replace(/\s/g,''),prose.replace(/\s/g,''));
const list='- 첫 번째 목록은 화면이 넓어져도 새로운 항목과 합쳐지면 안 됩니다.\n- 두 번째 목록 역시 자기 줄에 유지해야 합니다.';
assert.equal(reflow(list),list);
const code='G\nR\nE\nN\nF\nI\nE\nH\nR\nS';
assert.equal(reflow(code),code);
const art='+-----------------------+\n| TERMINAL / ARCHIVE    |\n+-----------------------+';
assert.equal(reflow(art),art);
const section='【기록 1】\n'+prose.split('\n\n')[1];
assert.ok(reflow(section).startsWith('【기록 1】\n'));
assert.equal(reflow('첫 줄\r\n\r\n둘째 문단'),'첫 줄\n\n둘째 문단');
assert.equal(reflow(fitted),fitted);
console.log('PASS: reader reflow retains paragraphs, lists, codes, headings and every non-whitespace character');

const sourceSections='소개 문단\n\n【연구 노트 - 플라즈마 소총】\n첫 본문\n\n【연구 노트 - 미니건】\n둘째 본문';
const parts=sectionize(sourceSections);
assert.equal(parts.map(p=>p.text).join(''),sourceSections);
assert.deepEqual(parts.filter(p=>p.type==='heading').map(p=>p.title),['연구 노트 - 플라즈마 소총','연구 노트 - 미니건']);
assert.deepEqual(sectionize('보통 문장 안의 【강조】 표시는 소제목이 아닙니다.'),[{type:'text',text:'보통 문장 안의 【강조】 표시는 소제목이 아닙니다.'}]);
assert.equal(sectionize('【<img src=x onerror=alert(1)>】\n본문')[0].title,'<img src=x onerror=alert(1)>');
console.log('PASS: document headings use explicit source markers and preserve text order');

const nested=sectionize('【큰 제목】\r\n=== 작은 제목 ===\r\n본문\r\n\r\n【다음 제목】\r\n내용');
assert.deepEqual(nested.filter(p=>p.type==='heading').map(p=>[p.title,p.level]),[['큰 제목',3],['작은 제목',4],['다음 제목',3]]);
assert.ok(reflow('=== 소제목 ===\n'+prose.split('\n\n')[1]).startsWith('=== 소제목 ===\n'));

assert.deepEqual(sectionize('=== 첫 제목 ===\n본문\n=== 둘째 제목 ===\n본문').filter(p=>p.type==='heading').map(p=>p.level),[3,3]);
assert.equal(sectionize('==================')[0].type,'text');

const fs=require('node:fs');
const documents=JSON.parse(fs.readFileSync(require('node:path').join(__dirname,'../docs/fallout/catalog.json'),'utf8')).entries.filter(r=>r.type==='document');
for(const record of documents){
  const segments=sectionize(record.body_ko);
  assert.equal(segments.map(p=>p.text).join(''),record.body_ko,record.id);
}
console.log('PASS: section parsing preserves all '+documents.length+' archived documents');
