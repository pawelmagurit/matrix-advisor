import type { CutPiece, OrderLine } from './types'

export function expandOrderLines(orders: OrderLine[]): CutPiece[] {
  const pieces: CutPiece[] = []
  for (const order of orders) {
    for (let i = 0; i < order.quantity; i++) {
      pieces.push({
        orderId: order.orderId,
        lengthMm: order.lengthMm,
        pieceIndex: i + 1,
      })
    }
  }
  return pieces
}
