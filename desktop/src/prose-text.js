// Field Academy: the text half of Prose, with no React, so node tests can run it.
//
// A blank line starts a new paragraph, a run of lines starting "- " is a bulleted list and a run
// starting "1. " is a numbered list. Anything else is a paragraph, with single line breaks kept.

const BULLET = /^\s*[-*•]\s+(.*)$/
const NUMBER = /^\s*\d{1,2}[.)]\s+(.*)$/

/** Split text into blocks: { kind: 'p' | 'ul' | 'ol', items: [string] }. Exported for tests. */
export function proseBlocks(text) {
  const blocks = []
  for (const chunk of String(text ?? '').replace(/\r\n?/g, '\n').split(/\n[ \t]*\n/)) {
    let para = []
    let list = null
    const flushPara = () => {
      if (para.length) blocks.push({ kind: 'p', items: [para.join('\n')] })
      para = []
    }
    const flushList = () => {
      if (list) blocks.push(list)
      list = null
    }
    for (const line of chunk.split('\n')) {
      if (!line.trim()) continue
      const bullet = line.match(BULLET)
      const number = bullet ? null : line.match(NUMBER)
      if (bullet || number) {
        const kind = bullet ? 'ul' : 'ol'
        flushPara()
        if (list && list.kind !== kind) flushList()
        if (!list) list = { kind, items: [] }
        list.items.push((bullet || number)[1].trim())
      } else {
        flushList()
        para.push(line.trim())
      }
    }
    flushPara()
    flushList()
  }
  return blocks
}

/** "Example: ..." under a label that already says example reads twice. Drop the word. */
export function withoutExampleWord(text) {
  return String(text ?? '').replace(/^\s*(?:for )?example:\s*/i, '')
}
