(() => {
  "use strict";
  const toggle = document.getElementById("hearthToggle");
  const label = document.getElementById("hearthLabel");
  const volume = document.getElementById("hearthVolume");
  const status = document.getElementById("hearthStatus");
  let context;
  let master;
  let playing = false;

  // Synthesize a seamless bed of embers and short wood crackles locally.
  // No remote audio, tracking, or copyrighted recordings are required.
  function createFire() {
    context = new AudioContext();
    const length = context.sampleRate * 40;
    const buffer = context.createBuffer(2, length, context.sampleRate);
    for (let channel = 0; channel < 2; channel++) {
      const samples = buffer.getChannelData(channel);
      let ember = 0;
      for (let i = 0; i < length; i++) {
        ember = (ember + (Math.random() * 2 - 1) * 0.02) / 1.02;
        samples[i] = ember * 0.3;
      }
      for (let time = 0.1; time < 39.8; time += 0.07 + Math.random() * 0.28) {
        const start = Math.floor(time * context.sampleRate);
        const duration = Math.floor(context.sampleRate * (0.012 + Math.random() * 0.05));
        const strength = 0.35 + Math.random() * 0.35;
        const pitch = 1400 + Math.random() * 2800;
        for (let i = 0; i < duration; i++) {
          const attack = Math.min(1, i / (context.sampleRate * 0.0004));
          const decay = Math.exp(-i / (duration / 6));
          const snap = Math.sin(2 * Math.PI * pitch * i / context.sampleRate);
          samples[start + i] += ((Math.random() * 2 - 1) * 0.65 + snap * 0.35) * strength * attack * decay;
        }
      }
      for (let i = 0; i < length; i++) samples[i] = Math.max(-0.85, Math.min(0.85, samples[i]));
      const edge = Math.floor(context.sampleRate * 0.04);
      for (let i = 0; i < edge; i++) {
        samples[i] *= i / edge;
        samples[length - 1 - i] *= i / edge;
      }
    }
    const fire = context.createBufferSource();
    fire.buffer = buffer;
    fire.loop = true;
    const warmth = context.createBiquadFilter();
    warmth.type = "lowpass";
    warmth.frequency.value = 6000;
    master = context.createGain();
    master.gain.value = 0;
    fire.connect(warmth).connect(master).connect(context.destination);
    fire.start();
  }

  function setVolume() {
    volume.setAttribute("aria-valuetext", volume.value + "%");
    if (master) {
      master.gain.setTargetAtTime(playing ? Number(volume.value) / 100 * 0.65 : 0, context.currentTime, 0.08);
    }
  }

  toggle.addEventListener("click", async () => {
    toggle.disabled = true;
    try {
      if (!context) createFire();
      if (playing) {
        await context.suspend();
        playing = false;
      } else {
        await context.resume();
        if (context.state !== "running") throw new Error("Audio playback was not started");
        playing = true;
      }
      setVolume();
      toggle.setAttribute("aria-pressed", String(playing));
      label.textContent = playing ? "모닥불 끄기" : "모닥불 켜기";
      status.textContent = playing ? "모닥불이 타고 있습니다. 편안히 읽어보세요." : "장작 소리와 함께 쉬어가세요.";
    } catch (error) {
      status.textContent = "배경음을 재생하지 못했습니다. 브라우저의 소리 설정을 확인해 주세요.";
      console.warn("모닥불 배경음:", error);
    } finally {
      toggle.disabled = false;
    }
  });
  volume.addEventListener("input", setVolume);
})();
