# Rung 4 — "Could you describe the damage?"

> This folder is a STARTER — it has a `# TODO(you):` hole the codelab walks you
> through. Answers: `_solutions/r4_the_photo/solution.py`.


**The failure:** the customer already SENT a photo, and support asks them to describe it.
**The fix:** multimodal memory — see the image now, store the thing (artifact), and
extract structured facts the stores can actually search.

## What's wired

`record_damage(model, damage, batch)` writes `photo_*` facts into state. The photo
itself travels as an image part in the message; adk web was launched with
`--artifact_service_uri file://…/artifacts_store` so artifacts persist as real files.

## Try it (adk web → agent `r4_the_photo`)

1. Click the attach (+) button and pick `_shared/maya/lamp_photo.jpg`
   (or photograph anything on your desk — bring-your-own-broken-thing).
2. `Here is a photo of my broken lamp. What do you see? Please record the damage.`

**What must be true:** Iris names the model AND reads the batch code **B7 off the
image**; the `record_damage` chip fires; the State tab gains
`photo_model / photo_damage / photo_batch`.

## The honesty aside

Long-term memory stores are TEXT-first. The photo is not "in memory" — the artifact
holds the photo, memory holds the extraction, and a reference ties them together.
That's the production pattern: **extract-then-store, with an artifact ref.**
(Next step up: multimodal embeddings — out of scope here.)
