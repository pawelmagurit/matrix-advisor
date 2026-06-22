import { parse } from 'csv-parse/browser/esm/sync'
import type { OrderLine } from '@/lib/cutting/types'

const REQUIRED = ['orderId', 'profileCode', 'alloy', 'lengthMm', 'quantity'] as const

const CSV_COLUMNS = [
  'orderId',
  'profileCode',
  'matrixCode',
  'contractor',
  'alloy',
  'lengthMm',
  'quantity',
  'tolerancePlusMm',
  'toleranceMinusMm',
  'priority',
] as const

/** Aliasy nagłówków (Excel PL, polskie nazwy, warianty wielkości liter) */
const HEADER_ALIASES: Record<string, (typeof CSV_COLUMNS)[number]> = {
  orderid: 'orderId',
  zlecenie: 'orderId',
  zlec: 'orderId',
  profilecode: 'profileCode',
  profil: 'profileCode',
  kod_profilu: 'profileCode',
  matrixcode: 'matrixCode',
  matryca: 'matrixCode',
  contractor: 'contractor',
  kontrahent: 'contractor',
  alloy: 'alloy',
  stop: 'alloy',
  lengthmm: 'lengthMm',
  dlugosc: 'lengthMm',
  dlugoscmm: 'lengthMm',
  'dlugosc_mm': 'lengthMm',
  'dlugosc[mm]': 'lengthMm',
  quantity: 'quantity',
  ilosc: 'quantity',
  qty: 'quantity',
  toleranceplusmm: 'tolerancePlusMm',
  toleranceminusmm: 'toleranceMinusMm',
  priority: 'priority',
  priorytet: 'priority',
}

function normalizeHeaderKey(raw: string): string {
  const trimmed = raw.trim().replace(/^\ufeff/, '')
  const canonical = HEADER_ALIASES[trimmed.toLowerCase()]
  if (canonical) return canonical
  // dokładne dopasowanie camelCase z pliku szablonu
  if ((CSV_COLUMNS as readonly string[]).includes(trimmed)) return trimmed
  return trimmed
}

function normalizeRow(row: Record<string, string>): Record<string, string> {
  const out: Record<string, string> = {}
  for (const [key, value] of Object.entries(row)) {
    out[normalizeHeaderKey(key)] = value
  }
  return out
}

function detectDelimiter(text: string): ',' | ';' | '\t' {
  const firstLine = text.split(/\r?\n/).find((l) => l.trim().length > 0) ?? ''
  const commas = (firstLine.match(/,/g) ?? []).length
  const semis = (firstLine.match(/;/g) ?? []).length
  const tabs = (firstLine.match(/\t/g) ?? []).length
  if (semis > commas && semis >= tabs) return ';'
  if (tabs > commas && tabs > semis) return '\t'
  return ','
}

function rowToOrderLine(row: Record<string, string>): OrderLine {
  const lengthMm = Number(row.lengthMm)
  const quantity = Number(row.quantity)

  const order: OrderLine = {
    orderId: row.orderId,
    profileCode: row.profileCode,
    alloy: row.alloy,
    lengthMm,
    quantity,
    tolerancePlusMm: row.tolerancePlusMm ? Number(row.tolerancePlusMm) : 10,
    toleranceMinusMm: row.toleranceMinusMm ? Number(row.toleranceMinusMm) : 0,
  }

  if (row.matrixCode?.trim()) order.matrixCode = row.matrixCode.trim()
  if (row.contractor?.trim()) order.contractor = row.contractor.trim()
  if (row.priority?.trim()) order.priority = Number(row.priority)

  return order
}

export function parseOrdersCsv(text: string): { orders: OrderLine[]; error?: string } {
  try {
    const delimiter = detectDelimiter(text)
    const records = parse(text, {
      columns: true,
      skip_empty_lines: true,
      trim: true,
      bom: true,
      delimiter,
      relax_column_count: true,
    }) as Record<string, string>[]

    if (records.length === 0) {
      return { orders: [], error: 'Plik CSV jest pusty.' }
    }

    const normalized = records.map(normalizeRow)
    const headers = Object.keys(normalized[0])
    const missing = REQUIRED.filter((col) => !headers.includes(col))
    if (missing.length > 0) {
      const found = headers.length > 0 ? headers.join(', ') : '(brak)'
      return {
        orders: [],
        error: `Brak wymaganej kolumny: ${missing[0]}. Wykryte kolumny: ${found}. Upewnij się, że plik używa przecinków lub średników jako separatora (Excel PL zapisuje CSV ze średnikami).`,
      }
    }

    const orders: OrderLine[] = []
    for (let i = 0; i < normalized.length; i++) {
      const row = normalized[i]
      const lengthMm = Number(String(row.lengthMm).replace(/\s/g, '').replace(',', '.'))
      const quantity = Number(String(row.quantity).replace(/\s/g, '').replace(',', '.'))

      if (!Number.isFinite(lengthMm) || lengthMm <= 0) {
        return { orders: [], error: `Wiersz ${i + 2}: nieprawidłowa długość` }
      }
      if (!Number.isFinite(quantity) || quantity <= 0 || !Number.isInteger(quantity)) {
        return { orders: [], error: `Wiersz ${i + 2}: nieprawidłowa ilość (musi być liczbą całkowitą)` }
      }

      orders.push(rowToOrderLine({ ...row, lengthMm: String(lengthMm), quantity: String(quantity) }))
    }

    return { orders }
  } catch {
    return { orders: [], error: 'Nie udało się odczytać pliku CSV.' }
  }
}

export async function readCsvFile(file: File): Promise<{ orders: OrderLine[]; error?: string }> {
  const text = await file.text()
  return parseOrdersCsv(text)
}

function escapeCsvCell(value: string | number | undefined): string {
  if (value === undefined || value === '') return ''
  const str = String(value)
  if (str.includes(',') || str.includes('"') || str.includes('\n')) {
    return `"${str.replace(/"/g, '""')}"`
  }
  return str
}

export function serializeOrdersCsv(orders: OrderLine[]): string {
  const header = CSV_COLUMNS.join(',')
  const rows = orders.map((order) =>
    CSV_COLUMNS.map((col) => {
      switch (col) {
        case 'orderId':
          return escapeCsvCell(order.orderId)
        case 'profileCode':
          return escapeCsvCell(order.profileCode)
        case 'matrixCode':
          return escapeCsvCell(order.matrixCode)
        case 'contractor':
          return escapeCsvCell(order.contractor)
        case 'alloy':
          return escapeCsvCell(order.alloy)
        case 'lengthMm':
          return escapeCsvCell(order.lengthMm)
        case 'quantity':
          return escapeCsvCell(order.quantity)
        case 'tolerancePlusMm':
          return escapeCsvCell(order.tolerancePlusMm ?? 10)
        case 'toleranceMinusMm':
          return escapeCsvCell(order.toleranceMinusMm ?? 0)
        case 'priority':
          return escapeCsvCell(order.priority)
        default:
          return ''
      }
    }).join(','),
  )
  return '\ufeff' + [header, ...rows].join('\n') + '\n'
}

export function downloadOrdersCsv(orders: OrderLine[], filename: string) {
  const blob = new Blob([serializeOrdersCsv(orders)], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

export function downloadTextFile(content: string, filename: string, mime = 'text/plain;charset=utf-8') {
  const blob = new Blob([content], { type: mime })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}
