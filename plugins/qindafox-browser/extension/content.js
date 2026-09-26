/* Each reference belongs to one atomic observation and one actual DOM node. */
(() => {
  if (globalThis.__qindafoxAgent) return;
  globalThis.__qindafoxAgent = true;
  let current = null;
  const clean = (v, n = 180) => String(v || "").replace(/\s+/g, " ").trim().slice(0, n);
  const sensitive = e => e.matches('input[type=password], input[autocomplete^="cc-"], input[autocomplete="one-time-code"]');
  const visible = e => {
    const r = e.getBoundingClientRect(), s = getComputedStyle(e);
    return r.width > 0 && r.height > 0 && s.visibility !== "hidden" && s.display !== "none" && s.opacity !== "0" && !e.closest('[hidden],[inert],[aria-hidden="true"]');
  };
  const inView = e => { const r = e.getBoundingClientRect(); return r.bottom > 0 && r.right > 0 && r.top < innerHeight && r.left < innerWidth; };
  function all(root = document) {
    const result = [];
    for (const e of root.querySelectorAll('*')) { result.push(e); if (e.shadowRoot) result.push(...all(e.shadowRoot)); }
    return result;
  }
  function name(e) {
    const root = e.getRootNode();
    const labelled = (e.getAttribute('aria-labelledby') || '').split(/\s+/).map(id => root.getElementById?.(id)?.textContent || '').join(' ');
    return clean(labelled || e.getAttribute('aria-label') || [...(e.labels || [])].map(l => l.innerText).join(' ') || e.getAttribute('alt') || e.innerText || e.getAttribute('placeholder') || e.getAttribute('title') || e.getAttribute('name'));
  }
  function role(e) {
    return e.getAttribute('role') || ({A:'link', BUTTON:'button', SELECT:'combobox', TEXTAREA:'textbox', SUMMARY:'button'}[e.tagName]) || (e.tagName === 'INPUT' ? ({checkbox:'checkbox', radio:'radio', submit:'button', button:'button'}[e.type] || 'textbox') : e.isContentEditable ? 'textbox' : 'control');
  }
  function describe(e, ref) {
    const editable = e.matches('input:not([type=button]):not([type=submit]):not([type=checkbox]):not([type=radio]):not([type=file]):not([type=hidden]),textarea') || e.isContentEditable;
    const actions = ['click', 'scroll'];
    if (editable && !e.readOnly) actions.push('fill');
    if (e.tagName === 'SELECT') actions.push('select');
    if (e.matches('input[type=checkbox],input[type=radio]')) actions.push('check');
    const d = {ref, role:role(e), name:name(e), actions, disabled:!!(e.disabled || e.getAttribute('aria-disabled') === 'true'), sensitive:sensitive(e)};
    if ('value' in e && !sensitive(e) && e.type !== 'file') d.value = clean(e.value, 120);
    if ('checked' in e) d.checked = e.checked;
    if (e.tagName === 'SELECT') d.options = [...e.options].slice(0, 60).map(o => ({value:o.value, label:clean(o.label), disabled:o.disabled}));
    if (e.href) d.href = e.href;
    return d;
  }
  const fingerprint = e => JSON.stringify({...describe(e, ''), context:clean(e.parentElement?.innerText, 240)});
  function pageText(limit, viewport) {
    const texts = [];
    let count = 0;
    function walk(root) {
      const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
      let node;
      while ((node = walker.nextNode()) && count < limit) {
        const e = node.parentElement;
        if (!e || e.closest('script,style,noscript,textarea,[contenteditable],input') || !visible(e) || (viewport && !inView(e))) continue;
        const t = clean(node.nodeValue, limit - count);
        if (t) { texts.push(t); count += t.length + 1; }
      }
      for (const e of root.querySelectorAll('*')) if (e.shadowRoot && count < limit) walk(e.shadowRoot);
    }
    walk(document.body || document.documentElement);
    return texts.join('\n').slice(0, limit);
  }
  function snapshot(p) {
    const token = crypto.randomUUID(), nodes = new Map(), elements = [];
    const max = Math.max(1, Math.min(p.maxElements || 120, 500));
    const candidates = all().filter(e => e.matches('a[href],button,input:not([type=hidden]),select,textarea,summary,[role=button],[role=link],[role=checkbox],[role=radio],[role=tab],[role=option],[role=combobox],[role=textbox],[contenteditable=true],[tabindex]') && visible(e) && (!p.viewportOnly || inView(e)));
    for (const e of candidates.slice(0, max)) {
      const ref = `${token}:${elements.length + 1}`;
      nodes.set(ref, {e, fingerprint:fingerprint(e)});
      elements.push(describe(e, ref));
    }
    current = {token, nodes, url:location.href};
    return {document:token, url:location.href, title:document.title, text:pageText(Math.min(p.maxText || 6000, 30000), !!p.viewportOnly), elements, truncated:candidates.length > max, ready:document.readyState, viewport:{width:innerWidth,height:innerHeight}, scroll:{x:scrollX,y:scrollY}};
  }
  function resolve(ref) {
    const item = current?.nodes.get(ref);
    if (!item || current.url !== location.href || !item.e.isConnected || fingerprint(item.e) !== item.fingerprint) throw Error('STALE_REFERENCE: observe again before acting');
    if (!visible(item.e) || item.e.disabled || item.e.getAttribute('aria-disabled') === 'true') throw Error('NOT_ACTIONABLE');
    return item.e;
  }
  function uncovered(e) {
    e.scrollIntoView({block:'center', inline:'center', behavior:'instant'});
    const r = e.getBoundingClientRect(), x = Math.max(0, Math.min(innerWidth - 1, r.x + r.width / 2)), y = Math.max(0, Math.min(innerHeight - 1, r.y + r.height / 2));
    let hit = document.elementFromPoint(x,y);
    while (hit?.shadowRoot) { const deeper = hit.shadowRoot.elementFromPoint(x,y); if (!deeper || deeper === hit) break; hit = deeper; }
    if (hit !== e && !e.contains(hit)) throw Error('OCCLUDED: target is covered; observe or dismiss the overlay');
  }
  async function act(p) {
    const allowed = ['click','fill','select','check','scroll','key'];
    if (!allowed.includes(p.action)) throw Error('Unknown action');
    const e = p.ref ? resolve(p.ref) : null;
    if (!e && !['scroll'].includes(p.action)) throw Error('A fresh ref is required');
    if (e) uncovered(e);
    if (p.action !== 'key' && e && !describe(e, p.ref).actions.includes(p.action)) throw Error('Action incompatible with target');
    // Consume references before dispatch: no replay after timeouts or ambiguous side effects.
    current = null;
    if (p.action === 'click') { e.focus(); e.click(); }
    if (p.action === 'fill') {
      if (typeof p.text !== 'string' || p.text.length > 30000) throw Error('fill needs text, at most 30000 characters');
      e.focus();
      if (e.isContentEditable) e.textContent = p.text;
      else {
        const prototype = e.tagName === 'TEXTAREA' ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype;
        Object.getOwnPropertyDescriptor(prototype, 'value').set.call(e,p.text);
      }
      e.dispatchEvent(new InputEvent('input', {bubbles:true,inputType:'insertText',data:sensitive(e) ? null : p.text}));
      e.dispatchEvent(new Event('change',{bubbles:true}));
    }
    if (p.action === 'select') {
      const option = [...e.options].find(o => o.value === p.value && !o.disabled);
      if (!option) throw Error('Select value was not an enabled observed option');
      e.value = p.value;
      e.dispatchEvent(new Event('input',{bubbles:true})); e.dispatchEvent(new Event('change',{bubbles:true}));
    }
    if (p.action === 'check') { if (typeof p.checked !== 'boolean') throw Error('checked must be boolean'); if (e.type === 'radio' && !p.checked) throw Error('Cannot uncheck radio directly'); if (e.checked !== p.checked) e.click(); }
    if (p.action === 'scroll') {
      const amount = Math.max(-2000,Math.min(Number(p.amount ?? 650),2000));
      if (!Number.isFinite(amount)) throw Error('Invalid scroll amount');
      (e || window).scrollBy({top:amount,behavior:'instant'});
    }
    if (p.action === 'key') {
      if (!['Enter','Escape','ArrowDown','ArrowUp','ArrowLeft','ArrowRight','Tab','Home','End','Backspace','Delete',' '].includes(p.key)) throw Error('Unsupported key');
      e.focus();
      e.dispatchEvent(new KeyboardEvent('keydown',{key:p.key,bubbles:true,cancelable:true}));
      e.dispatchEvent(new KeyboardEvent('keyup',{key:p.key,bubbles:true}));
    }
    return {performed:true, action:p.action, verifyRequired:true, syntheticInput:true};
  }
  browser.runtime.onMessage.addListener((m) => {
    if (m.qindafox !== true) return;
    return Promise.resolve().then(() => {
      if (m.method === 'observe') return snapshot(m.params || {});
      if (m.method === 'act') return act(m.params || {});
      if (m.method === 'extract') return {url:location.href,title:document.title,text:pageText(Math.min(m.params?.maxText || 15000, 60000),false)};
      throw Error('Unknown content method');
    });
  });
})();
