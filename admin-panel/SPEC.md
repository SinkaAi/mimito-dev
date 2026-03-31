# Mimito Admin Panel — SPEC.md

## Context

Denis runs Mimito — a B2B garment manufacturing company. The current site at `mimito-dev` (localhost:5005) is a Flask SPA with hardcoded content and a very basic admin panel (just inquiry list). The site needs a proper CMS-style admin panel where every piece of content can be edited without touching code.

---

## What the Site Has (editable units)

### Content Sections
1. **Hero** — badge, title line 1, title line 2, description, CTA buttons, stats (3 numbers + labels), product overview card
2. **Services** — 6 service cards (icon, title, description each) — currently hardcoded in app.py
3. **"Why Mimito"** — label, title, subtitle, 4 stat blocks (number, label, description)
4. **Products** — section header, 6 product categories from DB (label, description, sizes, colors, materials)
5. **Configurator** — labels and prompts
6. **Contact** — location, email, phone, working-with text, form labels
7. **Footer** — tagline, column headers, copyright, made-with text

### Data
- **Products** — already in PostgreSQL/SQLite via `Product` model
- **Translations** — currently in `translations.py` (Python dict)
- **Services** — hardcoded Python list in `app.py`
- **Stats/config** — mixed (some in translations, some hardcoded in template)

---

## What We Will Build

A new **CMS-style admin panel** that can edit ALL content on the site, with full EN/MK language support baked in from day one.

### Architecture

```
/admin              → Admin dashboard (replaces current bare admin)
/admin/content      → All translatable text (hero, sections, footer)
/admin/products     → Product category management
/admin/services    → Service cards management
/admin/config      → Company info (email, phone, location)
/admin/inquiries    → Inquiry management (keep existing)
/api/content         → GET/PUT translatable content blocks
/api/products        → CRUD for products
/api/services        → CRUD for services
/api/config          → GET/PUT company config
```

### Database Model — ContentBlock

New table: `content_blocks`
```sql
id, block_key, en_text, mk_text, updated_at
```
`block_key` examples: `hero_title_1`, `hero_desc`, `services_title`, `contact_email`, etc.

### Database Model — ServiceBlock

New table: `service_blocks`
```sql
id, icon, title_en, title_mk, desc_en, desc_mk, sort_order
```

### Database Model — SiteConfig

New table: `site_config`
```sql
id, key, value  (e.g. "company_phone", "company_email")
```

### Key Design Decisions

1. **JSON in SQLite** — Keep it simple. Single `content_blocks` table with `block_key → en/mk text`. No complex relational CMS needed for this scale.

2. **Fallback chain** — If `content_blocks` is empty, fall back to `translations.py`. Existing translations.py becomes the default content.

3. **EN + MK side-by-side** — Admin shows both language fields next to each other. Site renders whichever language is active.

4. **Live preview** — Each section in the admin has a "preview" button that opens the site in a new tab at that section.

5. **No hardcoded content in templates** — After migration, all content comes from the DB. Templates become pure presentation.

6. **Services move to DB** — Currently hardcoded. New `service_blocks` table makes them editable.

7. **Existing data preserved** — Products, inquiries, and existing data stay intact. Only content layer changes.

### Design Language (Admin)

- Clean, professional — matches Mimito's brand (navy + gold)
- Left sidebar navigation
- Main content area with forms
- Color-coded language tabs (EN = blue, MK = green)
- Toast notifications on save
- Dark mode admin UI for comfortable long sessions

### Content Blocks to Migrate (key ones)

**Hero section:** hero_badge, hero_title_1, hero_title_2, hero_desc, hero_cta_quote, hero_cta_products, hero_stat_years, hero_stat_garments, hero_stat_export, hero_card_title, hero_status

**Stats:** why_years_num, why_years_label, why_years_desc, why_export_num, why_export_label, why_export_desc, why_moq_num, why_moq_label, why_moq_desc, why_turnaround_num, why_turnaround_label, why_turnaround_desc

**Section headers:** services_label, services_title, services_subtitle, products_label, products_title, products_subtitle, config_label, config_title, config_subtitle, contact_label, contact_title, contact_subtitle, why_label, why_title, why_subtitle

**Contact:** contact_location_val, contact_email_val, contact_phone_val, contact_working_val

**Footer:** footer_tagline, footer_col_products, footer_col_company, footer_col_contact, footer_copyright, footer_made

**Configurator:** config_product, config_size, config_color, config_material, config_quantity, config_add, config_reset, inquiry_title, inquiry_total, inquiry_submit

### Phase 1 (MVP)
- New admin shell with navigation
- Content blocks API + UI (all translatable text)
- Services management (CRUD)
- Site config (company info)
- Products management (extend existing)
- Inquiry management (keep/rebuild existing)

### Phase 2 (Future)
- Image uploads (hero images, product images)
- Multi-image galleries
- SEO fields (meta title, description per page)
- Activity log / audit trail
- User accounts for multiple staff

---

## Tech Stack
- Flask (existing)
- SQLAlchemy + SQLite (existing)
- Vanilla JS frontend (no framework — keeps it simple and dependency-light)
- Single-file HTML admin for each section
- No build step needed
