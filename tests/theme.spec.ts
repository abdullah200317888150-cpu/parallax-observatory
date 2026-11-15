import {test,expect} from '@playwright/test';

test('theme follows the system until explicitly chosen, then persists after reload',async({page})=>{
 await page.emulateMedia({colorScheme:'dark'});
 await page.goto('/');
 await expect(page.locator('html')).toHaveAttribute('data-theme','dark');
 await page.emulateMedia({colorScheme:'light'});
 await expect(page.locator('html')).toHaveAttribute('data-theme','light');
 await page.getByRole('button',{name:'Switch to dark mode'}).click();
 await expect(page.locator('html')).toHaveAttribute('data-theme','dark');
 await page.reload();
 await expect(page.locator('html')).toHaveAttribute('data-theme','dark');
 await expect(page.locator('meta[name="theme-color"]')).toHaveAttribute('content','#101619');
 await page.screenshot({path:'test-results/parallax-dark-desktop.png',fullPage:true});
 await page.getByRole('button',{name:'The mission',exact:true}).click();
 await expect(page.getByRole('dialog')).toHaveCSS('background-color','rgb(25, 34, 34)');
 await page.keyboard.press('Escape');
 await page.getByRole('button',{name:'Switch to light mode'}).click();
 await page.reload();
 await expect(page.locator('html')).toHaveAttribute('data-theme','light');
});

test('theme toggle remains available on mobile without horizontal overflow',async({page})=>{
 await page.setViewportSize({width:390,height:844});
 await page.emulateMedia({colorScheme:'light'});
 await page.goto('/');
 await page.getByRole('button',{name:'Switch to dark mode'}).click();
 await expect(page.getByRole('button',{name:'Switch to light mode'})).toBeInViewport();
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBeTruthy();
 await page.screenshot({path:'test-results/parallax-dark-mobile.png',fullPage:true});
});
