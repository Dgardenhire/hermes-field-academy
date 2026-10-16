// A stand-in for '@hermes/plugin-sdk', so desktop/plugin.js renders in a plain browser.
//
// The names the plugin imports. Components and the data layer (the real
// @tanstack/react-query, through the import map) come from kit-sdk-stub.js.
// host records every call in window.__hostLog. The app provides the real SDK.

// Components, area ids and the data layer the kit and the plugin use: hermes-ui-kit's harness
// stand-in, copied here by the kit's build. Field Academy's own host follows.
export * from './kit-sdk-stub.js'

function atom(value) {
  return { get: () => value }
}

function log(...args) {
  ;(window.__hostLog = window.__hostLog || []).push(args)
}

export const host = {
  state: {
    gateway: atom('open'),
    profile: atom('default'),
    focusedSessionId: atom(null),
    activeSessionId: atom(null),
    busy: atom(false),
  },
  navigate(path) { log('navigate', path) },
  newChat() { log('newChat') },
  notify(input) { log('notify', input) },
  async request(method, params) {
    log('request', method, params)
    const answers = (window.__harness || {}).rpc || {}
    if (method in answers) return answers[method]
    throw new Error(`Hermes gateway unavailable (${method})`)
  },
  async profileRoutes() { return [{ profile: 'default', mode: 'local' }] },
}
