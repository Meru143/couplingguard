# couplingguard product demo (Remotion)

A 24-second product demo that renders to MP4, WebM, or GIF. Optional —
the README in the repo root has the same content as an animated SVG that
renders inline on GitHub without any toolchain.

## Why this exists

Static SVGs (under `../../assets/`) work everywhere GitHub renders
markdown. But for marketing surfaces that *can't* render SVG — social
media previews, Marketplace hero images, conference slide decks,
Product Hunt videos — you need a real raster MP4 or GIF.

This Remotion project is the source of truth for that. Same beat
structure as `assets/animated-demo.svg`, but rendered as real video at
1080p / 30 fps with deterministic frames.

## Render the demo

```bash
cd demo/remotion
npm install
npm run build           # → out/couplingguard-demo.mp4    (~5 MB)
npm run build:gif       # → out/couplingguard-demo.gif    (720 px wide, ~12 MB)
npm run build:webm      # → out/couplingguard-demo.webm   (VP8, ~3 MB)
```

Rendering takes ~30 seconds on an M-series Mac, ~60 seconds on a typical
Linux runner.

## Preview live

```bash
npm start
```

Opens Remotion Studio in your browser at http://localhost:3000. Scrub
the timeline, edit any `.tsx` file, and the preview hot-reloads.

## Structure

```
demo/remotion/
├── package.json
├── tsconfig.json
├── remotion.config.ts
└── src/
    ├── index.ts          # registerRoot entry
    ├── Root.tsx          # Composition declaration (1920x1080, 30fps, 24s)
    ├── CouplingDemo.tsx  # The whole composition + 5 scenes
    └── theme.ts          # Color + font constants
```

Each scene is a pure function of `useCurrentFrame()`. No CSS transitions
(forbidden by Remotion). No `Math.random()` or `Date.now()` (would break
deterministic rendering).

## Customize for your fork

If you fork couplingguard and want your own demo:

1. Edit the GitHub username in `src/CouplingDemo.tsx` (search for
   `Meru143/couplingguard`).
2. Swap the file names in the `ScenePain` and `SceneComment` rows to
   match your actual coupled files (run couplingguard with `--dry-run`
   against your repo to capture real ones).
3. Re-render with `npm run build`.

## Scene timeline

| Time | Scene | What's shown |
|---|---|---|
| 0.0–3.0s | Title card | Brand + tagline + "Free / Zero-config / 5 lines" |
| 3.0–8.0s | The pain | "Two files always break together" + 3 example commits |
| 8.0–14.0s | The formula | Big monospace `score = co_changes / max(count_a, count_b)` |
| 14.0–20.0s | Rendered comment | The actual PR comment with risk badges + delta line + reviewers |
| 20.0–24.0s | CTA | Install snippet + repo URL |

Total: 24 seconds. Tuned for Twitter video (2:20 max), LinkedIn (10 min
max), and YouTube Shorts (60s max). For the YouTube Shorts cut you can
shorten the formula scene to 4s.

## Output sizes (rendered at 1920x1080 / 30 fps, ~24s)

- MP4 H.264: ~5 MB
- WebM VP8: ~3 MB
- GIF @ 720px: ~12 MB

GIF is biggest because animated GIFs are bytes-per-frame inefficient.
Prefer MP4 or WebM wherever possible.

## License

MIT. Same as couplingguard itself.
