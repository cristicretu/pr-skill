# Capturing stills and motion, by platform

The same principles hold on every platform. Only the tools change.

- **Same input, two builds.** Render `main` and the branch from the identical fixture and scripted input. Get `main` with `git worktree add ../<repo>-main origin/main` and run it on another port or simulator. If the feature can be switched off (a flag, `reduce_motion`, an env var), rendering the branch with it off is also acceptable, as long as the caption says so.
- **Freeze time, then step it.** Frame N must be exactly t = N × step after the input, every run. Recording wall-clock time gives you dropped frames, jitter, and a GIF that doesn't match what the code does.
- **Fix everything else too:** viewport and device scale (capture at 2x), color scheme, fonts loaded, locale and timezone, the fake "now" (use a fixed date), random seeds, the status bar and clock on mobile, and the text caret (hide it).
- **Draw what a headless render can't show.** Offscreen renders have no mouse pointer, no touch indicator and often no window vibrancy. Draw the pointer or touch dot onto the frame at the real event position (the #491 rewrite did this), and mention render artifacts in a small note under the images ("the light sidebar looks flat grey because a headless render has no vibrancy").
- **Crop to what matters.** Capture the element or region, not the whole desktop. Use full-window shots only when context is the point.
- **Check the premise first.** Capture `main` before you build, and confirm the problem looks the way it was described.

Every recipe below ends in a directory of `frame_%04d.png` files or a single PNG. From there, `compare.py`, `strip.py` and `gif.sh` do the rest.

---

## Web: any framework (Next.js, React, Vue, Svelte, Remix, Astro, plain HTML)

Use Playwright. If the project doesn't already have it: `pnpm add -D playwright && pnpm exec playwright install chromium` (or npm/yarn/bun).

### Stills

```sh
node scripts/web-frames.mjs --still --url http://localhost:3000/checkout \
  --clip "[data-testid=cart]" --width 390 --height 844 --scheme dark --out after-dark.png
```

`--clip` crops to an element, and `--setup "click:#open-menu"` puts the page into a state first. Take the shot in both `--scheme light` and `--scheme dark` when the UI themes, and at the widths that matter (390 for a phone, 1280 for desktop).

### Motion: stepped frames

```sh
node scripts/web-frames.mjs --url http://localhost:3000/ --out frames/ \
  --clip "#sheet-root" --action "click:[data-open-sheet]" --frames 30 --step 8 \
  --probe "getComputedStyle(document.querySelector('#sheet')).transform"
```

How it works, and why it's exact:
- `page.clock.install()` and then `pauseAt()` fake and freeze `Date`, timers, `requestAnimationFrame` and `performance.now`. Each frame runs `clock.runFor(step)`. That drives JS animation libraries (Motion/framer-motion, react-spring, GSAP, hand-written rAF).
- CSS transitions, CSS keyframes and `element.animate()` run on the compositor's own timeline, which the fake clock doesn't touch. So each frame, every `document.getAnimations()` entry is paused and its `currentTime` set to its own elapsed time.
- `--probe` logs a value per frame (a transform, an opacity, a scroll offset) to `probe.txt`. Use it to confirm the curve numerically and to feed `strip.py --labels`.

Tested behaviour: a 240 ms `cubic-bezier(.2,.8,.2,1)` transition stepped at 16 ms gives 0, 75, 143, 191 … 280 px, identical on every run.

For complex flows, pass `--action file:flow.mjs` with `export default async (page) => { … }` (drag, type, wait for a request).

### Running two builds

```sh
git worktree add ../app-main origin/main && (cd ../app-main && pnpm i && pnpm dev --port 3001)
pnpm dev --port 3000
```

For Next.js, capture against `next build && next start` when the change affects performance, hydration or loading states: dev mode has overlays and is slower. Hide the Next.js dev indicator (`devIndicators: false` in `next.config`) or crop it out.

### Loading states, errors, slow networks

- Pin API responses with `page.route('**/api/orders', r => r.fulfill({ json: fixture }))`, or use MSW if the repo already does.
- To show a loading state, hold the route open: `page.route(url, async r => { await gate; r.fulfill(...) })`. Take the skeleton shot, release the gate, then take the loaded shot. A layout-shift PR is best shown as skeleton and loaded frames stacked with a guide line.
- Throttle with CDP: `const cdp = await context.newCDPSession(page); await cdp.send('Network.emulateNetworkConditions', { offline: false, latency: 400, downloadThroughput: 50000, uploadThroughput: 20000 })`.

### When only a browser-automation tool is available (Chrome DevTools MCP, claude-in-chrome)

- Take screenshots at fixed viewport sizes.
- Slow every animation down with CDP `Animation.setPlaybackRate({ playbackRate: 0.1 })`, or in-page with `document.getAnimations().forEach(a => a.playbackRate = 0.1)`, then take screenshots at intervals. It's less exact than stepping, so caption it as "played at 10% speed".
- Take a performance trace for jank claims, and report long frames and layout-shift scores as numbers.

### Storybook

If the repo has Storybook, a story is often the best fixture: every state on one page. Point `web-frames.mjs` at `http://localhost:6006/iframe.html?id=<story-id>&viewMode=story`.

---

## iOS / iPadOS (SwiftUI, UIKit), and React Native / Expo / Flutter on iOS

### Simulator setup that makes shots clean

```sh
xcrun simctl boot "iPhone 16 Pro"            # pick one device and keep it for every shot
xcrun simctl status_bar booted override --time "9:41" --batteryState charged --batteryLevel 100 \
  --cellularMode active --cellularBars 4 --wifiBars 3
xcrun simctl ui booted appearance dark        # or light; shoot both when the UI themes
xcrun simctl ui booted content_size extra-extra-large   # Dynamic Type edge cases
xcrun simctl io booted screenshot after-dark.png
```

Build and install with `xcodebuild -scheme App -destination 'platform=iOS Simulator,name=iPhone 16 Pro' -derivedDataPath build build`, then `xcrun simctl install booted build/Build/Products/Debug-iphonesimulator/App.app`. For `main`, build from the worktree into a different derived-data path, and give it a different bundle id or install it in turn.

### Put the app into the state you want (fixture launch)

Add a DEBUG-only launch argument that loads fixture data and opens the right screen, so no tapping is needed:

```sh
xcrun simctl launch booted com.acme.app -PRFixture checkout-long-names -PRScreen cart
```

```swift
#if DEBUG
if let fixture = UserDefaults.standard.string(forKey: "PRFixture") { Store.loadFixture(named: fixture) }
#endif
```

(Launch arguments of the form `-Key value` land in `UserDefaults`.) Remove it before committing, unless the repo wants it kept as a demo seam.

### Motion

- **Deterministic frames (preferred).** Pause Core Animation and scrub it. In a DEBUG hook, after triggering the transition: `window.layer.speed = 0` and then, per frame, `window.layer.timeOffset = t` and take a screenshot. This scrubs UIKit animations and anything else backed by Core Animation. SwiftUI animations mostly are, but verify with a strip, because some are driven per frame by SwiftUI itself.
- **SwiftUI views as a pure function of progress.** When the animated view takes its progress as an input (a `phase`, an `Animatable` value), render each step offscreen with `ImageRenderer(content: view(progress: p)).uiImage`, either from a unit test or a preview-only harness. This is the most exact option and needs no simulator input.
- **Snapshot tests.** If the repo uses swift-snapshot-testing, add a snapshot per state and reuse the recorded PNGs as the before and after images.
- **Real-time recording (fallback).** `xcrun simctl io booted recordVideo --codec h264 take.mov`, perform the interaction, press Ctrl-C, then extract frames with `ffmpeg -i take.mov -vf fps=60 frames/frame_%04d.png`. To get real slow motion, launch with a DEBUG hook that sets `window.layer.speed = 0.1` (the simulator's Debug > Slow Animations toggle does the same by hand), and caption it with the speed factor.
- **Gestures.** Drive them with XCUITest (`app.swipeUp(velocity:)`, `press(forDuration:thenDragTo:)`) so the input is identical on both builds.

### React Native / Expo / Flutter

Use the simulator setup above for iOS and the emulator setup below for Android. For fixtures, use a dev-only deep link (`myapp://pr/checkout-long-names`) or a launch env. For motion, Reanimated and Animated run on the UI thread in real time, so record and slow down (RN: `Animated` has no global scale, so set the durations with a DEBUG multiplier); Flutter has `timeDilation = 10.0` from `package:flutter/scheduler.dart`, and golden tests (`matchesGoldenFile`) with `tester.pump(Duration(milliseconds: 8))` give exact stepped frames.

---

## Android (Views, Jetpack Compose)

```sh
adb shell settings put global sysui_demo_allowed 1
adb shell am broadcast -a com.android.systemui.demo -e command clock -e hhmm 0941
adb shell am broadcast -a com.android.systemui.demo -e command battery -e level 100 -e plugged false
adb shell cmd uimode night yes                     # dark theme
adb exec-out screencap -p > after.png
adb shell settings put global animator_duration_scale 10   # 10x slow motion for recordings; set back to 1
adb shell screenrecord /sdcard/take.mp4 && adb pull /sdcard/take.mp4
```

For deterministic Compose frames: `composeTestRule.mainClock.autoAdvance = false`, trigger the change, then loop over `mainClock.advanceTimeBy(8)` and `onRoot().captureToImage()`. Paparazzi or Roborazzi render states on the JVM with no device.

---

## Desktop apps

- **Electron / Tauri web views.** Use Playwright's `_electron.launch({ args: ['.'] })` for Electron and the same frame stepping as for web. For Tauri, point Playwright at the dev server URL.
- **macOS native (AppKit/SwiftUI).** `screencapture -l <windowID> -o shot.png` when screen capture is permitted (`-o` drops the shadow). Agent sessions often can't capture the screen. Then render offscreen: `NSView.bitmapImageRepForCachingDisplay(in:)` plus `cacheDisplay(in:to:)`, or `ImageRenderer` for SwiftUI, from a test or DEBUG hook. The Core Animation scrub above works here too (`layer.speed = 0`, `timeOffset = t`).
- **Custom renderers (GPU, game engines, GPUI, Skia, canvas).** Render offscreen from a test with an injected clock and save PNGs. This is what the diri PRs did (see `examples.md`). The pattern: make the animation a pure function of elapsed time, add a builder or test seam to inject the clock, and write an ignored test that steps it and saves `frame_%04d.png`. If it's cheap to keep, commit it as a documented fixture (for example `render_theme_fade_frames`) so the next PR can reuse it.

---

## Terminal UIs and CLIs

- **Static output.** Paste the before and after as fenced code blocks. That's the most honest option and it stays searchable. Use a `diff` fence to show changed lines in color.
- **Styled output, TUIs, progress bars.** Record with a script, not by hand. [VHS](https://github.com/charmbracelet/vhs) (`brew install vhs`) turns a `.tape` file (Type, Enter, Sleep, Set Width/Height/Theme) into a GIF or PNG frames reproducibly: run the same tape against the `main` build and the branch build. Alternatively, run the program under a pty (`script`, Python's `pty`), capture its ANSI output, and render it through a terminal renderer the repo already has.
- **Timing-sensitive output** (spinners, streaming): drive the program with a fake clock or env knob if one exists, otherwise record with VHS and caption the real timings.

---

## Checklist before composing

- [ ] `main` and branch captured with the same fixture, input, size, scale, theme and clock
- [ ] Every state the PR claims to change is captured, plus the awkward inputs
- [ ] Both color schemes if the UI themes; both sizes if it's responsive
- [ ] Motion stepped at a known interval (the caption will say "one tile per 8 ms")
- [ ] You opened and looked at the raw frames yourself
