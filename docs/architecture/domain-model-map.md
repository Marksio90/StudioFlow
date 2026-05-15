# Domain Model Map

## VideoIdea → ContentIdea migration

### Phase 1 (implemented on May 15, 2026)
- Introduce `ContentIdea` as the canonical domain model name.
- Keep physical database table name stable as `video_ideas`.
- Keep compatibility aliases/wrappers for `VideoIdea` naming in ORM, schema, repository, and service layers.

### Phase 2 (optional, future)
If table-level naming alignment is needed, perform a separate migration:
1. Rename table `video_ideas` to `content_ideas` **or** create `content_ideas` and migrate rows.
2. Add compatibility view named `video_ideas` selecting from `content_ideas` for backward compatibility.
3. Keep write-path compatibility by using DB triggers/rules or a dual-write strategy during transition.
4. Remove compatibility view once all callers fully migrate.

### Deprecation timeline
- **Now (May 15, 2026):** `ContentIdea*` names are preferred.
- **+1 release:** emit deprecation warnings in API/docs/changelogs for `VideoIdea*` names.
- **+2 releases:** freeze new usage of `VideoIdea*` names in internal code.
- **+3 releases:** remove `VideoIdea*` aliases/wrappers after consumer migration completion.
