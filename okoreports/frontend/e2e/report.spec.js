import { expect, test } from '@playwright/test'

const baseUrl = process.env.BASE_URL ?? 'http://localhost:8080/'

test('renders a report from the sample data in e2e/reports', async ({ page }) => {
  const errors = []
  page.on('pageerror', error => errors.push(error))

  await page.goto(baseUrl)
  await page.getByText('Vis meny').click()
  await page.getByLabel('År 2026 Regnskap (20261124)', { exact: true }).check()

  await expect(page.getByRole('row', { name: /^Sum/ })).toContainText(/2\s200\s*400\s*1\s800/)

  await page.getByRole('row', { name: /^Kafe 1/ }).click()
  await page.getByRole('row', { name: /^Uspesifisert/ }).click()
  await expect(page.getByRole('row', { name: /^3000 Salgsinntekt/ })).toBeVisible()

  expect(errors).toEqual([])
})
