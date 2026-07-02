# Piper voices

Not checked into git - these are large ONNX model files, and Piper makes them trivial to re-fetch.

```bash
python -m piper.download_voices --download-dir backend/app/data/voices hi_IN-pratham-medium en_US-lessac-medium
```

`app/speech/tts.py` maps BFT language codes to voice names (`hi` → `hi_IN-pratham-medium`, everything else → `en_US-lessac-medium`). To add another of the 22 regional voices the exec summary called for, run `python -m piper.download_voices` with no arguments to list what's available, download it into this directory, and add it to `_VOICE_BY_LANGUAGE` in `tts.py`.
