// Field Academy: plain text with light structure, rendered as real paragraphs and lists.
//
// Mission and Deployer text is written in plain strings. A blank line starts a new paragraph, a run
// of lines starting "- " becomes a bulleted list and a run starting "1. " becomes a numbered list,
// so a sequence of steps reads as steps instead of one run-on paragraph. Anything else is a
// paragraph, with single line breaks kept. No HTML is ever read from the text.

import { jsx } from 'react/jsx-runtime'
import { proseBlocks, withoutExampleWord } from './prose-text.js'

export { proseBlocks, withoutExampleWord }

export const PROSE_CSS = `
.fa-prose{display:grid;gap:8px;max-width:72ch}
.fa-prose>p{margin:0}
.fa-prose>ul,.fa-prose>ol{margin:0;padding-left:22px;display:grid;gap:4px}
.fa-prose>ol>li::marker{font-variant-numeric:tabular-nums;color:var(--fa-blaze-ink,var(--hk-ink))}
.fa-prose>ul>li::marker{color:var(--fa-blaze-ink,var(--hk-ink))}
.fa-prose-line{white-space:pre-line;overflow-wrap:anywhere}
`

/** Text as paragraphs and lists. One plain paragraph renders as a single <p>, so short copy stays light. */
export function Prose({ text, className = '' }) {
  const blocks = proseBlocks(text)
  if (!blocks.length) return null
  if (blocks.length === 1 && blocks[0].kind === 'p') {
    return jsx('p', { className: `fa-prose-line ${className}`.trim(), children: blocks[0].items[0] })
  }
  return jsx('div', { className: `fa-prose ${className}`.trim(), children: blocks.map((block, index) => block.kind === 'p'
    ? jsx('p', { className: 'fa-prose-line', children: block.items[0] }, index)
    : jsx(block.kind, { children: block.items.map((item, i) => jsx('li', { children: item }, i)) }, index)) })
}
