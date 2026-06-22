export function classifyOffcut(
  offcutMm: number,
  minOffcutReusableMm: number,
): { remnantMm: number; wasteMm: number } {
  if (offcutMm <= 0) {
    return { remnantMm: 0, wasteMm: 0 }
  }
  if (offcutMm >= minOffcutReusableMm) {
    return { remnantMm: offcutMm, wasteMm: 0 }
  }
  return { remnantMm: 0, wasteMm: offcutMm }
}
