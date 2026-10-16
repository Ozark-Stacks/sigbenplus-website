# Signature Benefits Plus — website rebuild

Static, dependency-free replacement for the Carrd single-page site at sigbenplus.com.
Five pages, one stylesheet, one small script. No build step is required to host it.

## Layout

```
site/                  ← deploy this folder as the web root
  index.html           Home
  group-benefits/      Group employee benefits
  fractional-hr/       Fractional HR
  about/               Team
  contact/             Contact form + details
  404.html, robots.txt, sitemap.xml, .htaccess
  assets/css/styles.css, assets/js/main.js, assets/img/…
tools/build_site.py    Optional generator: edit the shared header/footer or page copy here and re-run
docs/seo-audit.html    The SEO and site audit of the previous site
```

## Preview locally

```bash
python -m http.server 8787 --directory site
```

Then open http://localhost:8787/. Pages use root-relative paths (`/assets/...`), so
open them through a server rather than double-clicking the HTML files.

## Regenerate pages after editing copy

```bash
python tools/build_site.py
```

## The hero dial

The homepage hero is a 12-month "renewal dial" drawn as inline SVG by `dial_svg()` in
`tools/build_site.py`. The lime arc is the 90-day window before the renewal month;
`assets/js/main.js` rotates it when a visitor picks a month (from the dropdown or by
clicking a segment) and prefills the contact form with that month. No images, no
library; it weighs about 6 KB. On load a radar sweep lights the ring, the arc draws
itself and the start dot pops; after about three seconds `main.js` adds `is-ready` so
later month changes only spring-rotate the arc (always the short way round).

## Header and partner section

A navy utility bar carries the phone number, email and the **Client login** menu
(Employee Navigator, Zywave). The sticky header below it shows the logo at 66 px with
the full name "Signature Benefits Plus" beside it. The homepage has a "platforms behind
the service" band with the Employee Navigator and Zywave logos (white marks from the old
site, in `assets/img/partners/`) and login buttons. CSS and JS links carry a content-hash
`?v=` so browsers refetch them after a rebuild.

## Contact page

The contact page opens on the same navy band as the home page with call, email and
visit tiles (the visit tile links to Google Maps for the address in `BIZ`). The form
asks what the visitor needs help with (Group benefits / Fractional HR / Both / Not sure),
their renewal month and headcount, and is prefilled from `/contact/?renews=<Month>`
links produced by the hero dial. The side column shows the four team members.

## Before go-live: things to confirm with the client

1. **Street address and suite.** Directory listings tied to 678-388-1837 give
   1301 Shiloh Road NW, Kennesaw, GA 30144, but the suite varies (110 / 111 / 141).
   Update `BIZ` in `tools/build_site.py` and rebuild. Add business hours there too if desired.
2. **Contact form endpoint.** The form has no backend yet. Set `data-endpoint` on
   `<form id="contact-form">` (contact/index.html) to a Formspree, Basin, Netlify Forms
   or similar POST URL. Until then it opens the visitor's email client with the message prefilled.
3. **Service descriptions.** The one-line service descriptions and FAQ answers were
   written from the current site's copy and standard industry practice. Have the team
   read them once.
4. **Analytics.** Nothing is installed. Add Google Analytics 4 or Plausible in
   `footer()` in `tools/build_site.py`, and verify the site in Google Search Console
   (submit `https://www.sigbenplus.com/sitemap.xml`).
5. **Google Business Profile.** Claim or update the listing for Signature Benefits Plus
   with the same name, address and phone used on the site.
6. **Old URLs.** The Carrd site used `#one`, `#two`, `#three`, `#contact` anchors on `/`.
   Anchors don't reach the server, so nothing needs redirecting. `.htaccess` forces
   https + www; delete it on non-Apache hosts (Netlify, Cloudflare Pages, Vercel do this themselves).
