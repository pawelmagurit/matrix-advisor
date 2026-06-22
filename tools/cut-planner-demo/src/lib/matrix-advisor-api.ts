export const MATRIX_ADVISOR_API =
  import.meta.env.VITE_MATRIX_ADVISOR_API ?? '/api/matrix-advisor'

export interface MatrixRecord {
  matrix_id: string
  profile_id: string
  supplier_name: string | null
  die_type: string | null
  cavity_count: number | null
  press_code: string | null
  effectiveness_pct: number | null
  correction_count: number | null
  interruption_count: number | null
}

export interface SimilarProfile {
  profile_id: string
  display_name: string | null
  rank: number
  score: number
  matrices: MatrixRecord[]
}

export interface AdvisoryResponse {
  query_profile_id: string
  query_display_name: string | null
  method: string
  query_matrices: MatrixRecord[]
  similar: SimilarProfile[]
  recommendation_note: string
}

export interface ProfileListItem {
  profile_id: string
  display_name: string | null
  matrix_count: number
}

export async function fetchHealth(): Promise<{ status: string; profiles_indexed: number }> {
  const res = await fetch(`${MATRIX_ADVISOR_API}/health`)
  if (!res.ok) throw new Error(`API ${res.status}`)
  return res.json()
}

export async function fetchProfiles(): Promise<ProfileListItem[]> {
  const res = await fetch(`${MATRIX_ADVISOR_API}/profiles`)
  if (!res.ok) throw new Error(`API ${res.status}`)
  const data = await res.json()
  return data.profiles
}

export async function fetchAdvisory(
  profileId: string,
  method: 'embedding' | 'geometric' = 'embedding',
  topK = 8,
): Promise<AdvisoryResponse> {
  const params = new URLSearchParams({ method, top_k: String(topK) })
  const res = await fetch(`${MATRIX_ADVISOR_API}/profiles/${encodeURIComponent(profileId)}/advisory?${params}`)
  if (!res.ok) {
    const text = await res.text()
    throw new Error(text || `API ${res.status}`)
  }
  return res.json()
}

export function pictogramUrl(profileId: string): string {
  return `${MATRIX_ADVISOR_API}/profiles/${encodeURIComponent(profileId)}/pictogram`
}
