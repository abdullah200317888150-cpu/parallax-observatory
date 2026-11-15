import {test,expect} from '@playwright/test';

test('explorer playback, target selection, coordinate validation, and persistent notebook',async({page})=>{
 await page.goto('/',{waitUntil:'domcontentloaded'});
 await page.screenshot({path:'test-results/parallax-desktop.png',fullPage:true});
 await expect(page.getByRole('heading',{name:'The sky never stands still.'})).toBeVisible();
 await expect(page.getByText('SIMULATED SKY · LEARN THE CONTROLS')).toBeVisible();
 await page.getByRole('button',{name:'Next observation',exact:true}).click();
 await expect(page.getByLabel('Observation timeline')).toHaveValue('1');
 await page.getByRole('button',{name:'Play animation',exact:true}).click();
 await expect(page.getByRole('button',{name:'Pause animation',exact:true})).toBeVisible();
 await page.getByRole('button',{name:'Pause animation',exact:true}).click();
 await page.getByRole('button',{name:/WISE 0855 Follow the motion/}).click();
 await expect(page.getByRole('heading',{name:/WISE 0855/})).toBeVisible();
 await expect(page.locator('#ra')).toHaveValue('133.795129');
 await page.locator('#ra').fill('400');
 await page.getByRole('button',{name:'Explore coordinates',exact:true}).click();
 await expect(page.getByRole('alert')).toContainText('Enter RA');
 await page.getByRole('textbox',{name:'Observation note',exact:true}).fill('Inspect this candidate again.');
 await page.getByRole('button',{name:'Mark an observation',exact:true}).click();
 await page.locator('canvas').click({position:{x:150,y:150}});
 await page.getByRole('button',{name:/Notebook/}).click();
 await expect(page.getByRole('dialog')).toContainText('Inspect this candidate again.');
 await expect(page.getByRole('dialog')).toContainText('SIMULATED TUTORIAL');
 await page.reload({waitUntil:'domcontentloaded'});
 await page.getByRole('button',{name:/Notebook/}).click();
 await expect(page.getByRole('dialog')).toContainText('Inspect this candidate again.');
});

test('real archive results are displayed without simulated fallback',async({page})=>{
 // A raster checkerboard exercises interpolation; SVGs render as vectors and
 // can look identical regardless of Canvas imageSmoothingEnabled.
 const fixture=await page.evaluate(()=>{const c=document.createElement('canvas');c.width=2;c.height=2;const x=c.getContext('2d')!;x.fillStyle='white';x.fillRect(0,0,2,2);x.fillStyle='black';x.fillRect(0,0,1,1);x.fillRect(1,1,1,1);return c.toDataURL()});
 await page.route('**/api/observations?**',async route=>route.fulfill({json:{frames:[{id:'real-1',date:'2025-06-10T00:00:00Z',image:fixture,wavelength:1.2,flagged_fraction:.02,source_url:'https://irsa.ipac.caltech.edu/'}],warnings:['Test archive response']}}));
 await page.goto('/');
 await page.getByRole('button',{name:'Explore coordinates',exact:true}).click();
 await expect(page.getByText('ARCHIVE OBSERVATION',{exact:true})).toBeVisible();
 await expect(page.getByText('SIMULATED SKY · LEARN THE CONTROLS')).toHaveCount(0);
 await expect(page.getByText('1.200 µm')).toBeVisible();
 await expect(page.getByText(/Approx. 59 native pixels across/)).toBeVisible();
 await expect(page.locator('.image-loading')).toHaveCount(0);
 await expect(page.locator('canvas')).toHaveAttribute('data-rendering','smooth');
 const smoothImage=await page.locator('canvas').evaluate((el:HTMLCanvasElement)=>el.toDataURL());
 await page.getByRole('button',{name:'Pixel-exact',exact:true}).click();
 await expect(page.locator('canvas')).toHaveAttribute('data-rendering','pixel-exact');
 await expect.poll(()=>page.locator('canvas').evaluate((el:HTMLCanvasElement)=>el.toDataURL()).then(value=>value!==smoothImage)).toBeTruthy();
 await page.getByRole('button',{name:'Smooth',exact:true}).click();
 await expect(page.locator('canvas')).toHaveAttribute('data-rendering','smooth');
 await expect(page.getByRole('button',{name:'Difference',exact:true})).toBeDisabled();
});

test('archive failure stays honest and coordinate links restore inputs',async({page})=>{
 await page.route('**/api/observations?**',route=>route.fulfill({status:502,json:{detail:'IRSA temporarily unavailable'}}));
 await page.goto('/?ra=133.795129&dec=-7.245147&fov=12&band=D5');
 await expect(page.locator('#ra')).toHaveValue('133.795129');
 await expect(page.locator('#fov')).toHaveValue('12');
 await expect(page.getByRole('combobox',{name:'Infrared detector'})).toHaveValue('D5');
 await page.getByRole('button',{name:'Explore coordinates',exact:true}).click();
 await expect(page.getByRole('alert')).toContainText('IRSA temporarily unavailable');
 await expect(page.getByText('SIMULATED SKY · LEARN THE CONTROLS')).toBeVisible();
});

test('mobile layout has no horizontal overflow and tour works',async({page})=>{
 await page.setViewportSize({width:390,height:844});
 await page.goto('/');
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBeTruthy();
 await page.screenshot({path:'test-results/parallax-mobile.png',fullPage:true});
 await page.getByRole('button',{name:'Open viewing help'}).count();
 await page.getByRole('button',{name:'The mission',exact:true}).click();
 await expect(page.getByRole('dialog')).toBeVisible();
 await page.keyboard.press('Escape');
 await expect(page.getByRole('dialog')).toHaveCount(0);
});
