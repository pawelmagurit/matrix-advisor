const PALETTE = [
  '#2563eb',
  '#059669',
  '#d97706',
  '#7c3aed',
  '#db2777',
  '#0891b2',
  '#4f46e5',
  '#65a30d',
]

export function orderColor(orderId: string): string {
  let hash = 0
  for (let i = 0; i < orderId.length; i++) {
    hash = orderId.charCodeAt(i) + ((hash << 5) - hash)
  }
  return PALETTE[Math.abs(hash) % PALETTE.length]
}

export const VARIANT_LABELS: Record<string, string> = {
  min_waste: 'Najmniej odpadu',
  min_stocks: 'Najmniej wędek',
  balanced: 'Zbalansowany',
}
