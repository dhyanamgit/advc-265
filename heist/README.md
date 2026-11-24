# The Perfect Heist (animated cartoon)

A 44-second cartoon generated entirely with code. A masked robber hits the
Grand Bank; the cashier outsmarts him with five plot twists (silent alarm,
dye pack, broccoli swap, police, and a final "it was a drill" reveal).
Purely fictional and comedic — no violence, no real-world how-to.

## Files

- `make_video.py` — generator script (Pillow draws every frame, ffmpeg encodes)
- `heist.mp4` — rendered video (H.264, 44 s; compact 480x270/10fps encode — run the script for full 960x540/24fps)

## Regenerate

```bash
pip install pillow imageio-ffmpeg
python3 make_video.py
```

Writes `frames/`, `heist.mp4`, and `heist_preview.gif` next to the script.
Edit the `SCENES` list and scene functions to change the story.
