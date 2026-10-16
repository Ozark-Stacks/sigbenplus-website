"""Generates the static pages in /site from one shared layout.

Run:  python tools/build_site.py
Edit the PAGES list below (or the layout functions) and re-run. The output is
plain HTML with no runtime dependency on this script, so the site can also be
edited directly if that's easier.
"""
from __future__ import annotations
import json, math, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "site")
DOMAIN = "https://www.sigbenplus.com"

BIZ = {
    "name": "Signature Benefits Plus",
    "phone_display": "678-388-1837",
    "phone_tel": "+16783881837",
    "email": "info@sigbenplus.com",
    "street": "1301 Shiloh Road NW",
    "city": "Kennesaw",
    "region": "GA",
    "zip": "30144",
    "linkedin": "https://www.linkedin.com/in/brian-logan-5b117a13/",
    "youtube": "https://www.youtube.com/channel/UCr83D0He0xuiI5Wimf4mITQ",
    "employee_navigator": "https://www.employeenavigator.com/identity/Account/Login",
    "zywave": "https://auth.zywave.com/username/login",
}

ORG_LD = {
    "@context": "https://schema.org",
    "@type": ["InsuranceAgency", "ProfessionalService"],
    "@id": DOMAIN + "/#organization",
    "name": BIZ["name"],
    "url": DOMAIN + "/",
    "logo": DOMAIN + "/assets/img/logo-sbplus.png",
    "image": DOMAIN + "/assets/img/og-card.jpg",
    "description": "Group employee benefits brokerage and fractional HR services for Georgia businesses: group health plans, HR compliance, onboarding, background checks, drug testing, terminations, employee handbooks and annual training.",
    "telephone": "+1-678-388-1837",
    "email": BIZ["email"],
    "address": {
        "@type": "PostalAddress",
        "streetAddress": BIZ["street"],
        "addressLocality": BIZ["city"],
        "addressRegion": BIZ["region"],
        "postalCode": BIZ["zip"],
        "addressCountry": "US",
    },
    "areaServed": [
        {"@type": "State", "name": "Georgia"},
        {"@type": "City", "name": "Kennesaw"},
        {"@type": "City", "name": "Atlanta"},
    ],
    "sameAs": [BIZ["linkedin"], BIZ["youtube"]],
    "knowsAbout": ["Group health insurance", "Employee benefits", "HR compliance", "Fractional HR", "Employee onboarding", "Employee handbooks", "Background checks", "Drug testing programs", "Annual compliance training"],
    "hasOfferCatalog": {
        "@type": "OfferCatalog",
        "name": "Services",
        "itemListElement": [
            {"@type": "Offer", "itemOffered": {"@type": "Service", "name": "Group Employee Benefits", "url": DOMAIN + "/group-benefits/"}},
            {"@type": "Offer", "itemOffered": {"@type": "Service", "name": "Fractional HR", "url": DOMAIN + "/fractional-hr/"}},
        ],
    },
}

def _asset_version() -> str:
    """Short content hash of the CSS + JS so browsers refetch them after a change."""
    import hashlib
    h = hashlib.sha256()
    for rel in ("site/assets/css/styles.css", "site/assets/js/main.js"):
        with open(os.path.join(ROOT, rel.replace("/", os.sep)), "rb") as f:
            h.update(f.read())
    return h.hexdigest()[:8]


ASSET_V = _asset_version()

NAV = [
    ("/group-benefits/", "Group Benefits"),
    ("/fractional-hr/", "Fractional HR"),
    ("/about/", "About"),
    ("/contact/", "Contact"),
]

MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]

FONTS_URL = "https://fonts.googleapis.com/css2?family=Newsreader:opsz,wght@6..72,500;6..72,600&family=Public+Sans:wght@400;500;600;700&display=swap"


def _pt(cx, cy, r, deg):
    a = math.radians(deg)
    return cx + r * math.sin(a), cy - r * math.cos(a)


def _arc(cx, cy, r, a0, a1):
    x0, y0 = _pt(cx, cy, r, a0)
    x1, y1 = _pt(cx, cy, r, a1)
    large = 1 if (a1 - a0) > 180 else 0
    return "M%.1f %.1f A%d %d 0 %d 1 %.1f %.1f" % (x0, y0, r, r, large, x1, y1)


def dial_svg() -> str:
    """The renewal dial: 12 month segments; a lime arc covers the 90-day window before
    the renewal month (white). JS rotates the highlight group by 30 degrees per month."""
    cx = cy = 260
    r, rl, half = 218, 247, 13.5
    segs, labels = [], []
    for i, m in enumerate(MONTHS):
        a = i * 30
        segs.append('<path class="dial__seg" data-month="%d" style="--i:%d" d="%s"><title>%s</title></path>' % (i, i, _arc(cx, cy, r, a - half, a + half), m))
        lx, ly = _pt(cx, cy, rl, a)
        labels.append('<text class="dial__lbl" x="%.1f" y="%.1f">%s</text>' % (lx, ly, m[:3].upper()))
    ticks = []
    for a in (-75, -45, -15):  # 90 / 60 / 30 day boundaries
        x0, y0 = _pt(cx, cy, r - 15, a)
        x1, y1 = _pt(cx, cy, r + 15, a)
        ticks.append('<line class="dial__tick" x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>' % (x0, y0, x1, y1))
    # "90 days / 60 days / 30 days" sit just inside the ring; CSS counter-rotates them so they stay upright
    days = "".join(
        '<g class="dial__day" style="--rel:%ddeg"><text x="%d" y="%d">%s</text></g>' % (rel, cx, cy - (r - 44), lbl)
        for rel, lbl in ((-90, "90 days"), (-60, "60 days"), (-30, "30 days"))
    )
    sx, sy = _pt(cx, cy, r, -90 - half)
    return (
        '<svg class="dial__svg" viewBox="0 0 520 520" aria-hidden="true" focusable="false">'
        '<circle class="dial__bg" cx="%d" cy="%d" r="%d"/>' % (cx, cy, r)
        + '<g class="dial__segs">' + "".join(segs) + "</g>"
        + '<g class="dial__hl" id="dial-hl">'
        + '<path class="dial__arc" d="%s"/>' % _arc(cx, cy, r, -90 - half, half)
        + '<path class="dial__renew" d="%s"/>' % _arc(cx, cy, r, -half, half)
        + "".join(ticks)
        + days
        + '<circle class="dial__ping" cx="%.1f" cy="%.1f" r="9"/>' % (sx, sy)
        + '<circle class="dial__start" cx="%.1f" cy="%.1f" r="9"/>' % (sx, sy)
        + "</g>"
        + '<g class="dial__labels">' + "".join(labels) + "</g>"
        + "</svg>"
    )


def office_photo(alt: str) -> str:
    """Responsive <picture> for the one photo on the site (WebP + JPEG, two widths)."""
    sizes = "(max-width: 800px) 100vw, 50vw"
    return (
        '<picture>'
        f'<source type="image/webp" srcset="/assets/img/office-meeting-800.webp 800w, /assets/img/office-meeting-1200.webp 1200w" sizes="{sizes}">'
        f'<img src="/assets/img/office-meeting-1200.jpg" srcset="/assets/img/office-meeting-800.jpg 800w, /assets/img/office-meeting-1200.jpg 1200w" sizes="{sizes}" alt="{alt}" width="1200" height="799" loading="lazy">'
        '</picture>'
    )


def head(p: dict) -> str:
    url = DOMAIN + p["path"]
    ld = [ORG_LD] + p.get("ld", [])
    ld_html = "\n".join(
        '<script type="application/ld+json">%s</script>' % json.dumps(x, ensure_ascii=False, separators=(",", ":"))
        for x in ld
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{p["title"]}</title>
<meta name="description" content="{p["description"]}">
<link rel="canonical" href="{url}">
<meta name="robots" content="index, follow, max-image-preview:large">
<meta name="theme-color" content="#123F63">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{BIZ["name"]}">
<meta property="og:title" content="{p["og_title"]}">
<meta property="og:description" content="{p["description"]}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{DOMAIN}/assets/img/og-card.jpg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="A benefits review meeting around a conference table">
<meta property="og:locale" content="en_US">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{p["og_title"]}">
<meta name="twitter:description" content="{p["description"]}">
<meta name="twitter:image" content="{DOMAIN}/assets/img/og-card.jpg">
<link rel="icon" type="image/png" href="/assets/img/favicon.png">
<link rel="apple-touch-icon" href="/assets/img/apple-touch-icon.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="/assets/css/styles.css?v={ASSET_V}">
<link rel="preload" as="style" href="{FONTS_URL}" onload="this.onload=null;this.rel='stylesheet'">
<noscript><link rel="stylesheet" href="{FONTS_URL}"></noscript>
{ld_html}
</head>
<body>
<a class="skip-link" href="#main">Skip to content</a>
"""


def header(current: str) -> str:
    items = "\n".join(
        '        <li><a href="%s"%s>%s</a></li>' % (href, ' aria-current="page"' if href == current else "", label)
        for href, label in NAV
    )
    return f"""<div class="topbar">
  <div class="wrap topbar__inner">
    <div class="topbar__contact">
      <a class="tel" href="tel:{BIZ["phone_tel"]}">{BIZ["phone_display"]}</a>
      <a class="email" href="mailto:{BIZ["email"]}">{BIZ["email"]}</a>
      <span class="topbar__place">{BIZ["city"]}, Georgia</span>
    </div>
    <details class="login">
      <summary>Client login</summary>
      <ul class="login__menu">
        <li><a href="{BIZ["employee_navigator"]}" rel="noopener">Employee Navigator <small>Benefits enrollment &amp; employee portal</small></a></li>
        <li><a href="{BIZ["zywave"]}" rel="noopener">Zywave <small>HR compliance library &amp; resources</small></a></li>
      </ul>
    </details>
  </div>
</div>
<header class="site-header">
  <div class="wrap site-header__inner">
    <a class="brand" href="/">
      <img src="/assets/img/logo-sbplus-200.png" srcset="/assets/img/logo-sbplus-200.png 200w, /assets/img/logo-sbplus.png 534w" sizes="110px" alt="" width="200" height="122" fetchpriority="high">
      <span class="brand__name"><b>Signature Benefits Plus</b><span>Group benefits &amp; fractional HR for Georgia employers</span></span>
    </a>
    <button class="nav-toggle" type="button" aria-expanded="false" aria-controls="site-nav">Menu</button>
    <nav id="site-nav" class="site-nav" aria-label="Main">
      <ul>
{items}
      </ul>
      <div class="site-nav__actions">
        <a class="btn" href="/contact/">Talk to us</a>
      </div>
    </nav>
  </div>
</header>
<main id="main">
"""


def footer() -> str:
    return f"""</main>
<footer class="site-footer">
  <div class="wrap">
    <div class="site-footer__grid">
      <div>
        <a class="brand" href="/" aria-label="Signature Benefits Plus home"><img src="/assets/img/logo-sbplus-200.png" alt="" width="200" height="122" loading="lazy"></a>
        <address>
          {BIZ["name"]}<br>
          {BIZ["street"]}<br>
          {BIZ["city"]}, {BIZ["region"]} {BIZ["zip"]}
        </address>
      </div>
      <div>
        <h3>Services</h3>
        <ul>
          <li><a href="/group-benefits/">Group Benefits</a></li>
          <li><a href="/fractional-hr/">Fractional HR</a></li>
          <li><a href="/fractional-hr/#services">HR compliance &amp; audits</a></li>
          <li><a href="/fractional-hr/#services">Handbooks &amp; training</a></li>
        </ul>
      </div>
      <div>
        <h3>Company</h3>
        <ul>
          <li><a href="/about/">About &amp; team</a></li>
          <li><a href="/contact/">Contact</a></li>
          <li><a href="{BIZ["linkedin"]}" rel="noopener">LinkedIn</a></li>
          <li><a href="{BIZ["youtube"]}" rel="noopener">YouTube</a></li>
        </ul>
      </div>
      <div>
        <h3>Get in touch</h3>
        <ul>
          <li><a href="tel:{BIZ["phone_tel"]}">{BIZ["phone_display"]}</a></li>
          <li><a href="mailto:{BIZ["email"]}">{BIZ["email"]}</a></li>
          <li><a href="{BIZ["employee_navigator"]}" rel="noopener">Employee Navigator login</a></li>
          <li><a href="{BIZ["zywave"]}" rel="noopener">Zywave login</a></li>
        </ul>
      </div>
    </div>
    <div class="site-footer__bottom">
      <span>&copy; <span data-year>2026</span> {BIZ["name"]}. All rights reserved.</span>
      <span>Kennesaw, Georgia &middot; Serving employers across Georgia</span>
    </div>
  </div>
</footer>
<script src="/assets/js/main.js?v={ASSET_V}" defer></script>
</body>
</html>
"""


def breadcrumb(trail: list) -> tuple:
    parts = []
    for i, (h, t) in enumerate(trail):
        if i < len(trail) - 1:
            parts.append('<li><a href="%s">%s</a></li>' % (h, t))
        else:
            parts.append('<li aria-current="page">%s</li>' % t)
    html = '<ol class="breadcrumb" aria-label="Breadcrumb">' + "".join(parts) + "</ol>"
    ld = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": t, "item": DOMAIN + h} for i, (h, t) in enumerate(trail)
        ],
    }
    return html, ld


def faq(items: list) -> tuple:
    html = '<div class="faq">' + "".join(
        '<details><summary>%s</summary><div class="faq__a"><p>%s</p></div></details>' % (q, a) for q, a in items
    ) + "</div>"
    ld = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": re.sub(r"<[^>]+>", "", a)}}
            for q, a in items
        ],
    }
    return html, ld


CTA_BAND = """<section class="section band--navy">
  <div class="wrap cta-band">
    <div>
      <h2>Not sure you're compliant? Let's find out.</h2>
      <p>Are you sure you are complying with all state and federal regulations? If an audit is needed, we'll work through it with you.</p>
    </div>
    <div class="btn-row">
      <a class="btn" href="/contact/">Start a conversation</a>
      <a class="btn btn--outline-light" href="tel:%s">Call %s</a>
    </div>
  </div>
</section>
""" % (BIZ["phone_tel"], BIZ["phone_display"])

MONTH_OPTIONS = "".join(
    '<option value="%d"%s>%s</option>' % (i, " selected" if i == 0 else "", m) for i, m in enumerate(MONTHS)
)

TEAM = [
    ("brian-logan.jpg", "Brian Logan", "Partner", BIZ["linkedin"]),
    ("paige-alfonso.jpg", "Paige Alfonso", "Senior Account Manager", None),
    ("gaby-centeno.jpg", "Gaby Centeno", "Account Manager", None),
    ("rhonda-perry.jpg", "Rhonda Perry", "Account Manager", None),
]


def team_list() -> str:
    out = ['<ul class="team">']
    for img, name, role, link in TEAM:
        base = img[:-4]
        out.append(
            '  <li><img src="/assets/img/team/%s-400.jpg" srcset="/assets/img/team/%s-400.jpg 400w, /assets/img/team/%s 495w" sizes="(max-width: 800px) 45vw, 250px" alt="Portrait of %s" width="400" height="400" loading="lazy"><h3>%s</h3><p>%s</p>%s</li>'
            % (base, base, img, name, name, role, ('<a href="%s" rel="noopener">LinkedIn</a>' % link) if link else "")
        )
    out.append("</ul>")
    return "\n".join(out)


VALUES_GB = """<ul class="values">
      <li><strong>Efficiency</strong><p>We focus on <em>your</em> bottom line. Our goal is to provide the top-tier support you need so your business can operate efficiently and effectively.</p></li>
      <li><strong>Integrity</strong><p>With Signature Benefits Plus you can expect the highest level of integrity and the most up-to-date industry knowledge.</p></li>
      <li><strong>Cutting edge</strong><p>We are always on the lookout for the newest and best technology resources to give businesses and their employees access to the latest tools and products. We follow the leading industry best practices to find the solutions that work for each of our clients.</p></li>
    </ul>"""

VALUES_FHR = """<ul class="values">
      <li><strong>Flexibility</strong><p>We tailor our services specifically to your business. That means you get exactly what you need and nothing you don't. We're here to take on the tasks you no longer want to handle.</p></li>
      <li><strong>Proactive approach</strong><p>While many big HR firms react to issues after they've happened, we aim to catch missteps before they turn into problems. Our dedicated approach means we are on the lookout for issues when others may not have the bandwidth.</p></li>
      <li><strong>Cost savings</strong><p>When you work with Signature Benefits Plus, we share the HR burden at a fraction of the cost. This allows your other HR specialists to focus on the most productive aspects of the job.</p></li>
    </ul>"""

GB_FAQ_ITEMS = [
    ("When should we start our renewal?", "Sixty to ninety days before your plan renews. That leaves time to review claims and census data, compare carrier options, and roll out changes to employees without a scramble. Tell us your renewal month and we'll reach out at the right time."),
    ("Do you work with specific carriers?", "We work with the leading carriers and compare options for your group rather than steering you to one. The goal is the plan that fits your budget and your people."),
    ("Who helps our employees with enrollment and questions?", "We do. Clients get enrollment through Employee Navigator and an account manager who knows the group. Employees and administrators have someone to call."),
    ("Is an audit needed?", "If you're not certain you're complying with every state and federal requirement that applies to your plan, an audit is the quickest way to know. We'll review what you have and tell you plainly what, if anything, needs attention."),
]
FHR_FAQ_ITEMS = [
    ("What is fractional HR?", "Experienced HR support on a part-time, as-needed basis. You get the expertise of an HR department for the hours you actually need, instead of carrying a full-time salary."),
    ("Do we need to replace our existing HR person?", "No. We share the HR burden so the people you already have can focus on the most productive parts of the job. Many clients use us alongside an office manager or a single HR generalist."),
    ("Which tasks can you take on?", "HR compliance, onboarding, background checks, drug testing programs, terminations, employee handbooks and annual training. We tailor the scope to your business, so you get exactly what you need and nothing you don't."),
    ("How do you keep problems from happening in the first place?", "By looking for them before they surface. Where many large HR firms react after an issue has already happened, we aim to catch missteps early, when they are still cheap to fix."),
]

gb_faq_html, gb_faq_ld = faq(GB_FAQ_ITEMS)
fhr_faq_html, fhr_faq_ld = faq(FHR_FAQ_ITEMS)
gb_bc_html, gb_bc_ld = breadcrumb([("/", "Home"), ("/group-benefits/", "Group Benefits")])
fhr_bc_html, fhr_bc_ld = breadcrumb([("/", "Home"), ("/fractional-hr/", "Fractional HR")])
about_bc_html, about_bc_ld = breadcrumb([("/", "Home"), ("/about/", "About")])
contact_bc_html, contact_bc_ld = breadcrumb([("/", "Home"), ("/contact/", "Contact")])

HOME_BODY = f"""<section class="hero-band">
  <div class="wrap hero-band__grid">
    <div>
      <h1>Group benefits and HR support that gets ahead of the deadline.</h1>
      <p class="lede">Signature Benefits Plus is a Kennesaw-based benefits broker and fractional HR partner. We start your renewal <strong>90 days out</strong>, and we take on the HR work you'd rather not do.</p>
      <div class="btn-row">
        <a class="btn" href="/contact/">Talk to us</a>
        <a class="btn btn--outline-light" href="#services-title">What we handle</a>
      </div>
    </div>
    <aside class="planner planner--dial" aria-labelledby="planner-title">
      <h2 id="planner-title" class="visually-hidden">Renewal planner</h2>
      <div class="dial" id="dial">
        {dial_svg()}
        <div class="dial__center">
          <small>Your plan renews</small>
          <span class="dial__month" id="dial-month">January</span>
          <span class="dial__sub" id="dial-sub">We start in October</span>
        </div>
      </div>
      <div class="planner__controls">
        <label for="renew-month">Renewal month</label>
        <select id="renew-month" name="renew-month">{MONTH_OPTIONS}</select>
      </div>
      <p class="planner__out" id="planner-out" aria-live="polite">For a <strong>January 1</strong> renewal, we'd start your review in <strong>October</strong> and have options in front of you by <strong>November</strong>.</p>
      <a class="btn btn--light" id="planner-cta" href="/contact/?renews=January">Tell us your renewal date</a>
      <p class="planner__note">The lime arc is the 90 days we work ahead of your renewal. Click a month or pick one above.</p>
    </aside>
  </div>
</section>

<section class="paths-strip" aria-label="Our two services">
  <div class="wrap">
    <div class="paths paths--float">
      <a class="path" href="/group-benefits/">
        <h2>Group Benefits</h2>
        <p>Health, dental, vision, life and voluntary plans, compared across leading carriers and supported through enrollment and renewal.</p>
        <span class="path__go">See how we handle benefits</span>
      </a>
      <a class="path" href="/fractional-hr/">
        <h2>Fractional HR</h2>
        <p>Compliance, onboarding, handbooks, training and terminations, handled by an experienced HR team at a fraction of a full-time hire.</p>
        <span class="path__go">See what we take on</span>
      </a>
    </div>
  </div>
</section>

<section class="section band--mist" aria-labelledby="services-title">
  <div class="wrap">
    <div class="section-head">
      <h2 id="services-title">What we take off your plate</h2>
      <p>Two sides of the same job: a benefits program your employees value, and the HR work that keeps the business compliant.</p>
    </div>
    <div class="services">
      <div class="services__group">
        <h3>Benefits</h3>
        <ul class="service-list">
          <li><div><strong>Employee benefits</strong><span>Group health, dental, vision, life and voluntary plans, shopped across leading carriers and managed from quote to renewal.</span></div></li>
          <li><div><strong>Enrollment and employee support</strong><span>Online enrollment through Employee Navigator, plus an account manager your employees can actually reach.</span></div></li>
          <li><div><strong>Renewal planning</strong><span>We start 60 to 90 days out, review the numbers, and bring you options before the deadline does.</span></div></li>
        </ul>
      </div>
      <div class="services__group">
        <h3>HR</h3>
        <ul class="service-list">
          <li><div><strong>HR compliance</strong><span>State and federal requirements tracked, audited and documented so missteps are caught early.</span></div></li>
          <li><div><strong>Onboarding</strong><span>New-hire paperwork, benefits enrollment and first-week setup done right the first time.</span></div></li>
          <li><div><strong>Background checks and drug testing</strong><span>Screening programs and policies that are consistent, fair and defensible.</span></div></li>
          <li><div><strong>Terminations</strong><span>Documented, compliant separations that protect the business and treat people decently.</span></div></li>
          <li><div><strong>Employee handbooks and annual training</strong><span>Handbooks written for your state and workplace, and required training delivered on schedule.</span></div></li>
        </ul>
      </div>
    </div>
  </div>
</section>

<section class="section" aria-labelledby="gb-title">
  <div class="wrap offer">
    <div class="offer__intro">
      <h2 id="gb-title">Why work with us for your group benefits?</h2>
      <p>With constantly changing legislation and compliance mandates, it's more important than ever to have a broker you trust.</p>
      <a class="btn btn--ghost" href="/group-benefits/">More on group benefits</a>
    </div>
    {VALUES_GB}
  </div>
</section>

<section class="section band--mist" aria-labelledby="fhr-title">
  <div class="wrap offer">
    <div class="offer__intro">
      <h2 id="fhr-title">Why consider us for fractional HR?</h2>
      <p>Not every business needs an additional full-time HR person or a whole HR team. We share the HR burden at a fraction of the cost.</p>
      <a class="btn btn--ghost" href="/fractional-hr/">More on fractional HR</a>
    </div>
    {VALUES_FHR}
  </div>
</section>

<section class="section" aria-labelledby="how-title">
  <div class="wrap">
    <div class="section-head">
      <h2 id="how-title">How it starts</h2>
      <p>No long onboarding. Three steps and you'll know where you stand.</p>
    </div>
    <ol class="steps">
      <li><h3>Tell us your renewal date</h3><p>Or tell us what's keeping you up at night on the HR side. A short call is enough to get started.</p></li>
      <li><h3>We review what you have</h3><p>Your current plan, your census, and your compliance exposure. If an audit is needed, we'll say so.</p></li>
      <li><h3>Options, then action</h3><p>You'll see your choices 60 to 90 days before renewal, with enough time to decide, enroll and communicate to employees.</p></li>
    </ol>
  </div>
</section>

<section class="section band--navy" aria-labelledby="partners-title">
  <div class="wrap">
    <div class="section-head">
      <h2 id="partners-title">The platforms behind the service</h2>
      <p>Enrollment and HR compliance run on two systems our clients know by name. Current clients log in here; new clients are set up on both.</p>
    </div>
    <div class="partners">
      <div class="partner">
        <img class="partner__logo" src="/assets/img/partners/employee-navigator.svg" alt="Employee Navigator" width="500" height="158" loading="lazy">
        <h3>Benefits administration and enrollment</h3>
        <p>Employees enroll online, make life-event changes and find their plan documents in one place. Administrators see the whole group without the paperwork.</p>
        <div class="btn-row"><a class="btn btn--outline-light" href="{BIZ["employee_navigator"]}" rel="noopener">Log in to Employee Navigator</a></div>
      </div>
      <div class="partner">
        <img class="partner__logo" src="/assets/img/partners/zywave.png" alt="Zywave" width="469" height="130" loading="lazy">
        <h3>HR compliance library and resources</h3>
        <p>Handbook templates, required notices, legislative briefs and compliance checklists, updated as the rules change. It is the reference shelf behind our fractional HR work.</p>
        <div class="btn-row"><a class="btn btn--outline-light" href="{BIZ["zywave"]}" rel="noopener">Log in to Zywave</a></div>
      </div>
    </div>
  </div>
</section>

<section class="section band--mist" aria-labelledby="team-title">
  <div class="wrap">
    <div class="section-head">
      <h2 id="team-title">Meet our team</h2>
      <p>We are proud of the team we've built, and we are excited to work with you. With over 45 years of combined HR experience, we've seen and handled everything an HR team might face.</p>
    </div>
    {team_list()}
    <p style="margin-top:2rem"><a class="text-link" href="/about/">More about the firm</a></p>
  </div>
</section>

{CTA_BAND}"""

GB_BODY = f"""<section class="page-head">
  <div class="wrap">
    {gb_bc_html}
    <h1>Group benefits, handled by a broker who watches your bottom line.</h1>
    <p class="lede">We shop your group health plan across leading carriers, run enrollment, and stay on the account all year, so renewal is a review and not a scramble.</p>
    <div class="btn-row" style="margin-top:1.5rem">
      <a class="btn" href="/contact/">Request a plan review</a>
      <a class="btn btn--ghost" href="#faq">Common questions</a>
    </div>
  </div>
</section>

<section class="section band--mist" aria-labelledby="gb-what">
  <div class="wrap">
    <div class="section-head">
      <h2 id="gb-what">What's included</h2>
      <p>A benefits program is more than a quote. These are the pieces we handle for every group.</p>
    </div>
    <div class="services">
      <div class="services__group">
        <h3>Plan design and placement</h3>
        <ul class="service-list">
          <li><div><strong>Group health</strong><span>Medical plans compared on cost, network and employee fit, not just the lowest premium.</span></div></li>
          <li><div><strong>Dental, vision and life</strong><span>Rounded-out coverage that makes the whole package easier to recruit with.</span></div></li>
          <li><div><strong>Voluntary benefits</strong><span>Additional benefits employees can elect at a fraction of health insurance costs.</span></div></li>
        </ul>
      </div>
      <div class="services__group">
        <h3>Administration and support</h3>
        <ul class="service-list">
          <li><div><strong>Enrollment through Employee Navigator</strong><span>Online open enrollment, new-hire elections and life-event changes in one place.</span></div></li>
          <li><div><strong>Compliance resources through Zywave</strong><span>Notices, documents and legislative updates when the rules change.</span></div></li>
          <li><div><strong>An account manager who knows your group</strong><span>Someone to call for claims questions, carrier issues and employee help.</span></div></li>
        </ul>
      </div>
    </div>
  </div>
</section>

<section class="section" aria-labelledby="gb-why">
  <div class="wrap offer">
    <div class="offer__intro">
      <h2 id="gb-why">Why work with us?</h2>
      <p>With constantly changing legislation and compliance mandates, it's more important than ever to have a broker you trust.</p>
    </div>
    {VALUES_GB}
  </div>
</section>

<section class="section band--navy" aria-labelledby="gb-timeline">
  <div class="wrap">
    <div class="section-head">
      <h2 id="gb-timeline">The renewal timeline we work to</h2>
      <p>Carriers release renewals late. We don't wait for them.</p>
    </div>
    <ol class="steps">
      <li><h3>90 days out</h3><p>We pull your census and claims experience, confirm what's changed in the business, and begin marketing the group.</p></li>
      <li><h3>60 days out</h3><p>You see a side-by-side of options with real numbers, and we recommend a direction.</p></li>
      <li><h3>30 days out</h3><p>Decision made, enrollment opened in Employee Navigator, employee communications sent. Renewal day is uneventful.</p></li>
    </ol>
  </div>
</section>

<section class="section" id="faq" aria-labelledby="gb-faq">
  <div class="wrap">
    <div class="section-head">
      <h2 id="gb-faq">Common questions about group benefits</h2>
    </div>
    {gb_faq_html}
  </div>
</section>

{CTA_BAND}"""

FHR_BODY = f"""<section class="page-head">
  <div class="wrap">
    {fhr_bc_html}
    <h1>HR expertise at a fraction of a full-time hire.</h1>
    <p class="lede">Not every business needs an additional full-time HR person or a whole HR team. We share the HR burden, tailored to what your business actually needs, and we look for problems before they become expensive.</p>
    <div class="btn-row" style="margin-top:1.5rem">
      <a class="btn" href="/contact/">Ask about an HR audit</a>
      <a class="btn btn--ghost" href="#services">What we handle</a>
    </div>
  </div>
</section>

<section class="section band--mist" id="services" aria-labelledby="fhr-services">
  <div class="wrap">
    <div class="section-head">
      <h2 id="fhr-services">What we handle</h2>
      <p>Pick the pieces you want off your desk. Scope is tailored to your business, so you get exactly what you need and nothing you don't.</p>
    </div>
    <div class="services">
      <div class="services__group">
        <h3>Compliance</h3>
        <ul class="service-list">
          <li><div><strong>HR compliance audits</strong><span>A clear-eyed review of policies, files and practices against current state and federal requirements.</span></div></li>
          <li><div><strong>Employee handbooks</strong><span>Written and updated for your state and your workplace, so the rules are in writing before you need them.</span></div></li>
          <li><div><strong>Annual training</strong><span>Required and recommended training delivered on schedule and documented.</span></div></li>
        </ul>
      </div>
      <div class="services__group">
        <h3>The employee lifecycle</h3>
        <ul class="service-list">
          <li><div><strong>Onboarding</strong><span>New-hire paperwork, benefits enrollment and first-week setup done right the first time.</span></div></li>
          <li><div><strong>Background checks</strong><span>Consistent pre-employment screening coordinated through vetted providers.</span></div></li>
          <li><div><strong>Drug testing</strong><span>Policy design and testing programs that hold up when questioned.</span></div></li>
          <li><div><strong>Terminations</strong><span>Documented, compliant separations that protect the business and treat people decently.</span></div></li>
        </ul>
      </div>
    </div>
  </div>
</section>

<section class="section" aria-labelledby="fhr-why">
  <div class="wrap offer">
    <div class="offer__intro">
      <h2 id="fhr-why">Why consider us?</h2>
      <p>We're here to take on the tasks you no longer want to handle, and to catch the ones you didn't know were a risk.</p>
    </div>
    {VALUES_FHR}
  </div>
</section>

<section class="section band--mist" aria-labelledby="fhr-fit">
  <div class="wrap feature">
    <div>
      <h2 id="fhr-fit">A good fit if&hellip;</h2>
      <ul class="service-list">
        <li><div><strong>You have an office manager doing HR on the side</strong><span>and you'd like a professional checking the work.</span></div></li>
        <li><div><strong>You're growing past the size where informal HR works</strong><span>and need handbooks, files and training that would survive a complaint.</span></div></li>
        <li><div><strong>You already use us for benefits</strong><span>and want one team that knows your people on both sides.</span></div></li>
      </ul>
    </div>
    {office_photo("Two people shaking hands across a conference table while colleagues look on")}
  </div>
</section>

<section class="section" id="faq" aria-labelledby="fhr-faq">
  <div class="wrap">
    <div class="section-head">
      <h2 id="fhr-faq">Common questions about fractional HR</h2>
    </div>
    {fhr_faq_html}
  </div>
</section>

{CTA_BAND}"""

ABOUT_BODY = f"""<section class="page-head">
  <div class="wrap">
    {about_bc_html}
    <h1>Meet the team.</h1>
    <p class="lede">We are proud of the team we've built, and we are excited to work with you. With over 45 years of combined HR experience, we've seen and handled everything an HR team might face.</p>
  </div>
</section>

<section class="section" aria-label="Team members">
  <div class="wrap">
    {team_list()}
  </div>
</section>

<section class="section band--mist" aria-labelledby="about-firm">
  <div class="wrap feature">
    {office_photo("A benefits review meeting around a conference table")}
    <div>
      <h2 id="about-firm">One team for benefits and HR</h2>
      <p>Signature Benefits Plus pairs group benefits brokerage with fractional HR support. Most firms do one or the other. Doing both means the people who place your health plan are the same people who write your handbook and run your onboarding, and nothing falls between two vendors.</p>
      <p>We're based in Kennesaw, Georgia, and work with employers across the state.</p>
      <p class="stat">45+</p>
      <p>years of combined HR experience across the team.</p>
      <div class="btn-row">
        <a class="btn" href="/contact/">Start a conversation</a>
        <a class="btn btn--ghost" href="{BIZ["linkedin"]}" rel="noopener">Brian on LinkedIn</a>
      </div>
    </div>
  </div>
</section>

{CTA_BAND}"""

ICON_PHONE = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3.1 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2.1 4.2 2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1.9.4 1.8.7 2.7a2 2 0 0 1-.5 2.1L8 9.8a16 16 0 0 0 6 6l1.3-1.3a2 2 0 0 1 2.1-.4c.9.3 1.8.6 2.7.7a2 2 0 0 1 1.7 2z"/></svg>'
ICON_MAIL = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3 7 9 6 9-6"/></svg>'
ICON_PIN = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0z"/><circle cx="12" cy="10" r="3"/></svg>'
MAPS_URL = "https://www.google.com/maps/search/?api=1&query=" + "+".join((BIZ["street"] + " " + BIZ["city"] + " " + BIZ["region"] + " " + BIZ["zip"]).split())
RENEW_OPTIONS = '<option value="">Not sure yet</option>' + "".join('<option value="%s">%s</option>' % (m, m) for m in MONTHS)

CONTACT_BODY = f"""<section class="hero-band hero-band--contact">
  <div class="wrap">
    {contact_bc_html}
    <h1>Let's team up and get the job done.</h1>
    <p class="lede">Tell us when your plan renews, or what's keeping you up at night on the HR side. We'll get back to you as soon as we can.</p>
    <ul class="contact-tiles">
      <li><a class="contact-tile" href="tel:{BIZ["phone_tel"]}"><span class="contact-tile__icon">{ICON_PHONE}</span><small>Call</small><strong>{BIZ["phone_display"]}</strong><span class="contact-tile__hint">Straight to the Kennesaw office</span></a></li>
      <li><a class="contact-tile" href="mailto:{BIZ["email"]}"><span class="contact-tile__icon">{ICON_MAIL}</span><small>Email</small><strong>{BIZ["email"]}</strong><span class="contact-tile__hint">We read every message</span></a></li>
      <li><a class="contact-tile" href="{MAPS_URL}" rel="noopener"><span class="contact-tile__icon">{ICON_PIN}</span><small>Visit</small><strong>{BIZ["street"]}, {BIZ["city"]}, {BIZ["region"]} {BIZ["zip"]}</strong><span class="contact-tile__hint">Get directions</span></a></li>
    </ul>
  </div>
</section>

<section class="contact-main">
  <div class="wrap contact">
    <div>
      <form id="contact-form" class="contact-form contact-form--card" method="post" action="#" data-endpoint="" novalidate>
        <h2 class="contact-form__title">Send us a message</h2>
        <p class="contact-form__intro">A few details and we'll come to the first call prepared.</p>
        <fieldset class="field">
          <legend>What do you need help with?</legend>
          <div class="pills">
            <label class="pill"><input type="radio" name="topic" value="Group benefits" checked><span>Group benefits</span></label>
            <label class="pill"><input type="radio" name="topic" value="Fractional HR"><span>Fractional HR</span></label>
            <label class="pill"><input type="radio" name="topic" value="Both"><span>Both</span></label>
            <label class="pill"><input type="radio" name="topic" value="Not sure yet"><span>Not sure yet</span></label>
          </div>
        </fieldset>
        <div class="field--2">
          <div class="field">
            <label for="name">Name</label>
            <input id="name" name="name" type="text" autocomplete="name" required>
          </div>
          <div class="field">
            <label for="company">Company <small>(optional)</small></label>
            <input id="company" name="company" type="text" autocomplete="organization">
          </div>
        </div>
        <div class="field--2">
          <div class="field">
            <label for="email">Email</label>
            <input id="email" name="email" type="email" autocomplete="email" required>
          </div>
          <div class="field">
            <label for="phone">Phone <small>(optional)</small></label>
            <input id="phone" name="phone" type="tel" autocomplete="tel">
          </div>
        </div>
        <div class="field--2">
          <div class="field">
            <label for="renew">When does your plan renew? <small>(optional)</small></label>
            <select id="renew" name="renews">{RENEW_OPTIONS}</select>
          </div>
          <div class="field">
            <label for="headcount">Employees <small>(optional)</small></label>
            <input id="headcount" name="headcount" type="text" inputmode="numeric" placeholder="e.g. 25">
          </div>
        </div>
        <div class="field">
          <label for="message">How can we help?</label>
          <textarea id="message" name="message" required></textarea>
          <small>Your current carrier, what's changed in the business, or the HR question on your mind.</small>
        </div>
        <div class="honeypot" aria-hidden="true">
          <label for="website">Leave this field empty</label>
          <input id="website" name="website" type="text" tabindex="-1" autocomplete="off">
        </div>
        <div class="btn-row">
          <button class="btn" type="submit">Send message</button>
          <p class="form-status" id="form-status" role="status" aria-live="polite"></p>
        </div>
      </form>
      <div class="form-done" id="form-done" hidden tabindex="-1">
        <h3>Thanks for reaching out.</h3>
        <p>We'll get back to you as soon as we can. If it's urgent, call <a href="tel:{BIZ["phone_tel"]}">{BIZ["phone_display"]}</a>.</p>
      </div>
    </div>
    <aside class="contact-aside">
      <div>
        <h2>Who you'll hear from</h2>
        <ul class="people">
          <li><img src="/assets/img/team/paige-alfonso-400.jpg" alt="" width="52" height="52" loading="lazy"><div><strong>Paige Alfonso</strong><span>Senior Account Manager</span></div></li>
          <li><img src="/assets/img/team/gaby-centeno-400.jpg" alt="" width="52" height="52" loading="lazy"><div><strong>Gaby Centeno</strong><span>Account Manager</span></div></li>
          <li><img src="/assets/img/team/rhonda-perry-400.jpg" alt="" width="52" height="52" loading="lazy"><div><strong>Rhonda Perry</strong><span>Account Manager</span></div></li>
          <li><img src="/assets/img/team/brian-logan-400.jpg" alt="" width="52" height="52" loading="lazy"><div><strong>Brian Logan</strong><span>Partner</span></div></li>
        </ul>
        <p>A small team in Kennesaw with over 45 years of combined HR experience. The person who answers is the person who handles your account.</p>
      </div>
      <div>
        <h2>What helps us come prepared</h2>
        <ul class="checklist">
          <li>Your renewal month, if you have a plan today</li>
          <li>Roughly how many employees you have</li>
          <li>Your current carrier or plan, if any</li>
          <li>The HR question or worry that prompted the call</li>
        </ul>
      </div>
      <div>
        <h2>Already a client?</h2>
        <p>Log in to <a href="{BIZ["employee_navigator"]}" rel="noopener">Employee Navigator</a> for enrollment or <a href="{BIZ["zywave"]}" rel="noopener">Zywave</a> for HR resources, or just call the office.</p>
      </div>
    </aside>
  </div>
</section>
"""

PAGES = [
    {
        "path": "/", "file": "index.html",
        "title": "SigBenPlus | Group Benefits & Fractional HR in Kennesaw, GA",
        "og_title": "Signature Benefits Plus: group benefits and fractional HR for Georgia businesses",
        "description": "Signature Benefits Plus helps Georgia employers with group health benefits, HR compliance, onboarding, handbooks and training. Based in Kennesaw, GA. Call 678-388-1837.",
        "ld": [{"@context": "https://schema.org", "@type": "WebSite", "@id": DOMAIN + "/#website", "url": DOMAIN + "/", "name": BIZ["name"], "publisher": {"@id": DOMAIN + "/#organization"}}],
        "body": HOME_BODY,
    },
    {
        "path": "/group-benefits/", "file": "group-benefits/index.html",
        "title": "SigBenPlus | Group Employee Benefits Broker in Kennesaw, GA",
        "og_title": "Group employee benefits, handled by a broker who watches your bottom line",
        "description": "Group health, dental, vision, life and voluntary benefits for Georgia employers. Carrier comparison, enrollment through Employee Navigator, and renewal reviews 60 to 90 days out.",
        "ld": [gb_bc_ld, gb_faq_ld, {"@context": "https://schema.org", "@type": "Service", "name": "Group Employee Benefits", "serviceType": "Employee benefits brokerage", "provider": {"@id": DOMAIN + "/#organization"}, "areaServed": {"@type": "State", "name": "Georgia"}, "url": DOMAIN + "/group-benefits/"}],
        "body": GB_BODY,
    },
    {
        "path": "/fractional-hr/", "file": "fractional-hr/index.html",
        "title": "SigBenPlus | Fractional HR Services for Georgia Businesses",
        "og_title": "HR expertise at a fraction of a full-time hire",
        "description": "Fractional HR for Georgia employers: HR compliance audits, onboarding, background checks, drug testing, terminations, employee handbooks and annual training. Kennesaw, GA.",
        "ld": [fhr_bc_ld, fhr_faq_ld, {"@context": "https://schema.org", "@type": "Service", "name": "Fractional HR", "serviceType": "Human resources consulting", "provider": {"@id": DOMAIN + "/#organization"}, "areaServed": {"@type": "State", "name": "Georgia"}, "url": DOMAIN + "/fractional-hr/"}],
        "body": FHR_BODY,
    },
    {
        "path": "/about/", "file": "about/index.html",
        "title": "SigBenPlus | About Signature Benefits Plus & Our Team",
        "og_title": "Meet the Signature Benefits Plus team",
        "description": "Signature Benefits Plus is a Kennesaw, Georgia benefits broker and fractional HR firm with over 45 years of combined HR experience. Meet Brian Logan, Paige Alfonso, Gaby Centeno and Rhonda Perry.",
        "ld": [about_bc_ld] + [
            dict({"@context": "https://schema.org", "@type": "Person", "name": n, "jobTitle": r, "worksFor": {"@id": DOMAIN + "/#organization"}, "image": DOMAIN + "/assets/img/team/" + i}, **({"sameAs": l} if l else {}))
            for i, n, r, l in TEAM
        ],
        "body": ABOUT_BODY,
    },
    {
        "path": "/contact/", "file": "contact/index.html",
        "title": "SigBenPlus | Contact Us in Kennesaw, GA | 678-388-1837",
        "og_title": "Let's team up and get the job done",
        "description": "Contact Signature Benefits Plus in Kennesaw, GA for group benefits and fractional HR. Call 678-388-1837, email info@sigbenplus.com, or send a message and we'll get back to you.",
        "ld": [contact_bc_ld, {"@context": "https://schema.org", "@type": "ContactPage", "url": DOMAIN + "/contact/", "name": "Contact Signature Benefits Plus", "about": {"@id": DOMAIN + "/#organization"}}],
        "body": CONTACT_BODY,
    },
]


def build() -> None:
    for p in PAGES:
        html = head(p) + header(p["path"]) + p["body"] + footer()
        target = os.path.join(OUT, p["file"].replace("/", os.sep))
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with open(target, "w", encoding="utf-8", newline="\n") as f:
            f.write(html)
        print("wrote %-28s %7d bytes" % (p["file"], len(html.encode("utf-8"))))

    today = "2026-10-14"
    urls = "".join(
        "  <url><loc>%s%s</loc><lastmod>%s</lastmod><changefreq>monthly</changefreq><priority>%s</priority></url>\n"
        % (DOMAIN, p["path"], today, "1.0" if p["path"] == "/" else "0.8")
        for p in PAGES
    )
    with open(os.path.join(OUT, "sitemap.xml"), "w", encoding="utf-8", newline="\n") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + urls + "</urlset>\n")
    print("wrote sitemap.xml")


if __name__ == "__main__":
    build()
