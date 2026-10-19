'use strict';

(() => {
  const STORAGE_KEY = 'naruto-animation-lab-reviews-v1';
  const gallery = document.getElementById('gallery');
  const message = document.getElementById('message');
  const filter = document.getElementById('character');
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
  function card(item) {
    const article = element('article', 'card');
    article.dataset.itemId = item.id;
    const imageLink = link('', safeURL(item.image, true));
    imageLink.className = 'image-link';
    imageLink.setAttribute('aria-label', `${item.title}，開啟完整圖片`);
    const image = element('img');
    image.src = imageLink.href;
    image.alt = item.title;
    image.loading = 'lazy';
    image.addEventListener('error', () => {
      imageLink.replaceChildren(element('p', 'image-error', '圖片讀取失敗，請確認候選檔案路徑。'));
    });
    imageLink.append(image);
    const body = element('div', 'card-body');
    const tags = element('div', 'tags');
    [item.character, item.kind || '美術提案'].forEach(text => tags.append(element('span', 'tag', text)));
    tags.append(element('span', 'tag pending', '尚待使用者核准'));
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
    article.append(imageLink, body);
    return article;
  }
  function render() {
    const visible = items.filter(item => filter.value === 'all' || item.character === filter.value);
    gallery.replaceChildren(...visible.map(card));
    document.getElementById('count').textContent = `${visible.length} 件候選作品`;
    message.textContent = visible.length ? '點選圖片可開啟原尺寸檔案。AI 概念稿需另行製作遊戲可用動畫。' : '目前沒有符合篩選條件的候選作品。';
  }
  filter.addEventListener('change', render);
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
