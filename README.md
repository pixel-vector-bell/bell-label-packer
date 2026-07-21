# Bell Flyer-Box Label Packer

Packs single-school 10-up "Picture Day Flyers" label sheets down to only the
labels actually needed, filling sheets continuously to eliminate waste.

## The rule
- 3 labels per box
- 1 box = up to 1000 flyers
- labels needed = 3 × ceil(flyers ÷ 1000)

## How to name files
Put the flyer count in the filename as `_<N>_Flyers.pdf`:

```
Teton_HS_Labels_2000_Flyers.pdf      -> 2000 flyers -> 2 boxes -> 6 labels
Apple_Valley_ES_Labels_800_Flyers.pdf ->  800 flyers -> 1 box  -> 3 labels
```

## How to use (Windows, offline)
1. Double-click **BellLabelPacker.exe**
2. Click **Choose Folder...** and pick the folder with your label PDFs
3. Click **Pack Labels**
4. Open `Packed_Box_Labels.pdf` in that folder and print it

Schools pack alphabetically by filename, back-to-back, so only the very last
sheet ever has empty slots. Runs 100% offline — no internet needed.
