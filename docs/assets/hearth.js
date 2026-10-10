(() => {
  "use strict";
  const toggle = document.getElementById("hearthToggle");
  const label = document.getElementById("hearthLabel");
  const volume = document.getElementById("hearthVolume");
  const status = document.getElementById("hearthStatus");
  // SoundsForYou — Campfire Crackling | Fireplace Sound (Pixabay Content License).
  // https://pixabay.com/sound-effects/campfire-crackling-fireplace-sound-119594/
  const fire = new Audio(new URL("./campfire-119594.mp3", document.currentScript.src).href);
  fire.preload = "none";
  fire.loop = true;
  let playing = false;

  function updateControls() {
    toggle.setAttribute("aria-pressed", String(playing));
    label.textContent = playing ? "모닥불 끄기" : "모닥불 켜기";
    status.textContent = playing ? "모닥불이 타고 있습니다. 편안히 읽어보세요." : "장작 소리와 함께 쉬어가세요.";
  }

  function playbackFailed(error) {
    fire.pause();
    playing = false;
    updateControls();
    status.textContent = "배경음을 재생하지 못했습니다. 브라우저의 소리 설정을 확인해 주세요.";
    console.warn("모닥불 배경음:", error);
  }

  function setVolume() {
    volume.setAttribute("aria-valuetext", volume.value + "%");
    fire.volume = Number(volume.value) / 100;
  }

  toggle.addEventListener("click", async () => {
    toggle.disabled = true;
    try {
      if (playing) {
        fire.pause();
        playing = false;
      } else {
        await fire.play();
        playing = true;
      }
      updateControls();
    } catch (error) {
      playbackFailed(error);
    } finally {
      toggle.disabled = false;
    }
  });
  fire.addEventListener("error", () => playbackFailed(fire.error));
  volume.addEventListener("input", setVolume);
  setVolume();
})();
