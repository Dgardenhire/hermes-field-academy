// Pure helpers for Foundations missions 1, 2, 4, 5 and 6 (0.9 M6, part A). No imports, so node tests load it as is.

/** Plain checks on a note before it is sent; the backend checks again. */
export function fieldProblems(fields, form) {
  const out = []
  for (const f of fields || []) {
    const v = form[f.id]
    const empty = v === undefined || v === null || (typeof v === 'string' && !v.trim())
    if (empty) {
      if (f.required !== false) out.push(`${f.label}: this is needed.`)
      continue
    }
    if (f.kind === 'int' && !/^\d[\d,]*$/.test(String(v).trim())) out.push(`${f.label}: a whole number.`)
    if (['text', 'textarea', 'lines'].includes(f.kind || 'text') && String(v).trim().length < (f.min || 1)) out.push(`${f.label} is too short.`)
  }
  return out
}

/** A description as the skills index shows it, clipped the way Hermes 0.22.6 and later do (agent/skill_utils.py,
 *  clip_skill_description): up to 60 characters as written; longer, the last whole word in the first 58, trailing
 *  punctuation dropped, plus three dots. One long word with no space is cut at 57. */
export function cutWords(description) {
  const text = String(description || '').trim().split(/\s+/).join(' ')
  if (text.length <= 60) return text
  const head = text.slice(0, 58)
  const boundary = head.search(/\s\S*$/)
  if (boundary <= 0) return `${text.slice(0, 57)}...`
  return `${head.slice(0, boundary).replace(/[\s.,;:\-\u2013\u2014(/]+$/, '')}...`
}
