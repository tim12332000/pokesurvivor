/* Standalone presentation controls. This file is never loaded by the game. */
(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const data = window.KIMIMARO_DESIGN;
  const labels = {
    willow:['WILLOW DANCE',['沉肩展骨','加速連斬','收刃回位']],
    camellia:['CAMELLIA DANCE',['收劍蓄勢','輕刺接重刺','抽劍回防']],
    bullets:['FINGER BONE BULLETS',['抬掌張指','雙手五拍連射','收手繼續走位']],
    larch:['LARCH DANCE',['低身蓄骨','展骨反掃','縮骨回防']],
    vine:['CLEMATIS · VINE',['抽出脊骨鞭','接觸繃緊、短拉','鬆鞭回收']],
    flower:['CLEMATIS · FLOWER',['骨片層疊成鑽','壓身重刺','碎骨、抽鑽回位']],
    bracken:['BRACKEN DANCE',['按地裂紋','骨林逐波拔高','碎裂沉回']],
    lily:['BONE WHIP · LILY',['側後展鞭','順向、反向雙圈掃','收鞭回位']],
    combo:['BONE WHIP → DRILL',['甩鞭、繃緊短拉','雙手轉接、骨鑽成形','重刺命中、抽鑽回位']],
    curse:['EARTH CURSE MARK',['咒紋沿皮膚蔓延','背骨與長尾展開','二階待機、到期還原']]
  };
  const order = ['willow','camellia','bullets','larch','vine','flower','bracken','lily','combo','curse'];
  const state = {skill:'combo',time:0,playing:true,speed:1,rank:1,quantity:0,form:'normal',scenario:'crowd',loop:true,rangeVisible:false,sound:false};
  let scene = null;
  let ready = false;
  let audio = null;
  let lastFrame = 0;
  let audioEvents = [];
  const getSkill = id => data?.getSkill?.(id) || data?.skills?.find(skill => skill.id === id) || data?.[id] || null;
  const getDuration = () => state.skill === 'curse' ? 10 : Math.max(1.55, (getSkill(state.skill)?.duration || 1.4) + .9);
  const format = value => Number.isInteger(value) ? String(value) : Number(value.toFixed(2)).toString();

  function count(id) {
    if (data?.getCount) return data.getCount(id,state.quantity);
    return id === 'willow' ? Math.min(8,Math.floor(4*1.25**state.quantity)) : id === 'bullets' ? Math.min(15,Math.floor(5*1.25**state.quantity)) : 1;
  }
  function damage(skill) {
    let total = skill?.damage?.[state.rank-1] || 0;
    if (skill?.id === 'willow') total *= count('willow') / 4;
    if (skill?.id === 'bullets') total *= count('bullets') / 5;
    return total;
  }
  function events() {
    const list = data?.getHitEvents?.(state.skill,state.quantity) || getSkill(state.skill)?.hits || [];
    if (state.skill === 'curse') return [{t:.2,kind:'transform'},{t:.75,kind:'transform'},{t:1,kind:'transform'},{t:9,kind:'restore'}];
    return list;
  }
  function rebuildEvents() {
    audioEvents = events();
    $('timeline-marks').replaceChildren();
    const duration = getDuration();
    for (const event of audioEvents) {
      const mark = document.createElement('span');
      mark.style.left = `${Math.min(100,event.t/duration*100)}%`;
      $('timeline-marks').append(mark);
    }
  }
  function renderDetails() {
    const skill = getSkill(state.skill);
    const entry = labels[state.skill];
    $('skill-name').textContent = skill?.name || state.skill;
    $('scene-caption').textContent = state.skill === 'combo' ? '蔓接花・羈絆銜接' : `${skill?.name || ''}・${state.scenario === 'boss' ? '首領' : '怪群'}預覽`;
    $('skill-category').textContent = entry?.[0] || 'SHIKOTSUMYAKU';
    $('skill-description').textContent = skill?.description || '';
    $('feel-note').textContent = skill?.feel || '';
    $('damage-label').textContent = state.skill === 'curse' ? '期間增傷' : '基礎總傷害';
    if (state.skill === 'curse') {
      const bonus = (skill?.damageBonus?.[state.rank-1] ?? .1) * 100;
      $('skill-damage').textContent = `+${format(bonus)}%`;
      $('skill-cd').innerHTML = '30<span>s</span>';
      $('skill-duration').innerHTML = '1 + 8<span>s</span>';
    } else {
      $('skill-damage').textContent = format(damage(skill));
      $('skill-cd').innerHTML = state.skill === 'combo' ? '各 8<span>s</span>' : `${format(skill?.cd || 0)}<span>s</span>`;
      $('skill-duration').innerHTML = `${(skill?.duration || 0).toFixed(2)}<span>s</span>`;
    }
    const qHint = state.skill === 'willow' ? `${count('willow')} 連斬 · 每擊基傷固定，最多八連。` : state.skill === 'bullets' ? `${count('bullets')} 枚骨彈 · 五拍射出，最多十五枚。` : state.skill === 'camellia' ? `每刺最多 ${count('camellia')} 名不同敵人；單體總傷不變。` : '這招不增加命中數；可切到柳或穿彈看數量成長。';
    $('quantity-hint').textContent = qHint;
    $('quantity-value').textContent = state.quantity;
    $('quantity-input').setAttribute('aria-valuetext',`${state.quantity} 張數量卡`);
    $('motion-beats').replaceChildren(...(entry?.[1] || []).map(label => {
      const item = document.createElement('li');
      item.textContent = label;
      return item;
    }));
    $('preview-note').textContent = state.skill === 'combo' ? '蔓與花各耗自己的冷卻；同組順接一條動作，不額外送第三擊。' : state.skill === 'curse' ? '1 秒轉形 → 8 秒咒印二 → 還原；普通招式也可切換二階形態觀看。' : state.skill === 'bracken' ? '三波骨林以同一圓心擴張；同敵只受一次傷，首領不被拉動。' : '選一招，拖曳時間軸看接觸、收勢與骨質變化。';
    const formButtons = document.querySelectorAll('[data-form]');
    for (const button of formButtons) {
      button.setAttribute('aria-pressed',String(button.dataset.form === state.form));
      button.disabled = state.skill === 'curse';
    }
    for (const button of document.querySelectorAll('[data-scenario]')) button.setAttribute('aria-pressed',String(button.dataset.scenario === state.scenario));
    for (const button of document.querySelectorAll('[data-skill]')) button.setAttribute('aria-pressed',String(button.dataset.skill === state.skill));
    const selected = $('skill-nav').querySelector('[aria-pressed="true"]');
    if (selected) $('skill-nav').scrollLeft = selected.offsetLeft - $('skill-nav').offsetLeft - ($('skill-nav').clientWidth-selected.offsetWidth)/2;
    $('timeline').max = getDuration();
    $('time-total').textContent = `${getDuration().toFixed(2)} s`;
    rebuildEvents();
    updateTimeLabels();
  }
  function updateTimeLabels() {
    $('timeline').value = state.time;
    $('time-current').textContent = state.time.toFixed(2);
    $('timeline').setAttribute('aria-valuetext',`${state.time.toFixed(2)} 秒`);
    $('play-button').textContent = state.playing ? '暫停' : '播放';
    $('play-button').setAttribute('aria-label',state.playing ? '暫停演出' : '播放演出');
    const skill = getSkill(state.skill);
    const duration = state.skill === 'curse' ? 10 : (skill?.duration || 1);
    const progress = state.time / duration;
    const active = progress < .25 ? 0 : progress < .78 ? 1 : 2;
    [...$('motion-beats').children].forEach((item,index) => item.classList.toggle('active',index === active));
  }
  function applyTime(time, shouldDraw = true) {
    state.time = Math.max(0,Math.min(getDuration(),Number(time) || 0));
    if (scene) {
      scene.setTime(state.time);
      if (shouldDraw) scene.draw();
    }
    updateTimeLabels();
    return scene?.getSnapshot?.();
  }
  function resetScene() {
    if (!scene) return;
    scene.setSkill(state.skill);
    scene.setRank(state.rank);
    scene.setQuantity(state.quantity);
    scene.setForm(state.form);
    scene.setScenario(state.scenario);
    scene.setRangeVisible?.(state.rangeVisible);
    applyTime(0);
  }
  function selectSkill(id) {
    if (!order.includes(id)) return false;
    state.skill = id;
    resetScene();
    renderDetails();
    return true;
  }
  function pause() {
    state.playing = false;
    updateTimeLabels();
  }
  function play() {
    if (state.time >= getDuration()) applyTime(0);
    state.playing = true;
    lastFrame = performance.now();
    updateTimeLabels();
  }

  function getAudio() {
    if (!audio) {
      const AudioCtor = window.AudioContext || window.webkitAudioContext;
      if (!AudioCtor) return null;
      audio = new AudioCtor();
    }
    if (audio.state === 'suspended') audio.resume().catch(() => {});
    return audio;
  }
  function soundEvent(event) {
    if (!state.sound || !audio || audio.state !== 'running') return;
    const heavy = state.skill === 'flower' || state.skill === 'bracken' || (state.skill === 'combo' && event.t > .8);
    const oscillator = audio.createOscillator();
    const gain = audio.createGain();
    const now = audio.currentTime;
    oscillator.type = heavy ? 'triangle' : state.skill === 'bullets' ? 'sine' : 'triangle';
    const initial = heavy ? 135 : state.skill === 'bullets' ? 940 : 430;
    oscillator.frequency.setValueAtTime(initial,now);
    oscillator.frequency.exponentialRampToValueAtTime(heavy ? 43 : 150,now + (heavy ? .14 : .065));
    gain.gain.setValueAtTime(.0001,now);
    gain.gain.exponentialRampToValueAtTime(heavy ? .12 : .035,now+.004);
    gain.gain.exponentialRampToValueAtTime(.0001,now+(heavy ? .19 : .09));
    oscillator.connect(gain).connect(audio.destination);
    oscillator.start(now);
    oscillator.stop(now+.21);
  }
  function frame(now) {
    const dt = Math.min(.06,Math.max(0,(now-lastFrame)/1000));
    lastFrame = now;
    if (ready && state.playing && !document.hidden) {
      const previous = state.time;
      let next = previous+dt*state.speed;
      for (const event of audioEvents) if (event.t > previous && event.t <= next) soundEvent(event);
      if (next > getDuration()) {
        if (state.loop) { next = 0; scene.reset(); }
        else { next = getDuration(); state.playing = false; }
      }
      applyTime(next,false);
      scene.draw();
    }
    requestAnimationFrame(frame);
  }
  function buildNav() {
    for (const id of order) {
      const item = getSkill(id);
      const button = document.createElement('button');
      button.type = 'button';
      button.className = `skill-chip${id === 'combo' || id === 'curse' ? ' special' : ''}`;
      button.dataset.skill = id;
      button.textContent = item?.name || id;
      button.setAttribute('aria-pressed',String(id === state.skill));
      button.addEventListener('click',() => selectSkill(id));
      $('skill-nav').append(button);
    }
  }
  function wireControls() {
    $('play-button').addEventListener('click',() => state.playing ? pause() : play());
    $('replay-button').addEventListener('click',() => { resetScene(); play(); });
    $('timeline').addEventListener('input',event => { const time = event.target.value; pause(); applyTime(time); });
    $('speed-select').addEventListener('change',event => { state.speed = Number(event.target.value); });
    $('loop-toggle').addEventListener('change',event => { state.loop = event.target.checked; });
    $('rank-select').addEventListener('change',event => { state.rank = Number(event.target.value); resetScene(); renderDetails(); });
    $('quantity-input').addEventListener('input',event => { state.quantity = Number(event.target.value); resetScene(); renderDetails(); });
    $('range-toggle').addEventListener('change',event => { state.rangeVisible = event.target.checked; scene?.setRangeVisible?.(state.rangeVisible); scene?.draw(); });
    for (const button of document.querySelectorAll('[data-form]')) button.addEventListener('click',() => { state.form = button.dataset.form; resetScene(); renderDetails(); });
    for (const button of document.querySelectorAll('[data-scenario]')) button.addEventListener('click',() => { state.scenario = button.dataset.scenario; resetScene(); renderDetails(); });
    $('sound-button').addEventListener('click',() => {
      if (!getAudio()) { $('sound-button').textContent = '音效不支援'; return; }
      state.sound = !state.sound;
      $('sound-button').setAttribute('aria-pressed',String(state.sound));
      $('sound-button').textContent = `音效：${state.sound ? '開' : '關'}`;
      $('sound-button').title = state.sound ? '關閉設計音效' : '開啟設計音效';
      if (state.sound) soundEvent({t:state.time});
    });
    document.addEventListener('keydown',event => {
      if (event.target.matches('input,select,textarea,button,a,summary')) return;
      if (event.code === 'Space') { event.preventDefault(); state.playing ? pause() : play(); }
      if (event.code === 'ArrowLeft' || event.code === 'ArrowRight') { event.preventDefault(); pause(); applyTime(state.time+(event.code === 'ArrowLeft' ? -.05 : .05)); }
    });
    document.addEventListener('visibilitychange',() => { lastFrame = performance.now(); });
  }

  const publicAPI = {
    scene:null,ready:false,state,selectSkill,
    get audioContextState() { return audio?.state || 'uninitialized'; },
    setTime(time) { pause(); return applyTime(time); }, play,pause,
    setRank(rank) { state.rank = Math.max(1,Math.min(5,Number(rank)||1)); $('rank-select').value = state.rank; resetScene(); renderDetails(); },
    setQuantity(quantity) { state.quantity = Math.max(0,Math.min(5,Math.floor(Number(quantity)||0))); $('quantity-input').value = state.quantity; resetScene(); renderDetails(); },
    setForm(form) { state.form = form === 'curse' ? 'curse' : 'normal'; resetScene(); renderDetails(); },
    setScenario(scenario) { state.scenario = scenario === 'boss' ? 'boss' : 'crowd'; resetScene(); renderDetails(); },
    getDuration
  };
  window.KimimaroPreview = publicAPI;

  async function init() {
    if (!data || !window.KimimaroScene) {
      $('load-message').textContent = '預覽檔案未完整載入，請從本機服務重新開啟此頁。';
      return;
    }
    buildNav();
    wireControls();
    renderDetails();
    scene = new window.KimimaroScene($('preview-canvas'));
    publicAPI.scene = scene;
    try { await scene.loadAssets(); }
    catch (error) { console.warn('Design preview asset fallback:',error); }
    resetScene();
    ready = true;
    publicAPI.ready = true;
    $('load-message').classList.add('hidden');
    lastFrame = performance.now();
    requestAnimationFrame(frame);
  }
  init().catch(error => {
    console.error(error);
    $('load-message').textContent = '預覽尚未準備完成，請重新整理。';
  });
})();
