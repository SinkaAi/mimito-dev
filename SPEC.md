# Mimito — Website Spec

## Overview
B2B tailoring & garment manufacturing company website. Professional, clean, informative. A funnel for B2B orders.
**MVP Phase 1:** Landing page + Services + Inquiry form + Product teaser

## Brand
- **Name:** Mimito
- **Type:** B2B garment manufacturer
- **Tagline:** _"Precision Tailoring. Global Reach."_ (placeholder)
- **Vibe:** Clean industrial — professional, trust-building, premium without being flashy

## Design Language

### Aesthetic Direction
Clean industrial with warm accents. Structured grid. Proof-of-craftsmanship focused. Not cold — professional warmth.

### Color Palette
- **Primary:** `#0f172a` (near-black navy)
- **Accent:** `#c8a96e` (warm gold/tan — tailor thread color)
- **Accent alt:** `#e8d5b7` (light cream)
- **Background:** `#ffffff` (white) + `#f8f7f4` (warm off-white sections)
- **Text:** `#1a1a2e` (body), `#6b7280` (secondary)
- **Dark sections:** `#0f172a` background, white text

### Typography
- **Headings:** Inter (700, 600) — clean, professional, geometric
- **Body:** Inter (400) — readable, modern
- **Accent text:** Inter (500) — for labels and small caps

### Layout
- Max-width: 1200px centered
- Section padding: 80px vertical
- Grid: 12-column on desktop, responsive
- Generous white space between sections

### Motion
- Subtle fade-in on scroll (Intersection Observer)
- Smooth hover transitions on cards/buttons (200ms ease)
- No flashy animations — professional restraint

## Pages / Sections

### 1. Header
- Logo (left): "MIMITO" in bold uppercase
- Nav (right): Services | Products | About | Contact
- Sticky on scroll with subtle shadow

### 2. Hero Section
- Full-width, dark background (#0f172a)
- Large headline: "Professional Tailoring. Made in Macedonia."
- Sub-headline: What Mimito does (custom garments, B2B, any quantity)
- Two CTAs: "Request a Quote" (primary gold) + "View Products" (ghost button)
- Background: subtle fabric texture or clean dark gradient

### 3. Services Section
- Light background (#f8f7f4)
- Section title: "What We Produce"
- 6-8 service cards in a 3-column grid:
  - Custom Shirts
  - Custom Pants & Trousers
  - Blazers & Suits
  - Women's Apparel
  - Bags & Accessories
  - Workwear & Uniforms
- Each card: icon + title + short description
- "Configure & Order" link per card (leads to product section)

### 4. Why Mimito Section
- Dark background (#0f172a)
- 3-4 value propositions in a row:
  - Years of experience
  - Export to Germany & EU
  - Any quantity (MOQ flexible)
  - Fast turnaround
- Clean, data-forward layout with large numbers

### 5. Products Teaser Section
- Light background
- "Our Products" — 4-6 product category cards (placeholder images)
- Each: product image + name + "Configure" button
- Opens the product configurator

### 6. Product Configurator (Phase 1 — simplified)
- Modal or inline section
- Select: Product category → Size range → Color → Material
- Add to inquiry list
- Inquiry list shows all configured items
- "Submit Inquiry" → sends email with all items + customer info

### 7. Contact / Inquiry Form
- Dark background
- Title: "Ready to Start?" or "Get Your Quote"
- Form fields:
  - Company Name
  - Contact Name
  - Email
  - Phone Number
  - Message / Special Requirements
  - Product Inquiry List (from configurator)
- Submit → sends email to Mimito

### 8. Footer
- Dark background
- Company name + short description
- Quick links: Services | Products | Contact
- Contact info: Phone, Email, Location (Macedonia)
- Copyright

## Tech Stack
- **Flask** backend (Python)
- **HTML/CSS/JS** (custom, no heavy frameworks)
- **Email:** Flask-Mail or SMTP
- **Data:** JSON files for MVP
- **Host:** Can deploy to Render later

## Configurator (Phase 1 Detail)
**Product options:**
- Categories: Shirts, Pants, Blazers, Women's Wear, Bags, Workwear
- Sizes: XS, S, M, L, XL, XXL, Custom (+ size chart link)
- Colors: Basic palette (8-10 options per product)
- Materials: 3-5 options per product (Cotton, Polyester, Mixed, Premium Cotton, etc.)
- Quantity: number input

**Flow:**
1. Select product → fills in available options
2. Configure → items added to inquiry list
3. Fill contact form
4. Submit → email to Mimito with inquiry list + contact details

## Phases
- **Phase 1 (MVP now):** Landing + Services + Why Mimito + Contact/Inquiry form + 1 configurator demo
- **Phase 2:** Full product catalog with images + working configurator
- **Phase 3:** Full cart/inquiry list + email automation
- **Phase 4:** Gallery, testimonials, client logos
