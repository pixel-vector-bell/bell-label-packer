# Bell Flyer-Box Label Packer

Packs single-school 10-up "Picture Day Flyers" label sheets down to only the
labels actually needed, filling sheets continuously to eliminate waste.

**Current version: 1.0.2** (shown in the bottom-right corner of the app window)

## The rule
- 3 labels per box
- 1 box = up to 1000 flyers
- labels needed = 3 × ceil(flyers ÷ 1000)

## How to name files
Put the flyer count in the filename as `[School Name] Labels [N] Flyers`:

```
Draper ES (Canyons) Labels 350 Flyers.pdf   ->  350 flyers -> 1 box  -> 3 labels
Alpine HS Labels 2000 Flyers.pdf            -> 2000 flyers -> 2 boxes -> 6 labels
```
(Spaces or underscores around the number both work.)

## How to use (offline)
1. Double-click **BellLabelPacker.exe** (Windows) or open **BellLabelPacker.app** (Mac)
2. Click **Choose Files...** and select the label PDFs (they sort A→Z automatically)
3. Check the **preview** on the right — it shows what the first packed page will look like
4. Click **Pack Labels & Save File** — pick where to save it and name it whatever you want

Schools pack alphabetically by filename, back-to-back, so only the very last
sheet ever has empty slots. Runs 100% offline — no internet needed.

## What's new in 1.0.2
- **Choose Files** (individual PDFs) instead of choosing a whole folder — sorted alphabetically on load
- **First-page preview** on the right (72 dpi, fast) so you see the result before packing
- **Pack Labels & Save File** — choose the save location and filename yourself
- **Version number** shown in the bottom-right corner
- Updated on-screen instructions

## Build (maintainers)
Pushing to `main` triggers GitHub Actions to build BOTH a Windows `.exe` and a
Mac `.app` (see `.github/workflows/build.yml`). Download the artifacts from the
Actions run. To cut a new version, bump the `VERSION` constant at the top of
`label_packer.py` and push.
