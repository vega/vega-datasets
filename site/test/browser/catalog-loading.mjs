// Compare two built revisions served with the same compression and caching policy.
// For prerequisites, see browser.mjs. Start each build's preview on a different port,
// then run in a separate terminal:
//   node site/test/browser/catalog-loading.mjs --baseline URL --base URL [--output report.json] [--runs 5]
// Stop other builds and tests while measuring. These are lab timings, not field INP
// or Lighthouse scores. First-activation timings are measured by chart-interactions.mjs.
import { launchBrowser } from './browser.mjs';
import {parseArgs} from 'node:util';
import {writeFileSync} from 'node:fs';
import assert from 'node:assert/strict';
const {values:args}=parseArgs({options:{baseline:{type:'string'},base:{type:'string'},output:{type:'string'},runs:{type:'string',default:'5'}}});
if(!args.baseline || !args.base) throw new Error('Provide --baseline and --base URLs');
const browser = await launchBrowser();
const results={chrome:await browser.version(),conditions:{cpu:4,downloadBytesPerSecond:209715.2,uploadBytesPerSecond:96000,latencyMs:150,cache:false,viewportHeight:900,deviceScaleFactor:1,kind:'local gzip server, alternating builds, lab measurements'},runs:[]};
try {
 for(const width of [390,800]) for(let run=1;run<=Number(args.runs);run++) for(const name of (run%2?['baseline','candidate']:['candidate','baseline'])) {
  const context=await browser.createBrowserContext(); const page=await context.newPage();
  const errors=[];
  page.on('pageerror',e=>errors.push(String(e)));
  page.on('requestfailed',r=>errors.push(`${r.url()}: ${r.failure()?.errorText}`));
  page.on('response',r=>{if(r.status()>=400)errors.push(`${r.status()}: ${r.url()}`);});
  await page.setViewport({width,height:900,deviceScaleFactor:1,isMobile:width<=640,hasTouch:width<=640});
  await page.setCacheEnabled(false); const cdp=await page.createCDPSession();
  await cdp.send('Emulation.setCPUThrottlingRate',{rate:4});
  await cdp.send('Network.emulateNetworkConditions',{offline:false,latency:150,downloadThroughput:209715.2,uploadThroughput:96000});
  await page.evaluateOnNewDocument(()=>{
    window.__lab={lcp:0,cls:0,tbt:0,longTasks:0};
    new PerformanceObserver(list=>{for(const e of list.getEntries()) window.__lab.lcp=e.startTime;}).observe({type:'largest-contentful-paint',buffered:true});
    new PerformanceObserver(list=>{for(const e of list.getEntries()) if(!e.hadRecentInput) window.__lab.cls+=e.value;}).observe({type:'layout-shift',buffered:true});
    new PerformanceObserver(list=>{for(const e of list.getEntries()){window.__lab.tbt+=Math.max(e.duration-50,0);window.__lab.longTasks++;}}).observe({type:'longtask',buffered:true});
  });
  await page.goto(name==='baseline'?args.baseline:args.base,{waitUntil:'networkidle0',timeout:120000});
  assert.deepEqual(errors,[], 'A comparison requires complete assets on both builds');
  const initial=await page.evaluate(()=>{
    const nav=performance.getEntriesByType('navigation')[0],res=performance.getEntriesByType('resource');
    return {...window.__lab,domContentLoaded:nav.domContentLoadedEventEnd,transfer:nav.transferSize+res.reduce((n,e)=>n+e.transferSize,0),htmlTransfer:nav.transferSize,jsDecoded:res.filter(e=>e.name.endsWith('.js')).reduce((n,e)=>n+e.decodedBodySize,0),runtime:res.some(e=>e.name.endsWith('.js')&&e.decodedBodySize>100000),resources:res.map(e=>({url:e.name,bytes:e.transferSize}))};
  });
  await page.$eval('[data-chart]',e=>e.scrollIntoView({block:'center'}));
  const approachMs=run<=3?0:2000;
  if(approachMs) await new Promise(r=>setTimeout(r,approachMs));
  await page.evaluate((width)=>{
    window.__activation=null;
    const type=width>640?'pointerenter':'click';
    const selector=width>640?'[data-chart]':'[data-gallery="vega"]';
    const listener=(event)=>{
      if(!(event.target instanceof Element)||!event.target.closest(selector)) return;
      document.removeEventListener(type,listener,true);
      const at=event.timeStamp;
      const observer=new MutationObserver(()=>{
        if(!document.querySelector('.chart-live:not(.pending) svg.marks'))return;
        observer.disconnect();
        requestAnimationFrame(()=>requestAnimationFrame(()=>window.__activation=performance.now()-at));
      });
      observer.observe(document.querySelector('[data-chart]'),{subtree:true,childList:true,attributes:true});
    };
    document.addEventListener(type,listener,true);
  },width);
  if(width>640)await page.hover('[data-chart]');else await page.tap('[data-gallery="vega"]');
  await page.waitForFunction(()=>window.__activation!==null,{timeout:60000});
  const activationMs=await page.evaluate(()=>window.__activation);
  assert.deepEqual(errors,[]);
  const result={name,width,run,approachMs,initial,activationMs};results.runs.push(result);
  if(args.output) writeFileSync(args.output,JSON.stringify(results,null,2));
  console.log(JSON.stringify({...result,initial:{...initial,resources:undefined}}));await context.close();
 }
}finally{await browser.close();}
