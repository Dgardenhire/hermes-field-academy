// What Hermes 0.22 and 0.23 expect of the page, checked without Hermes.
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { practiceRoute } from '../desktop/src/loop.js'

const local = { connectionId: 'local', mode: 'local', primary: true, profile: 'default', targetProfile: 'default' }
const practice = { connectionId: 'local', mode: 'local', profile: 'academy-practice', targetProfile: 'academy-practice' }
const remote = { connectionId: 'vps-1', mode: 'remote', profile: 'vps', targetProfile: 'academy-practice' }

test('a practice profile call uses the local route that serves it', () => {
  assert.deepEqual(practiceRoute([local, remote, practice], 'academy-practice'),
    { connectionId: 'local', mode: 'local', profile: 'academy-practice', targetProfile: 'academy-practice' })
  assert.deepEqual(practiceRoute([practice], 'Academy-Practice'), practiceRoute([practice], 'academy-practice'))
})

test('a remote profile with the same name is never the target', () => {
  assert.equal(practiceRoute([local, remote], 'academy-practice'), 'academy-practice')
})

test('with no routes, or broken ones, the bare name is kept', () => {
  assert.equal(practiceRoute([], 'academy-practice-b'), 'academy-practice-b')
  assert.equal(practiceRoute(null, 'academy-practice-b'), 'academy-practice-b')
  assert.equal(practiceRoute([{ mode: 'local', targetProfile: 'academy-practice-b' }, 'x', null], 'academy-practice-b'), 'academy-practice-b')
  assert.equal(practiceRoute([{ ...practice, connectionId: ' ' }], 'academy-practice'), 'academy-practice')
})

test('the built page gives the command palette a detail function, as Hermes calls detail()', () => {
  const page = readFileSync(new URL('../desktop/plugin.js', import.meta.url), 'utf8')
  const at = page.search(/id: ["']field-academy\.open["']/)
  assert.ok(at > 0, 'the palette entry is in the built page')
  const palette = page.slice(at, at + 400)
  assert.match(palette, /detail: \(\) => /)
  assert.doesNotMatch(palette, /detail: ['"]/)
})

test('no practice-profile call goes out with a bare host.requestProfile', () => {
  for (const file of ['foundations.js', 'foundations_b.js', 'foundations_a.js']) {
    const src = readFileSync(new URL(`../desktop/src/${file}`, import.meta.url), 'utf8').replace(/^\s*\/\/.*$/gm, '')
    const calls = src.match(/host\.requestProfile\(/g) || []
    assert.ok(calls.length <= (file === 'foundations.js' ? 1 : 0), `${file} calls host.requestProfile directly ${calls.length} times`)
  }
})
