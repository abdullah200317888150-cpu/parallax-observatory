// Start the Python service on port 8010 before running this verification.
// This uses real cached IRSA data and the actual API, without network mocking.
import {chromium} from '@playwright/test';
const browser=await chromium.launch({headless:true});
try {
 const page=await browser.newPage({viewport:{width:1280,height:900}});
 await page.goto('http://127.0.0.1:8010');
 await page.getByRole('button',{name:'Explore coordinates',exact:true}).click();
 await page.getByText('ARCHIVE OBSERVATION',{exact:true}).waitFor({timeout:15000});
 await page.waitForFunction(()=>!document.querySelector('.image-loading'));
 const response=await page.request.get('http://127.0.0.1:8010/api/observations?ra=269.4521&dec=4.6934&fov=6&detector=D2');
 if(!response.ok())throw Error('Real API request failed');
 const data=await response.json();
 const image=await page.request.get(new URL(data.frames[0].image,'http://127.0.0.1:8010').toString());
 if(!image.ok()||!image.headers()['content-type'].includes('image/png'))throw Error('Actual preview could not be served');
 await page.screenshot({path:'test-results/parallax-real-spherex.png',fullPage:true});
 await page.getByRole('button',{name:'Pixel-exact',exact:true}).click();
 await page.screenshot({path:'test-results/parallax-real-pixels.png',fullPage:true});
 await page.getByRole('button',{name:'Smooth',exact:true}).click();
 console.log(JSON.stringify({status:response.status(),frames:data.frames.length,first:data.frames[0].date,last:data.frames.at(-1).date,source:data.source,image_status:image.status()}));
} finally {await browser.close()}
