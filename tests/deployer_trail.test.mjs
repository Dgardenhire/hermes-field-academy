// The Deployer trail's data and geometry, run against snapshots the real backend produced.
//
//   FA_DEPLOYER=/path/to/snapshots.json node --test tests/deployer_trail.test.mjs
//
// tests/test_deployer_ui.py builds that file from the real deployer module (a fresh start, labs passed, everything
// passed and signed, certificate issued) and runs this. Every field the trail map reads must be there, and every
// number it draws must be finite, so a gap in the snapshot cannot blank the page.

import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { MAP_FIELDS, layoutProfile, layoutRow, trailModel } from '../desktop/src/trail.js'

const STATES = JSON.parse(readFileSync(process.env.FA_DEPLOYER, 'utf8'))
const BAD = /NaN|undefined|Infinity|null/

test('there are states to check', () => {
  assert.ok(Object.keys(STATES).length >= 2)
})

for (const [name, snapshot] of Object.entries(STATES)) {
  test(`${name}: the track carries every field the trail map reads`, () => {
    const track = snapshot.track
    for (const key of MAP_FIELDS.track) assert.ok(key in track, `track.${key}`)
    for (const level of track.levels) for (const key of MAP_FIELDS.level) assert.ok(key in level, `level.${key}`)
    for (const mission of track.missions) for (const key of MAP_FIELDS.mission) assert.ok(key in mission, `mission.${key}`)
    for (const key of MAP_FIELDS.certificate) assert.ok(key in track.certificate, `certificate.${key}`)
  })

  test(`${name}: the model has four camps, nine waypoints and sensible words`, () => {
    const model = trailModel(snapshot.track)
    assert.equal(model.camps.length, 4)
    assert.equal(model.total, 9)
    assert.deepEqual(model.camps.map(c => c.short), ['Audit', 'Architect', 'Build', 'Verify'])
    assert.equal(model.unit, 'parts')
    assert.ok(model.passed >= 0 && model.passed <= 9)
    const covered = model.camps.flatMap(c => c.waypoints.map(w => w.id))
    assert.equal(new Set(covered).size, 9)
  })

  test(`${name}: the map and the profile draw finite shapes at every width`, () => {
    const model = trailModel(snapshot.track)
    for (const width of [160, 320, 560, 900, 1400]) {
      const row = layoutRow(model, width, 96, 3)
      const profile = layoutProfile(model, width, 180)
      assert.equal(row.stops.length, model.total + 2)
      for (const stop of [...row.stops, ...profile.stops]) {
        assert.ok(Number.isFinite(stop.x) && Number.isFinite(stop.y), `${name} ${width}`)
      }
      assert.ok(!BAD.test(profile.ridge), 'ridge path')
    }
  })

  test(`${name}: every part the page opens exists in the snapshot`, () => {
    for (const key of ['items', 'labs', 'brief', 'scenarios', 'deploy', 'drills', 'walkthrough', 'certificate', 'hermes_version', 'about']) {
      assert.ok(key in snapshot, key)
    }
    assert.equal(snapshot.labs.length, 4)
    assert.equal(snapshot.scenarios.length, 9)
    assert.equal(snapshot.drills.length, 3)
    for (const key of ['certifies', 'does_not', 'lifecycle_credit', 'issuer']) assert.ok(snapshot.about[key], `about.${key}`)
    assert.ok(snapshot.certificate.label)
  })
}
