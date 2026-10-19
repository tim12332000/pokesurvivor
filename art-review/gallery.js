'use strict';

(() => {
  const STORAGE_KEY = 'naruto-animation-lab-reviews-v1';
  const gallery = document.getElementById('gallery');
  const message = document.getElementById('message');
  const filter = document.getElementById('character');
  const categoryFilter = document.getElementById('category');
  const categories = { movement: '方向移動', common: '共通動作', skill: '技能演出' };
  let disposePlayers = [];
  let manifest = null;
  let items = [];
  let reviews = {};
  let storageAvailable = true;
  try { reviews = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}') || {}; }
  catch (_) { storageAvailable = false; }
  if (typeof reviews !== 'object' || Array.isArray(reviews)) reviews = {};

  function element(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = String(text);
    return node;
  }
  function safeURL(value, localOnly = false) {
    if (typeof value !== 'string' || !value.trim()) return null;
    try {
      const url = new URL(value, location.href);
      if (!['http:', 'https:'].includes(url.protocol)) return null;
      if (localOnly && (url.origin !== location.origin || !url.pathname.startsWith(new URL('./', location.href).pathname))) return null;
      return url.href;
    } catch (_) { return null; }
  }
  function link(text, url) {
    const a = element('a', '', text);
    a.href = url;
    a.target = '_blank';
    a.rel = 'noopener noreferrer';
    return a;
  }
  function save(id, patch, status) {
    reviews[id] = { ...(reviews[id] || {}), ...patch, updatedAt: new Date().toISOString() };
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(reviews));
      storageAvailable = true;
    } catch (_) { storageAvailable = false; }
    status.textContent = storageAvailable ? '已儲存在此瀏覽器' : '瀏覽器無法儲存，請匯出紀錄保留';
  }
  function detail(title, values) {
    if (!Array.isArray(values) || !values.length) return null;
    const section = element('section', 'detail');
    section.append(element('h3', '', title));
    const list = element('ul');
    values.forEach(value => list.append(element('li', '', value)));
    section.append(list);
    return section;
  }
  function animationPlayer(item, sourceImage) {
    const spec = item.animation;
    if (!spec || !Number.isInteger(spec.columns) || !Number.isInteger(spec.rows) || spec.columns < 1 || spec.rows < 1) return null;
    const total = spec.columns * spec.rows;
    const sequences = (Array.isArray(spec.sequences) ? spec.sequences : []).map(sequence => ({
      name: String(sequence.name || '動作'),
      loop: sequence.loop ?? spec.loop ?? true,
      frames: Array.isArray(sequence.frames) ? sequence.frames.filter(frame => Number.isInteger(frame) && frame >= 0 && frame < total) : []
    })).filter(sequence => sequence.frames.length);
    if (!sequences.length) sequences.push({ name: '全部影格', loop:spec.loop??true, frames: Array.from({ length: total }, (_, i) => i) });
    const wrapper = element('section', 'animation-player');
    const canvas = element('canvas', 'animation-canvas');
    canvas.width = 384;
    canvas.height = 320;
    canvas.setAttribute('aria-label', `${item.title} 格線動畫播放預覽`);
    const context = canvas.getContext('2d');
    const controls = element('div', 'animation-controls');
    const sequenceSelect = element('select');
    sequenceSelect.setAttribute('aria-label', '播放動作');
    sequences.forEach((sequence, index) => {
      const option = element('option', '', sequence.name);
      option.value = String(index);
      sequenceSelect.append(option);
    });
    const previous = element('button', '', '上一格');
    const toggle = element('button', '', '暫停');
    const next = element('button', '', '下一格');
    [previous, toggle, next].forEach(button => { button.type = 'button'; });
    const speed = element('input');
    speed.type = 'number';
    speed.min = '1';
    speed.max = '24';
    speed.value = String(Math.max(1, Math.min(24, Number(spec.fps) || 7)));
    speed.setAttribute('aria-label', '播放 FPS');
    const speedLabel = element('label', 'speed-label', 'FPS ');
    speedLabel.append(speed);
    const counter = element('span', 'frame-counter');
    controls.append(sequenceSelect, previous, toggle, next, speedLabel, counter);
    wrapper.append(canvas, controls, element('p', 'animation-caption', '格線播放預覽，尚未對齊遊戲錨點'));
    let frameIndex = 0;
    let playing = true;
    let visible = false;
    let request = 0;
    let lastTime = null;
    let disposed = false;
    function frames() { return sequences[Number(sequenceSelect.value) || 0].frames; }
    function draw() {
      if (!context) return;
      const frame = frames()[frameIndex];
      canvas.dataset.frame = String(frame);
      counter.textContent = `${frameIndex + 1} / ${frames().length}`;
      context.clearRect(0, 0, canvas.width, canvas.height);
      if (!sourceImage.complete || !sourceImage.naturalWidth) return;
      const width = sourceImage.naturalWidth / spec.columns;
      const height = sourceImage.naturalHeight / spec.rows;
      const scale = Math.min((canvas.width - 24) / width, (canvas.height - 24) / height);
      const dw = width * scale;
      const dh = height * scale;
      context.imageSmoothingEnabled = false;
      context.drawImage(sourceImage, (frame % spec.columns) * width, Math.floor(frame / spec.columns) * height, width, height, (canvas.width - dw) / 2, (canvas.height - dh) / 2, dw, dh);
    }
    function shouldPlay() { return playing && visible && !document.hidden && !disposed; }
    function tick(time) {
      request = 0;
      if (!shouldPlay()) return;
      if (lastTime === null) lastTime = time;
      const interval = 1000 / Math.max(1, Math.min(24, Number(speed.value) || 7));
      if (time - lastTime >= interval) {
        const steps = Math.floor((time - lastTime) / interval);
        if(!sequences[Number(sequenceSelect.value)||0].loop&&frameIndex+steps>=frames().length-1){frameIndex=frames().length-1;draw();pause();return;}
        frameIndex = (frameIndex + steps) % frames().length;
        lastTime += steps * interval;
        draw();
      }
      request = requestAnimationFrame(tick);
    }
    function sync() {
      if (request) cancelAnimationFrame(request);
      request = 0;
      lastTime = null;
      if (shouldPlay()) request = requestAnimationFrame(tick);
    }
    function pause() { playing = false; toggle.textContent = '播放'; sync(); }
    previous.addEventListener('click', () => { pause(); frameIndex = (frameIndex + frames().length - 1) % frames().length; draw(); });
    next.addEventListener('click', () => { pause(); frameIndex = (frameIndex + 1) % frames().length; draw(); });
    toggle.addEventListener('click', () => {if(!playing&&!sequences[Number(sequenceSelect.value)||0].loop&&frameIndex===frames().length-1){frameIndex=0;draw();} playing = !playing; toggle.textContent = playing ? '暫停' : '播放'; sync(); });
    sequenceSelect.addEventListener('change', () => { frameIndex = 0; draw(); sync(); });
    speed.addEventListener('change', () => { speed.value = String(Math.max(1, Math.min(24, Number(speed.value) || 7))); sync(); });
    sourceImage.addEventListener('load', draw);
    document.addEventListener('visibilitychange', sync);
    const observer = new IntersectionObserver(entries => { visible = entries[0].isIntersecting; sync(); });
    observer.observe(canvas);
    disposePlayers.push(() => {
      disposed = true;
      observer.disconnect();
      if (request) cancelAnimationFrame(request);
      sourceImage.removeEventListener('load', draw);
      document.removeEventListener('visibilitychange', sync);
    });
    draw();
    return wrapper;
  }
  function card(item) {
    const article = element('article', 'card');
    article.dataset.itemId = item.id;
    const imageLink = link('', safeURL(item.image, true));
    imageLink.className = 'image-link';
    imageLink.setAttribute('aria-label', `${item.title}，開啟完整圖片`);
    const image = element('img');
    image.src = imageLink.href;
    image.alt = item.title;
    image.loading = item.animation ? 'eager' : 'lazy';
    image.addEventListener('error', () => {
      imageLink.replaceChildren(element('p', 'image-error', '圖片讀取失敗，請確認候選檔案路徑。'));
    });
    imageLink.append(image);
    const body = element('div', 'card-body');
    const tags = element('div', 'tags');
    [item.character, categories[item.category], item.kind || '美術提案'].filter(Boolean).forEach(text => tags.append(element('span', 'tag', text)));
    tags.append(element('span', 'tag pending', '尚待使用者核准'));
    tags.append(element('span','tag',item.runtimePreview?'已接獨立移動試玩':'僅分鏡審閱'));
    body.append(tags, element('h2', '', item.title), element('p', 'summary', item.summary || ''));
    const beforeURL = safeURL(item.beforeImage, true);
    if (beforeURL) {
      const before = element('div', 'before');
      const a = link('', beforeURL);
      const img = element('img');
      img.src = beforeURL;
      img.alt = `${item.title} 原始參考`;
      a.append(img);
      before.append(a, element('span', '', '原始素材／目前版本參考 · 點圖放大'));
      body.append(before);
    }
    [detail('這版改善', item.improvements), detail('仍需注意', item.limitations)].forEach(node => { if (node) body.append(node); });
    if (item.qa) {
      const qa = element('div', 'qa');
      qa.append(element('strong', '', `製作端初審${Number.isFinite(item.qa.score) ? ` ${item.qa.score}/100` : ''}`));
      if (item.qa.verdict) qa.append(element('div', '', item.qa.verdict));
      body.append(qa);
    }
    const references = element('div', 'references');
    (Array.isArray(item.references) ? item.references : []).forEach(ref => {
      const url = safeURL(ref.url);
      if (url) references.append(link(ref.title || '參考來源', url));
    });
    if (references.childElementCount) body.append(references);
    const review = element('section', 'review');
    const choices = element('div', 'choices');
    const saved = element('p', 'saved', storageAvailable ? '選擇與備註只保存在此瀏覽器' : '瀏覽器無法儲存，請匯出紀錄保留');
    [['approve', '認可這版'], ['revise', '需要修改'], ['reject', '不採用']].forEach(([value, text]) => {
      const button = element('button', '', text);
      button.type = 'button';
      button.dataset.decision = value;
      button.setAttribute('aria-pressed', String(reviews[item.id]?.decision === value));
      button.addEventListener('click', () => {
        save(item.id, { decision: value }, saved);
        choices.querySelectorAll('button').forEach(other => other.setAttribute('aria-pressed', String(other === button)));
      });
      choices.append(button);
    });
    const label = element('label', '', '修改方向／審閱備註');
    const notes = element('textarea');
    notes.id = `note-${item.id}`;
    label.htmlFor = notes.id;
    notes.placeholder = '例如：蓄力姿勢保留，雷光縮小一點…';
    notes.value = typeof reviews[item.id]?.note === 'string' ? reviews[item.id].note : '';
    notes.addEventListener('input', () => save(item.id, { note: notes.value }, saved));
    review.append(choices, label, notes, saved);
    body.append(review, element('p', 'file-path', `art-review/${item.image}`));
    const player = animationPlayer(item, image);
    if (player) {
      const sheet = element('details', 'full-sheet');
      sheet.append(element('summary', '', '查看完整圖集／點圖開啟原尺寸'), imageLink);
      article.append(player, sheet, body);
    } else article.append(imageLink, body);
    return article;
  }
  function render() {
    disposePlayers.forEach(dispose => dispose());
    disposePlayers = [];
    const visible = items.filter(item => (filter.value === 'all' || item.character === filter.value) && (categoryFilter.value === 'all' || item.category === categoryFilter.value));
    gallery.replaceChildren(...visible.map(card));
    document.getElementById('count').textContent = `${visible.length} 件候選作品`;
    message.textContent = visible.length ? '點選圖片可開啟原尺寸檔案。AI 概念稿需另行製作遊戲可用動畫。' : '目前沒有符合篩選條件的候選作品。';
  }
  filter.addEventListener('change', render);
  categoryFilter.addEventListener('change', render);
  document.getElementById('export').addEventListener('click', () => {
    const data = {
      branch: manifest?.branch || '', baseCommit: manifest?.baseCommit || '',
      exportedAt: new Date().toISOString(),
      reviews: items.map(item => ({ id: item.id, title: item.title, decision: reviews[item.id]?.decision || 'unreviewed', note: reviews[item.id]?.note || '', updatedAt: reviews[item.id]?.updatedAt || null }))
    };
    const url = URL.createObjectURL(new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' }));
    const a = element('a');
    a.href = url;
    a.download = `animation-review-${new Date().toISOString().slice(0, 10)}.json`;
    a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  });
  fetch('./manifest.json', { cache: 'no-store' })
    .then(response => { if (!response.ok) throw new Error('manifest'); return response.json(); })
    .then(data => {
      manifest = data;
      items = (Array.isArray(data.items) ? data.items : []).filter(item => item && typeof item.id === 'string' && item.status === 'candidate' && safeURL(item.image, true));
      document.getElementById('branch').textContent = `分支 ${data.branch || '未註明'}`;
      document.getElementById('base').textContent = `起點 ${String(data.baseCommit || '未註明').slice(0, 12)}`;
      [...new Set(items.map(item => item.character).filter(Boolean))].forEach(character => {
        const option = element('option', '', character);
        option.value = character;
        filter.append(option);
      });
      render();
    })
    .catch(() => {
      document.getElementById('branch').textContent = '候選清單尚未就緒';
      document.getElementById('base').hidden = true;
      message.textContent = '無法讀取 manifest.json。請透過本地 HTTP 網址開啟，並確認候選清單已建立。';
    });
})();
