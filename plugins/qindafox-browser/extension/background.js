let port, paused = false, chain = Promise.resolve();
const pauseKey = 'paused';
const publicTab = t => ({id:t.id,windowId:t.windowId,url:t.url,title:t.title,active:t.active,status:t.status});
function safeUrl(value) { const u = new URL(value); if (!['http:','https:','file:','about:'].includes(u.protocol) || (u.protocol === 'about:' && u.href !== 'about:blank')) throw Error('Only http, https, file, or about:blank navigation is supported'); return u.href; }
async function content(tabId, method, params, frameId = 0) {
  await browser.tabs.get(tabId);
  try { return await browser.tabs.sendMessage(tabId, {qindafox:true,method,params}, {frameId}); }
  catch (e) {
    if (!String(e).includes('Receiving end does not exist') && !String(e).includes('Could not establish connection')) throw e;
    await browser.tabs.executeScript(tabId,{file:'content.js',frameId,matchAboutBlank:true});
    return browser.tabs.sendMessage(tabId,{qindafox:true,method,params},{frameId});
  }
}
async function dispatch(method,p) {
  if (method === 'status') return {paused,version:'0.1.0',browser:await browser.runtime.getBrowserInfo()};
  if (paused) throw Error('PAUSED: click the QindaFox Agent toolbar button to resume');
  if (method === 'tabs') return (await browser.tabs.query({})).filter(t=>!t.incognito).map(publicTab);
  if (method === 'open') return publicTab(await browser.tabs.create({url:safeUrl(p.url),active:p.active !== false}));
  if (!Number.isInteger(p.tabId)) throw Error('Explicit integer tabId required');
  const tab = await browser.tabs.get(p.tabId);
  if (tab.incognito) throw Error('Private tabs are excluded');
  if (method === 'navigate') return publicTab(await browser.tabs.update(p.tabId,{url:safeUrl(p.url)}));
  if (method === 'activate') { await browser.windows.update(tab.windowId,{focused:true}); return publicTab(await browser.tabs.update(p.tabId,{active:true})); }
  if (method === 'close') { await browser.tabs.remove(p.tabId); return {closed:true}; }
  if (method === 'back') { await browser.tabs.goBack(p.tabId); return {navigating:true}; }
  if (method === 'forward') { await browser.tabs.goForward(p.tabId); return {navigating:true}; }
  if (method === 'reload') { await browser.tabs.reload(p.tabId); return {navigating:true}; }
  if (method === 'frames') return browser.webNavigation.getAllFrames({tabId:p.tabId});
  if (method === 'screenshot') return {dataUrl:await browser.tabs.captureTab(p.tabId,{format:'jpeg',quality:75})};
  if (['observe','act','extract'].includes(method)) return content(p.tabId,method,p,p.frameId || 0);
  if (method === 'wait') {
    if (!p.text && !p.urlIncludes) throw Error('wait requires text or urlIncludes');
    const end = Date.now() + Math.min(Math.max(p.timeoutMs || 5000,100),15000);
    do {
      const t = await browser.tabs.get(p.tabId);
      let foundText = !p.text;
      try { if (p.text) foundText = (await content(p.tabId,'extract',{maxText:60000},p.frameId || 0)).text.includes(p.text); } catch (_) { /* Navigation may replace the receiver. */ }
      if (foundText && (!p.urlIncludes || t.url.includes(p.urlIncludes))) return {matched:true,url:t.url};
      await new Promise(r=>setTimeout(r,100));
    } while (Date.now() < end);
    throw Error('WAIT_TIMEOUT: expected state not observed');
  }
  throw Error('Unknown browser method');
}
async function badge() { await browser.browserAction.setBadgeText({text:paused?'OFF':'ON'}); await browser.browserAction.setBadgeBackgroundColor({color:paused?'#666666':'#087F8C'}); }
function connect() {
  port = browser.runtime.connectNative('org.qindafox.agent');
  port.onMessage.addListener(message => {
    chain = chain.catch(()=>{}).then(async()=>{
      const started = performance.now();
      try { const result = await dispatch(message.method,message.params || {}); port.postMessage({id:message.id,result,elapsedMs:Math.round(performance.now()-started)}); }
      catch (e) { port.postMessage({id:message.id,error:{message:String(e.message || e)}}); }
    });
  });
  port.onDisconnect.addListener(()=>{setTimeout(connect,2000);});
}
browser.browserAction.onClicked.addListener(async()=>{paused=!paused;await browser.storage.local.set({[pauseKey]:paused});await badge();});
browser.storage.local.get(pauseKey).then(v=>{paused=!!v[pauseKey];badge();connect();});
