# Roadmap

Planned work, roughly in order. Not a changelog; the commit history covers what shipped.

## Next

- `/teams n`: split into n teams instead of always two
- Configurable names list with defaults, so `/teams` is useful without passing names every time
- Configurable response map: keyword to reply, with optional media
- `/gamepass` as an alias for `/gp`
- Add `/teams` to the help text
- Rename the safe-search suffix from `e` to `o`, so the letters match the API's own
  values (off, moderate, strict) instead of needing a separate explanation
- Make the default safe search level configurable rather than fixed in code

- Accept `/chart` period and interval in either order. Detect a swap, say so, and still
  return the chart instead of erroring. Needs care where a value is valid in both sets.
- Aliases and fuzzy matching for period and interval values, so `1mon` resolves to `1mo`.
  The valid keys are a closed set, so `difflib.get_close_matches` handles it without
  a model call.
- Report unknown symbols when they come from an explicit command. The inline `$SYMBOL`
  detector stays silent on purpose: it reads every message, so speaking up would mean
  replying to any `$word` in ordinary conversation.

## Later

- Natural language chart requests, for example `/chart apple last 3 months daily`.
  This is where a cheap model fallback earns its place: the input is open ended,
  unlike the fixed period and interval keys above.
- Saved text: `/save` a line, `/recall` it later
- Storage target for saved text. A database keeps everything in one place; an external
  doc API means the result stays readable and editable without building a frontend.
  Every current integration authenticates with a bearer key, so an OAuth2 provider
  would be new ground.
