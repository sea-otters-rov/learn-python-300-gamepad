// pad.js -- the one place every game reads its controls.
//
// Games stay dumb on purpose: no dead zone, no smoothing, no repeat. Whatever
// the board sends is what the game gets, so all the interesting decisions live
// in the student's Python. Slots follow the browser's "standard" layout:
//
//   axes[0], axes[1]    left stick  (-1 left/up .. +1 right/down)
//   axes[2], axes[3]    right stick
//   axes[4], axes[5]    tilt, like a third stick: right edge down is +1 in
//                       [4], far edge down is -1 in [5] (a stick pushed away)
//   buttons[0..3]       A, B, X, Y
//   buttons[9]          Start
//   buttons[10], [11]   left and right stick clicks
//   buttons[12..15]     D-pad up, down, left, right
//
// With no board the keyboard stands in, so a game can be tried without
// hardware: arrows are the left stick, W A S D the right stick, T F G H the
// tilt, Space is A, and B, X, Y and Enter are B, X, Y and Start. Press I to
// show what the game receives.

const Pad = (() => {
  const state = {
    source: "none", // "gamepad", "keyboard" or "none"
    name: "",
    axes: [0, 0, 0, 0, 0, 0],
    buttons: new Array(16).fill(false),
  };
  let previous = new Array(16).fill(false);
  const keys = new Set();

  addEventListener("keydown", (e) => {
    if (e.code.startsWith("Arrow") || e.code === "Space") e.preventDefault();
    if (e.repeat) return;
    if (e.code === "KeyI") inspector.hidden = !inspector.hidden;
    keys.add(e.code);
  });
  addEventListener("keyup", (e) => keys.delete(e.code));
  addEventListener("blur", () => keys.clear());

  const inspector = document.createElement("pre");
  inspector.hidden = true;
  inspector.style.cssText =
    "position:fixed;left:8px;bottom:8px;margin:0;padding:8px 10px;" +
    "background:#000c;color:#9f9;font:13px ui-monospace,monospace;" +
    "border-radius:6px;pointer-events:none;z-index:10";
  addEventListener("DOMContentLoaded", () => document.body.append(inspector));

  function update() {
    previous = state.buttons.slice();
    const gamepad = [...navigator.getGamepads()].find(Boolean);
    // A held key wins, so the keyboard still works with a board plugged in.
    if (gamepad && keys.size === 0) {
      state.source = "gamepad";
      state.name = gamepad.id;
      for (let i = 0; i < state.axes.length; i++) state.axes[i] = gamepad.axes[i] || 0;
      for (let i = 0; i < 16; i++) {
        state.buttons[i] = Boolean(gamepad.buttons[i] && gamepad.buttons[i].pressed);
      }
    } else {
      const key = (code) => (keys.has(code) ? 1 : 0);
      state.source = keys.size || state.source === "keyboard" ? "keyboard" : "none";
      state.name = "keyboard";
      state.axes[0] = key("ArrowRight") - key("ArrowLeft");
      state.axes[1] = key("ArrowDown") - key("ArrowUp");
      state.axes[2] = key("KeyD") - key("KeyA");
      state.axes[3] = key("KeyS") - key("KeyW");
      state.axes[4] = key("KeyH") - key("KeyF");
      state.axes[5] = key("KeyG") - key("KeyT");
      state.buttons.fill(false);
      state.buttons[0] = keys.has("Space");
      state.buttons[1] = keys.has("KeyB");
      state.buttons[2] = keys.has("KeyX");
      state.buttons[3] = keys.has("KeyY");
      state.buttons[9] = keys.has("Enter");
    }
    if (!inspector.hidden) showInspector();
    return state;
  }

  function justPressed(i) {
    return state.buttons[i] && !previous[i];
  }

  function showInspector() {
    const a = state.axes.map((v) => (v >= 0 ? "+" : "") + v.toFixed(3));
    const held = state.buttons.map((b, i) => (b ? i : null)).filter((i) => i !== null);
    inspector.textContent =
      `source   ${state.source}  ${state.name}\n` +
      `left     ${a[0]}  ${a[1]}\n` +
      `right    ${a[2]}  ${a[3]}\n` +
      `tilt     ${a[4]}  ${a[5]}\n` +
      `buttons  ${held.length ? held.join(" ") : "-"}`;
  }

  return { state, update, justPressed };
})();
