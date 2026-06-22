const BASE = '/api/v1'

export type ProfileListItem = {
  profile_id: string
  display_name: string | null
  owner_contractor: string | null
  masa_g_m: number | null
  wall_thickness_mm: number | null
  has_pictogram: boolean
  matrix_count: number
  best_effectiveness_pct: number | null
  supplier_names: string | null
}

export type MatrixRow = {
  matrix_id: string
  supplier_name: string | null
  die_type: string | null
  cavity_count: number | null
  status_code: string | null
  status_label: string | null
  effectiveness_pct: number | null
  successful_runs: number | null
  failed_runs: number | null
  die_wear_used: number | null
  die_wear_remaining: number | null
}

export type ProfileDetail = {
  profile_id: string
  display_name: string | null
  owner_contractor: string | null
  masa_g_m: number | null
  wall_thickness_mm: number | null
  has_pictogram: boolean
  source_system: string | null
  matrices: MatrixRow[]
}

export type BrowseResponse = {
  items: ProfileListItem[]
  total: number
  page: number
  page_size: number
  pages: number
}

export type Stats = {
  profiles: number
  pictograms: number
  matrices: number
  suppliers: number
  owners: number
  avg_effectiveness_pct: number | null
  source: string
  index_embedding_count?: number
  index_geometric_count?: number
  index_ok?: boolean
  index_warning?: string | null
}

export type AdvisoryResponse = {
  query_profile_id: string
  query_display_name: string | null
  method: string
  query_matrices: MatrixRow[]
  similar: Array<{
    profile_id: string
    display_name: string | null
    rank: number
    score: number
    matrices: MatrixRow[]
  }>
  recommendation_note: string
}

export type UploadQueryResponse = AdvisoryResponse & {
  query_preview: string
  quality_flags?: string[]
  index_warning?: string
}

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`)
  if (!res.ok) {
    const text = await res.text()
    throw new Error(text || res.statusText)
  }
  return res.json() as Promise<T>
}

export function pictogramUrl(profileId: string, raw = true) {
  return `${BASE}/profiles/${encodeURIComponent(profileId)}/pictogram?raw=${raw}`
}

export const fetchHealth = () => get<Stats & { status: string; profiles_indexed: number }>('/health')
export const fetchStats = () => get<Stats>('/stats')
export const fetchSuppliers = () => get<{ suppliers: string[] }>('/filters/suppliers')
export const fetchOwners = () => get<{ owners: string[] }>('/filters/owners')
export const fetchStatuses = () =>
  get<{ statuses: Array<{ code: string; label: string; count: number }> }>('/filters/statuses')

export function fetchBrowse(params: Record<string, string | number | boolean | undefined>) {
  const q = new URLSearchParams()
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== '' && v !== null) q.set(k, String(v))
  }
  return get<BrowseResponse>(`/profiles?${q}`)
}

export const fetchProfile = (id: string) =>
  get<ProfileDetail>(`/profiles/${encodeURIComponent(id)}`)

export const fetchAdvisory = (id: string, method: string, topK: number) =>
  get<AdvisoryResponse>(
    `/profiles/${encodeURIComponent(id)}/advisory?method=${method}&top_k=${topK}`,
  )

export async function fetchQueryByImage(
  file: File,
  method: string,
  topK: number,
  label?: string,
): Promise<UploadQueryResponse> {
  const form = new FormData()
  form.append('file', file)
  form.append('method', method)
  form.append('top_k', String(topK))
  if (label) form.append('label', label)

  const res = await fetch(`${BASE}/query/by-image`, { method: 'POST', body: form })
  if (!res.ok) {
    let msg = res.statusText
    try {
      const body = await res.json()
      msg = body.detail ?? msg
    } catch {
      msg = await res.text().catch(() => msg)
    }
    throw new Error(typeof msg === 'string' ? msg : JSON.stringify(msg))
  }
  return res.json() as Promise<UploadQueryResponse>
}
