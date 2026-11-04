# Multimodal images — Xavion backend contract

Xavion's image handling lives in `xavion/core/` and is not coupled to Quickshell.
The engine exposes `chat_stream(message, ..., images=[...])` while the transport
adapters are responsible only for acquiring an image and passing it on.

## Supported inputs

- Python `bytes`: `images=[Path("screenshot.png").read_bytes()]`
- Local image path: `images=[{"path": "/tmp/screenshot.png"}]`
- Base64: `images=[{"data": "<base64>", "mime_type": "image/png"}]`
- Data URI: `images=[{"data": "data:image/png;base64,<base64>"}]`

Accepted formats are PNG, JPEG and WebP. The backend verifies file signatures,
validates MIME claims, and limits requests to four images of at most 8 MiB each.
Images are saved locally in `data/images/` with random IDs. The session JSON
contains only attachment IDs and metadata, not base64 blobs. Image files are not
automatically deleted on `/reset` or on session deletion; garbage collection can
be added with session-management support.

## Model discovery

`OllamaCapabilityProvider` calls `POST http://localhost:11434/api/show` with
`{"model": "<active_model>"}`. It considers image support confirmed only if the
returned `capabilities` list includes `vision`. Missing/unavailable capabilities
are reported as `available: false`, not guessed by the model's name.

## Quickshell protocol

```json
{"type":"chat","message":"Explain this error","images":[{"path":"/tmp/error.png"}]}
```

```json
{"type":"chat","message":"What's shown here?","images":[{"data":"<base64>","mime_type":"image/png"}]}
```

The following events include an additional `capabilities` object:

- `ready`: the initial active model
- `models`: the currently selected model
- `model_changed`: the newly selected model
- `capabilities`: response to `{"type":"get_capabilities"}`

Example capability object:

```json
{"model":"qwen3.5:9b","available":true,"vision":true,"thinking":true,"tools":true,"error":null}
```

If `capabilities.available` is false or `capabilities.vision` is false, the
frontend should disable image attachment and explain the cause. The engine
performs the same validation to protect consumers which do not check UI state.

The `done` event includes `images` metadata (IDs, MIME types and byte sizes)
for images accepted with that message, without embedding binary data.

## Direct backend usage

```python
from xavion.core.engine import XavionAI

ai = XavionAI(model_name="qwen3.5:9b")
ai.start_new_session()

if ai.get_model_capabilities().vision:
    for text in ai.chat_stream("Describe the picture", images=[{"path": "/tmp/cat.png"}]):
        print(text, end="", flush=True)
```

## Integration notes

- A Quickshell file chooser, image preview, drag-and-drop, or integration with AI
  Selection is frontend work, separate from backend image support.
- The existing terminal UI still takes text only; its engine already accepts
  images programmatically. Adding a terminal command is a separate adapter task.
- Images attached earlier in a conversation are re-sent to the model on future
  turns to preserve visual context. This can increase prompt processing and VRAM
  usage; later optimization may summarize earlier visual content.
- Successful model capability lookups are cached. `get_capabilities` forces a
  refresh, and switching models refreshes the new model's capabilities.
- For security, the bridge accepts only local paths and inline image data; it
  does not fetch remote URLs on behalf of the frontend.
