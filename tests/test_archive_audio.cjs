'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const {embedUrl,volumeValue}=require('../docs/assets/archive-audio.js');
const data=JSON.parse(fs.readFileSync(path.join(__dirname,'../docs/assets/archive-audio-sources.json'),'utf8'));
for(const [game,config] of Object.entries(data.archives)){
 const html=fs.readFileSync(path.join(__dirname,'../docs',game,'index.html'),'utf8');
 const music=config.tracks.find(t=>t.kind==='BGM');
 const url=new URL(embedUrl(music.id));
 assert.equal(url.hostname,'www.youtube-nocookie.com');assert.equal(url.searchParams.get('autoplay'),'0');
 assert.equal(url.searchParams.get('playlist'),music.id);assert.equal(url.searchParams.get('loop'),'1');
 assert.ok(html.includes('data-video-id="'+music.id+'"'));
 assert.equal((html.match(/data-video-id=/g)||[]).length,1,'Only BGM uses a video player');
 assert.ok(html.includes('data-ambient-kind="'+(game==='fallout'?'campfire':'ship')+'"'));
 assert.ok(html.includes('data-ambient-volume'));assert.ok(html.includes('data-sound-stop'));
 assert.ok(!html.includes('<iframe'),'No media iframe before a user request');
}
assert.throws(()=>embedUrl('javascript:alert(1)'));
assert.equal(volumeValue('30'),.3);assert.equal(volumeValue(-20),0);assert.equal(volumeValue(200),1);assert.equal(volumeValue('bad'),0);
assert.ok(fs.statSync(path.join(__dirname,'../docs/assets/campfire-119594.mp3')).size>0);
console.log('PASS: native ASMR, separate manual BGM, volume bounds and existing local audio asset');
