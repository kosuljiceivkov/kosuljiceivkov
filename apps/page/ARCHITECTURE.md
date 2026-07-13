# Visual Page Builder — Forward-Looking Architecture

Locked product spec: structure-first Elementor-lite visual builder on `iv_page_v1`.

This document records **future-capability data shapes** that Phase A+ must not block.
These models are **not implemented in Phase A**.

## Company Sections (future)

Support two insertion modes without schema redesign:

| Mode | Behavior | `insertion_mode` |
|------|----------|------------------|
| Clone (v1) | Copy section JSON into the page; independent edits | `clone` |
| Linked (future) | Page section references canonical company section | `linked` |

### `CompanySection` (future model)

```text
id                  UUID PK
name                CharField
slug                SlugField (unique)
description         TextField (blank)
thumbnail_asset_id  FK MediaAsset (nullable)
section_snapshot    JSONField  — canonical iv_page_v1 section object
template_id         CharField (provenance)
variant_id          CharField (provenance)
template_version    PositiveIntegerField
default_insertion_mode  CharField choices: clone | linked (default clone)
is_archived         BooleanField
created_by          FK User
created_at / updated_at
```

### Page section provenance (stored inside section JSON)

```json
{
  "provenance": {
    "company_section_id": "uuid",
    "insertion_mode": "clone"
  }
}
```

**Linked mode (future):** renderer/editor resolve `company_section_id → section_snapshot`,
then apply optional `overrides` JSON on the page instance. Clone mode ignores
`company_section_id` after insert (snapshot is copied). Keeping `provenance` on
every inserted section makes mode migration possible later.

## Media Library (future)

Global asset store; page blocks reference assets by ID.

### `MediaAsset` (future model)

```text
id                  UUID PK
file                ImageField (blog_images storage)
title               CharField (blank, searchable)
alt_text_default    CharField (blank, searchable)
original_filename   CharField
file_size           PositiveIntegerField
width / height      PositiveIntegerField (nullable)
folder_id           FK MediaFolder (nullable) — folders v2
uploaded_by         FK User (nullable)
created_at / updated_at
deleted_at          DateTimeField (nullable, soft delete)
```

### `MediaFolder` (future)

```text
id, name, parent_id (self FK nullable), slug, path (materialized)
```

### `MediaTag` + `MediaAssetTag` (future M2M)

Enables tag filtering without changing `MediaAsset`.

### `MediaAssetRecentUse` (future)

```text
user_id, asset_id, last_used_at  — unique (user_id, asset_id)
```

Recently-used is a **usage index**, not a field on `MediaAsset`.

### Block image contract (from Phase A)

```json
{
  "type": "image",
  "attrs": {
    "media_asset_id": "uuid-or-null",
    "src": "/media/...",
    "alt": "",
    "caption": ""
  }
}
```

`media_asset_id` is preferred when the library exists. `src` remains a fallback
for direct uploads and backward compatibility. Renderer resolves asset ID → URL.

## Section revision history (future)

```text
PageSectionRevision
  post_id           FK BlogPost
  section_id        CharField (stable section.id in body_page)
  revision_number   PositiveIntegerField
  section_snapshot  JSONField
  created_by        FK User
  created_at        DateTimeField
  source            CharField (autosave | restore | manual)
```

Restore writes a new revision entry; never mutates history in place.
