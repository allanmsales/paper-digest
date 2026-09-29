/** Up to 4 significant digits, without float noise like 0.19999999. */
export function formatNumber(value: number): string {
  return Number(value.toPrecision(4)).toString()
}
