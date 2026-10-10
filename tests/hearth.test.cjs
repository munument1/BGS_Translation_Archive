const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

test("wood crackles dominate the quiet bed, with safe peaks and working controls", async () => {
  const elements = {};
  for (const id of ["hearthToggle", "hearthLabel", "hearthVolume", "hearthStatus"]) {
    elements[id] = {
      value: "30",
      attributes: {},
      handlers: {},
      setAttribute(key, value) { this.attributes[key] = value; },
      addEventListener(key, handler) { this.handlers[key] = handler; }
    };
  }
  let audio;
  class AudioContext {
    constructor() {
      audio = this;
      this.sampleRate = 44100;
      this.currentTime = 0;
      this.state = "suspended";
    }
    createBuffer(channels, length, rate) {
      this.samples = Array.from({ length: channels }, () => new Float32Array(length));
      this.rate = rate;
      return { getChannelData: channel => this.samples[channel] };
    }
    createBufferSource() {
      this.source = { connect: node => node, start() {} };
      return this.source;
    }
    createBiquadFilter() { return { frequency: {}, connect: node => node }; }
    createGain() {
      this.gain = { gain: { setTargetAtTime: value => { this.level = value; } }, connect: node => node };
      return this.gain;
    }
    async resume() { this.state = "running"; }
    async suspend() { this.state = "suspended"; }
  }
  let seed = 17;
  const math = Object.create(Math);
  math.random = () => ((seed = (1664525 * seed + 1013904223) >>> 0) / 2 ** 32);
  vm.runInNewContext(
    fs.readFileSync(path.join(__dirname, "../docs/assets/hearth.js"), "utf8"),
    { document: { getElementById: id => elements[id] }, AudioContext, Math: math, console }
  );
  assert.equal(audio, undefined, "audio must not start before the user's click");
  await elements.hearthToggle.handlers.click();
  assert.equal(audio.state, "running");
  assert.equal(audio.source.loop, true);
  assert.equal(elements.hearthToggle.attributes["aria-pressed"], "true");
  for (const samples of audio.samples) {
    assert.equal(samples.length, audio.rate * 40);
    let peak = 0;
    for (const value of samples) {
      assert.ok(Number.isFinite(value));
      peak = Math.max(peak, Math.abs(value));
    }
    assert.ok(peak <= 0.850001);
    const rms = (start, end) => Math.sqrt(
      samples.subarray(start, end).reduce((sum, value) => sum + value * value, 0) / (end - start)
    );
    const quietBed = rms(Math.floor(audio.rate * 0.05), Math.floor(audio.rate * 0.09));
    const firstCrackle = rms(Math.floor(audio.rate * 0.1), Math.floor(audio.rate * 0.11));
    assert.ok(firstCrackle > quietBed * 3, "a wood snap must stand clearly above the steady noise");
    assert.ok(samples[0] === 0);
    assert.ok(samples.at(-1) === 0);
  }
  elements.hearthVolume.value = "0";
  elements.hearthVolume.handlers.input();
  assert.equal(audio.level, 0);
  assert.equal(elements.hearthVolume.attributes["aria-valuetext"], "0%");
  elements.hearthVolume.value = "100";
  elements.hearthVolume.handlers.input();
  assert.equal(audio.level, 0.65);
  await elements.hearthToggle.handlers.click();
  assert.equal(audio.state, "suspended");
  assert.equal(audio.level, 0);
  assert.equal(elements.hearthToggle.attributes["aria-pressed"], "false");
});
