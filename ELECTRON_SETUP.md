# Race Oracle – Electron Desktop App Setup ✅

Your React + Vite app is now a **native desktop application** using Electron!

## What's New

✨ **Electron Integration:**
- `public/main.js` – Electron main process (window creation, menus)
- `public/preload.js` – Security context bridge
- Updated `package.json` with Electron build config
- `concurrently` runs Vite dev server + Electron together

🎯 **App Features:**
- 1600x900 window with min size 1000x600
- Dark menu bar with reload, DevTools, zoom controls
- Auto-opens DevTools in development (toggle in main.js)
- Proper app lifecycle (quit, reopen on macOS)

## Commands

### Development
```bash
npm run dev
```
Starts Vite + Electron together. App opens as native window.

### Build Desktop App

**macOS (DMG + ZIP):**
```bash
npm run build:electron
```
Creates: `dist/Race Oracle-0.0.1.dmg` + `.zip`

**Windows (NSIS Installer):**
```bash
npm run build:electron
```
Creates: `dist/Race Oracle Setup 0.0.1.exe`

**Linux (AppImage):**
```bash
npm run build:electron
```
Creates: `dist/Race Oracle-0.0.1.AppImage`

### Pack for testing (no installer)
```bash
npm run pack
```

### Only Vite dev (no Electron)
```bash
npm run dev:vite
```

### Only Electron (requires built dist)
```bash
npm run electron
```

## Build Config (in package.json)

```json
"build": {
  "appId": "com.raceoracle.app",
  "productName": "Race Oracle",
  "files": ["dist/**/*", "public/main.js", "public/preload.js"],
  "mac": { "target": ["dmg", "zip"] },
  "win": { "target": ["nsis"] },
  "linux": { "target": ["AppImage"] }
}
```

Customize icon: Replace `public/icon.png` (512x512 PNG or .icns for Mac).

## File Structure

```
race-oracle-frontend-Sim/
├── public/
│   ├── main.js          (Electron main process)
│   ├── preload.js       (Context bridge)
│   └── icon.png         (App icon)
├── src/
│   ├── components/      (React components)
│   ├── styles/          (CSS + variables)
│   ├── App.jsx
│   └── main.jsx
├── dist/                (Built app assets — created on build)
├── package.json         (with Electron config + build)
└── vite.config.js       (Vite + Electron build settings)
```

## Development Tips

1. **Auto-reload on code change**: Vite hot-reloads, Electron watches automatically
2. **DevTools**: Press `Cmd+Alt+I` (Mac) or `Ctrl+Shift+I` (Win/Linux)
3. **Main process changes**: Restart dev server to reload main.js
4. **Icons**: Use transparent PNG for best macOS appearance

## Next Steps

- [ ] Add `public/icon.png` (512x512)
- [ ] Test on target OS before releasing
- [ ] Sign app for distribution (macOS code signing, Windows signing)
- [ ] Set up CI/CD for automated builds

## Troubleshooting

**App won't start?**
- Check `npm run dev:vite` works first (Vite alone)
- Check `npm run electron` works with built dist

**Build fails?**
- Run `npm run build` first to generate `dist/`
- Check Node version: `node --version` (should be 14+)

**Permission denied on macOS?**
- Run: `chmod +x dist/*.app/Contents/MacOS/*`

---

**You now have a professional desktop app!** 🚀

Package it with `npm run build:electron` and distribute the `.dmg`, `.exe`, or `.AppImage`.
