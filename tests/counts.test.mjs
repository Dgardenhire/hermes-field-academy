// Every count on a trail agrees with its Field Record. Practice and teaching missions placed in a trail's camps
// (school.PLACEMENTS) show as waypoints but are counted apart, since the Field Record needs only the trail's own
// missions (pathways.certificate_route) or the Guide's own parts (deployer.py). Run against the real passports in
// harness/fixtures.json.

import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { countWords, trailModel } from '../desktop/src/trail.js'

const fixtures = JSON.parse(readFileSync(new URL('../harness/fixtures.json', import.meta.url), 'utf8'))
const STATES = Object.entries(fixtures.states)

test('the map count, the summit and the sentence agree on every trail of every state', () => {
  let placedSeen = 0
  for (const [name, state] of STATES) {
    const tracks = [...(state.passport?.tracks || []), ...(state.deployer?.track ? [state.deployer.track] : [])]
    for (const track of tracks) {
      const model = trailModel(track)
      const own = (track.missions || []).length
      assert.equal(model.recordTotal, own, `${name}/${track.id}: the record counts the trail's own ${own}`)
      assert.equal(model.recordTotal + model.extraTotal, model.total, `${name}/${track.id}: every waypoint counted once`)
      const remaining = track.certificate?.remaining
      if (typeof remaining === 'number' && track.certificate.status !== 'issued') {
        assert.equal(remaining, model.recordTotal - model.recordPassed, `${name}/${track.id}: "${remaining} to go" matches "${model.recordPassed} of ${model.recordTotal}"`)
      }
      const words = countWords(model)
      assert.match(words, new RegExp(`^${model.recordPassed} of ${model.recordTotal} `), `${name}/${track.id}: ${words}`)
      if (model.extraTotal) {
        placedSeen += 1
        assert.match(words, /Field Record doesn't need/, words)
      } else {
        assert.doesNotMatch(words, /placed here/, words)
      }
    }
  }
  assert.ok(placedSeen > 0, 'some fixture has placed missions')
})

test('the words for a trail with one practice mission', () => {
  const track = {
    id: 'integrator', name: 'Crossroads', missions: [1, 2, 3, 4, 5].map(n => ({ id: `m${n}`, level: 'beginner', status: n === 1 ? 'verified' : 'not_started' })),
    levels: [{ id: 'beginner', missions: ['m1', 'm2', 'm3', 'm4', 'm5'] }],
    placed: [{ id: 'f.toolsets', level: 'beginner', status: 'not_started', title: 'Tools' }],
    certificate: { status: 'in_progress', remaining: 4 },
  }
  const model = trailModel(track)
  assert.equal(model.total, 6)
  assert.equal(model.summit.remaining, 4)
  assert.equal(countWords(model), "1 of 5 missions passed, plus 0 of 1 practice mission placed here, which the Field Record doesn't need.")
  const guide = trailModel({ ...track, id: 'deployer', unit: 'parts', placed: [...track.placed, { id: 'f.teach-review', level: 'beginner', status: 'verified' }] })
  assert.equal(countWords(guide), "1 of 5 parts passed, plus 1 of 2 teaching missions placed here, which the Field Record doesn't need.")
})
