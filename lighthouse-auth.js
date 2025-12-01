/**
 * Lighthouse authentication script
 * Logs in as test user before auditing authenticated pages
 */
module.exports = async (browser, context) => {
  const page = await browser.newPage();
  
  // Navigate to login page
  await page.goto('http://localhost:8000/login/');
  
  // Fill in login form
  await page.type('input[name="username"]', 'lighthouse_test');
  await page.type('input[name="password"]', 'testpass123');
  
  // Submit form
  await page.click('button[type="submit"]');
  
  // Wait for navigation after login
  await page.waitForNavigation({ waitUntil: 'networkidle0' });
  
  // Get cookies and add them to context
  const cookies = await page.cookies();
  await context.addCookies(cookies);
  
  await page.close();
};

