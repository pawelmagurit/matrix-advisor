import type { OrderLine } from '@/lib/cutting/types'

interface OrdersTableProps {
  orders: OrderLine[]
  onChange: (orders: OrderLine[]) => void
}

export function OrdersTable({ orders, onChange }: OrdersTableProps) {
  const update = (index: number, patch: Partial<OrderLine>) => {
    const next = orders.map((o, i) => (i === index ? { ...o, ...patch } : o))
    onChange(next)
  }

  const addRow = () => {
    const ref = orders[0]
    onChange([
      ...orders,
      {
        orderId: `ZL-${Date.now()}`,
        profileCode: ref?.profileCode ?? 'E06335-4',
        matrixCode: ref?.matrixCode ?? ref?.profileCode ?? 'E06335-4',
        contractor: ref?.contractor,
        alloy: ref?.alloy ?? '6060',
        lengthMm: 6000,
        quantity: 1,
        tolerancePlusMm: 10,
        toleranceMinusMm: 0,
      },
    ])
  }

  const removeRow = (index: number) => {
    onChange(orders.filter((_, i) => i !== index))
  }

  return (
    <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-slate-200 bg-slate-50 text-left">
            <th className="p-2">Zlecenie</th>
            <th className="p-2">Matryca</th>
            <th className="p-2">Kontrahent</th>
            <th className="p-2">Profil</th>
            <th className="p-2">Stop</th>
            <th className="p-2">Długość [mm]</th>
            <th className="p-2">Ilość</th>
            <th className="p-2">Tol. +/− [mm]</th>
            <th className="p-2" />
          </tr>
        </thead>
        <tbody>
          {orders.map((order, i) => (
            <tr key={`${order.orderId}-${i}`} className="border-b border-slate-100">
              <td className="p-2">
                <input
                  className="w-full min-w-[5rem] rounded border border-slate-200 px-2 py-1"
                  value={order.orderId}
                  onChange={(e) => update(i, { orderId: e.target.value })}
                />
              </td>
              <td className="p-2">
                <input
                  className="w-full min-w-[5rem] rounded border border-slate-200 px-2 py-1 font-mono text-xs"
                  value={order.matrixCode ?? order.profileCode}
                  onChange={(e) => update(i, { matrixCode: e.target.value })}
                />
              </td>
              <td className="p-2">
                <input
                  className="w-full min-w-[6rem] rounded border border-slate-200 px-2 py-1"
                  value={order.contractor ?? ''}
                  placeholder="—"
                  onChange={(e) =>
                    update(i, { contractor: e.target.value || undefined })
                  }
                />
              </td>
              <td className="p-2">
                <input
                  className="w-full min-w-[5rem] rounded border border-slate-200 px-2 py-1 font-mono text-xs"
                  value={order.profileCode}
                  onChange={(e) => update(i, { profileCode: e.target.value })}
                />
              </td>
              <td className="p-2">
                <input
                  className="w-16 rounded border border-slate-200 px-2 py-1"
                  value={order.alloy}
                  onChange={(e) => update(i, { alloy: e.target.value })}
                />
              </td>
              <td className="p-2">
                <input
                  type="number"
                  className="w-24 rounded border border-slate-200 px-2 py-1"
                  value={order.lengthMm}
                  onChange={(e) => update(i, { lengthMm: Number(e.target.value) })}
                />
              </td>
              <td className="p-2">
                <input
                  type="number"
                  className="w-20 rounded border border-slate-200 px-2 py-1"
                  value={order.quantity}
                  onChange={(e) => update(i, { quantity: Number(e.target.value) })}
                />
              </td>
              <td className="p-2 text-xs text-slate-500">
                +{order.tolerancePlusMm ?? 10} / −{order.toleranceMinusMm ?? 0}
                <span className="ml-1 text-slate-400">(info)</span>
              </td>
              <td className="p-2">
                <button
                  type="button"
                  onClick={() => removeRow(i)}
                  className="text-xs text-red-600 hover:underline"
                >
                  Usuń
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <div className="p-3">
        <button
          type="button"
          onClick={addRow}
          className="rounded bg-slate-800 px-3 py-1.5 text-xs font-medium text-white hover:bg-slate-700"
        >
          Dodaj wiersz
        </button>
      </div>
    </div>
  )
}
