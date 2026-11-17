const {chromium} = require('C:/Users/Star Rain/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const path = require('path');
const fs = require('fs');
const assert = require('assert');
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe'});
 const context=await browser.newContext({viewport:{width:1440,height:1050}});
 const page=await context.newPage();
 const errors=[];page.on('pageerror',e=>errors.push(e.message));
 const pages=['index','build','extensions','reliability','codex','pi','deepseek','reading'];
 fs.mkdirSync('verification',{recursive:true});
 for(const slug of pages){
  await page.goto('file:///'+path.resolve(slug+'.html').replace(/\\/g,'/'));
  await page.waitForFunction(()=>window.SEARCH_INDEX?.length>0);
  assert.strictEqual(await page.locator('h1').count(),1);
  assert.strictEqual(await page.locator('.local-toc a').count(),await page.locator('article h2').count());
  assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
  assert.strictEqual(await page.locator('article pre').count(),await page.locator('article .copy-btn').count());
  if(slug==='index'){
   await page.screenshot({path:'verification/desktop.png'});
   await page.locator('#loop-next').click();
   assert((await page.locator('#loop-trace').textContent()).includes('组装上下文'));
   await page.locator('#loop-mode').selectOption('denied');
   for(let i=0;i<4;i++)await page.locator('#loop-next').click();
   assert((await page.locator('#loop-trace').textContent()).includes('门禁拒绝'));
   await page.locator('#loop-explorer').screenshot({path:'verification/loop.png'});
   await page.locator('#search-open').click();
   await page.locator('#search-input').fill('skill');
   assert(await page.locator('#search-results a').count()>0);
   await page.screenshot({path:'verification/search.png'});
   await page.keyboard.press('Escape');
   await page.locator('#font-toggle').click();
   assert(await page.locator('body.large-font').count());
   await page.locator('#font-toggle').click();
   await page.locator('#completed').check();
   await page.reload();
   assert(await page.locator('#completed').isChecked());
   await page.locator('#completed').uncheck();
  }
  if(slug==='reliability'){
   await page.locator('#budget-context').fill('16000');
   await page.locator('#budget-used').fill('44000');
   assert((await page.locator('#budget-result').textContent()).includes('超出'));
  }
 }
 await page.setViewportSize({width:390,height:844});
 for(const slug of pages){
  await page.goto('file:///'+path.resolve(slug+'.html').replace(/\\/g,'/'));
  assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
 }
 await page.goto('file:///'+path.resolve('index.html').replace(/\\/g,'/'));
 await page.screenshot({path:'verification/mobile.png'});
 await page.locator('#menu-toggle').click();
 assert.strictEqual(await page.locator('#menu-toggle').getAttribute('aria-expanded'),'true');
 await page.locator('.local-toc a').nth(3).click();
 assert.strictEqual(await page.locator('#menu-toggle').getAttribute('aria-expanded'),'false');
 assert.strictEqual(errors.length,0,errors.join('\n'));
 await page.setViewportSize({width:1440,height:1050});
 await page.goto('file:///'+path.resolve('index.html').replace(/\\/g,'/'));
 await page.emulateMedia({media:'print'});
 await page.pdf({path:'verification/print-sample.pdf',format:'A4',printBackground:true});
 await browser.close();
 fs.writeFileSync('verification/browser-results.json',JSON.stringify({pages:8,desktop:true,mobile:true,fileProtocol:true,search:true,loop:true,budget:true,completionStorage:true,print:true,pageErrors:errors},null,2));
 console.log('Verified 8 pages via file:// at desktop and mobile; interactions passed.');
})().catch(e=>{console.error(e);process.exit(1)});
