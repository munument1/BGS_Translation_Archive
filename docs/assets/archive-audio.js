/* Native ambient sound and user-initiated YouTube background music. */
(function(root){
  'use strict';
  function embedUrl(id){
    if(!/^[A-Za-z0-9_-]{11}$/.test(id))throw Error('Invalid YouTube video ID');
    const url=new URL('https://www.youtube-nocookie.com/embed/'+id);
    url.search=new URLSearchParams({playsinline:'1',autoplay:'0',loop:'1',playlist:id,rel:'0'}).toString();return url.href;
  }
  function volumeValue(value){const n=Number(value);return Number.isFinite(n)?Math.min(1,Math.max(0,n/100)):0;}
  if(typeof module!=='undefined'&&module.exports)module.exports={embedUrl,volumeValue};
  if(typeof document==='undefined')return;
  const assets=new URL('.',document.currentScript.src);
  const ambientFiles={ruins:'ruins-industrial-482892.mp3',ship:'spaceship-ambient-27988.mp3'};
  document.addEventListener('DOMContentLoaded',()=>{
    document.querySelectorAll('[data-sound-open]').forEach(link=>link.addEventListener('click',()=>{const deck=document.getElementById('soundscape');if(deck)deck.open=true;}));
    document.querySelectorAll('.sound-deck').forEach(deck=>{
      const stop=deck.querySelector('[data-sound-stop]');const status=deck.querySelector('[data-sound-status]');const ambient=[];
      function update(){const count=deck.querySelectorAll('iframe').length;const on=ambient.some(a=>a.playing);stop.disabled=!on&&count===0;status.textContent=on?'환경음 켜짐 · BGM도 별도로 재생할 수 있습니다.':count?'BGM 플레이어 열림 · 영상의 재생 버튼을 눌러 들으세요.':'환경음은 켜기 버튼으로, BGM은 YouTube에서 재생합니다.';}
      function resetVideo(card){
        const button=document.createElement('button');button.type='button';button.className='sound-load';button.dataset.soundLoad='';const icon=document.createElement('span');icon.textContent='▷';icon.setAttribute('aria-hidden','true');const label=document.createElement('span');label.textContent='BGM 플레이어 열기';button.append(icon,label);card.querySelector('.sound-player').replaceChildren(button);
      }
      deck.querySelectorAll('[data-ambient-kind]').forEach(card=>{
        const toggle=card.querySelector('[data-ambient-toggle]'),label=card.querySelector('[data-ambient-label]'),slider=card.querySelector('[data-ambient-volume]'),output=card.querySelector('[data-ambient-output]'),message=card.querySelector('[data-ambient-status]');
        const state={playing:false,backend:null};ambient.push(state);
        function paint(){toggle.setAttribute('aria-pressed',String(state.playing));label.textContent=card.dataset.ambientLabel+(state.playing?' 끄기':' 켜기');card.dataset.ambientState=state.playing?'playing':'paused';message.textContent=state.playing?'환경음을 재생하고 있습니다. 편안히 읽어보세요.':'켜기 버튼을 눌러 배경음을 들어보세요.';update();}
        state.stop=async()=>{if(state.backend)await state.backend.pause();state.playing=false;paint();};
        function changeVolume(){output.value=slider.value+'%';slider.setAttribute('aria-valuetext',slider.value+'%');if(state.backend)state.backend.setVolume(volumeValue(slider.value));}
        slider.addEventListener('input',changeVolume);
        toggle.addEventListener('click',async()=>{
          toggle.disabled=true;
          try{
            if(state.playing){await state.stop();}
            else{
              if(!state.backend){
                const filename=ambientFiles[card.dataset.ambientKind];if(!filename)throw Error('Unknown ambience');
                const audio=document.createElement('audio');audio.src=new URL(filename,assets).href;audio.preload='none';audio.loop=true;audio.hidden=true;card.append(audio);
                state.backend={play:()=>audio.play(),pause:()=>{audio.pause();},setVolume:value=>{audio.volume=value;}};
              }
              state.backend.setVolume(volumeValue(slider.value));await state.backend.play();state.playing=true;paint();
            }
          }catch(error){state.playing=false;paint();message.textContent='환경음을 켜지 못했습니다. 다시 눌러 주세요.';console.warn('Archive ambience:',error);}
          finally{toggle.disabled=false;}
        });
        changeVolume();paint();
      });
      deck.addEventListener('click',event=>{
        const load=event.target.closest('[data-sound-load]');if(!load)return;
        const card=load.closest('[data-video-id]');const frame=document.createElement('iframe');frame.src=embedUrl(card.dataset.videoId);frame.title=card.dataset.videoTitle+' · YouTube 플레이어';frame.width='560';frame.height='315';frame.loading='lazy';frame.referrerPolicy='strict-origin-when-cross-origin';frame.allow='accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share';frame.allowFullscreen=true;card.querySelector('.sound-player').replaceChildren(frame);update();
      });
      stop.addEventListener('click',async()=>{deck.querySelectorAll('[data-video-id]').forEach(resetVideo);await Promise.all(ambient.map(state=>state.stop()));update();});update();
    });
  });
})(typeof window!=='undefined'?window:globalThis);
