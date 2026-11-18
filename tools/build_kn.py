"""Build Kannada versions (/kn/ and /kn/catering/) from the English pages.

Every replacement is an exact string that must occur in the source; the script
fails loudly if the English copy changes, so the two languages never drift silently.
"""
import re, sys, urllib.parse

SRC_HOME, SRC_CAT = sys.argv[1], sys.argv[2]
OUT_HOME, OUT_CAT = sys.argv[3], sys.argv[4]
EN_HOME_OUT, EN_CAT_OUT = sys.argv[5], sys.argv[6]

BASE = 'https://srishtigardenhall.com'
q = lambda t: urllib.parse.quote(t, safe='')

WA_BOOK_EN = 'Hi%2C%20I%27d%20like%20to%20enquire%20about%20booking%20Srishti%20Garden.'
WA_CAT_EN = 'Hi%2C%20I%27d%20like%20to%20enquire%20about%20Srishti%20Caterers%20for%20my%20event.'
WA_BOOK_KN = q('ನಮಸ್ಕಾರ, ಸೃಷ್ಟಿ ಗಾರ್ಡನ್ ಬುಕಿಂಗ್ ಬಗ್ಗೆ ವಿಚಾರಿಸಬೇಕಿತ್ತು.')
WA_CAT_KN = q('ನಮಸ್ಕಾರ, ನಮ್ಮ ಕಾರ್ಯಕ್ರಮಕ್ಕೆ ಸೃಷ್ಟಿ ಕ್ಯಾಟರರ್ಸ್ ಬಗ್ಗೆ ವಿಚಾರಿಸಬೇಕಿತ್ತು.')

FONT_LINK = '<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+Kannada:wght@400;700&family=Noto+Serif+Kannada:wght@700&display=swap" rel="stylesheet">\n'
KN_CSS = '''  /* Kannada typography */
  html { font-size: 106%; }
  body { font-family: 'Karla', 'Noto Sans Kannada', sans-serif; line-height: 1.75; }
  h1, h2, h3, .brand, .rating .score, .review blockquote, .enquiry-call a, .form-title, .faq summary { font-family: 'Fraunces', 'Noto Serif Kannada', serif; }
  h1, h2, h3 { line-height: 1.35; }
  .eyebrow, .hero .place, .hero .events, .enquiry-form label { letter-spacing: 0.04em; text-transform: none; }
  .eyebrow { font-size: 0.85rem; }
  .enquiry-form label { font-size: 0.85rem; }
  .vnv span { font-size: 0.9rem; }

'''
LANG_CSS = '''  /* Language switch */
  nav a.lang { margin-left: 1.1rem; padding: 0.2rem 0.75rem; border: 1px solid var(--line); border-radius: 999px; font-size: 0.85rem; opacity: 1; }
  nav a.lang:hover, nav a.lang:focus { border-color: var(--accent); text-decoration: none; }
  @media (max-width: 640px) { nav a.lang { margin-left: 0.6rem; padding: 0.15rem 0.6rem; } .brand { white-space: nowrap; } }
  @media (max-width: 440px) { nav a[href$="#venue"] { display: none; } }

'''

def rep(s, pairs, label):
    for a, b in pairs:
        n = s.count(a)
        if n == 0:
            raise SystemExit(f'[{label}] missing: {a[:90]!r}')
        s = s.replace(a, b)
    return s

def add_css(s, css):
    i = s.index('  @media (prefers-reduced-motion: reduce)')
    return s[:i] + css + s[i:]

def alternates(en_url, kn_url):
    return (f'<link rel="alternate" hreflang="en" href="{en_url}">\n'
            f'<link rel="alternate" hreflang="kn" href="{kn_url}">\n'
            f'<link rel="alternate" hreflang="x-default" href="{en_url}">\n')

# ---------- shared strings (both pages) ----------
COMMON = [
    ('<a class="skip" href="#venue">Skip to content</a>', '<a class="skip" href="#venue">ಮುಖ್ಯ ವಿಷಯಕ್ಕೆ ಹೋಗಿ</a>'),
    ('Srishti <span>Garden</span></a>', 'ಸೃಷ್ಟಿ <span>ಗಾರ್ಡನ್</span></a>'),
    ('<nav aria-label="Main">', '<nav aria-label="ಮುಖ್ಯ ಮೆನು">'),
    ('Venue</a>\n', 'ಸಭಾಂಗಣ</a>\n'),
    ('Catering</a>\n', 'ಕ್ಯಾಟರಿಂಗ್</a>\n'),
    ('Gallery</a>\n', 'ಗ್ಯಾಲರಿ</a>\n'),
    ('Location</a>\n', 'ವಿಳಾಸ</a>\n'),
    ('Call +91 99454 20100</a>', 'ಕರೆ ಮಾಡಿ +91 99454 20100</a>'),
    ('Message on WhatsApp</a>', 'ವಾಟ್ಸಾಪ್ ಸಂದೇಶ ಕಳುಹಿಸಿ</a>'),
    ('<span class="veg">VEG</span><span class="nonveg">NON VEG</span>', '<span class="veg">ಸಸ್ಯಾಹಾರ</span><span class="nonveg">ಮಾಂಸಾಹಾರ</span>'),
    ('<nav class="mobile-bar" aria-label="Quick contact">', '<nav class="mobile-bar" aria-label="ತ್ವರಿತ ಸಂಪರ್ಕ">'),
    ('</svg>Call</a>', '</svg>ಕರೆ</a>'),
    ('</svg>WhatsApp</a>', '</svg>ವಾಟ್ಸಾಪ್</a>'),
    ('<a href="https://wa.me/919945420100">WhatsApp</a>', '<a href="https://wa.me/919945420100">ವಾಟ್ಸಾಪ್</a>'),
    ('<h3>Free hall for 500+ guests with our catering</h3><p>Book Srishti Caterers for more than 500 guests and you don\'t pay for the hall.</p>',
     '<h3>ನಮ್ಮ ಕ್ಯಾಟರಿಂಗ್ ಜೊತೆ 500+ ಅತಿಥಿಗಳಿಗೆ ಹಾಲ್ ಉಚಿತ</h3><p>500ಕ್ಕೂ ಹೆಚ್ಚು ಅತಿಥಿಗಳಿಗೆ ಸೃಷ್ಟಿ ಕ್ಯಾಟರರ್ಸ್ ಬುಕ್ ಮಾಡಿದರೆ ಹಾಲ್‌ಗೆ ಬಾಡಿಗೆ ಇಲ್ಲ.</p>'),
    ('>Check your date</a>', '>ನಿಮ್ಮ ದಿನಾಂಕ ಪರಿಶೀಲಿಸಿ</a>'),
    ('<h3>In-house catering</h3><p>Cooked on site for every function at Srishti Garden.</p>',
     '<h3>ಹಾಲ್‌ನಲ್ಲೇ ಕ್ಯಾಟರಿಂಗ್</h3><p>ಸೃಷ್ಟಿ ಗಾರ್ಡನ್‌ನ ಪ್ರತಿಯೊಂದು ಸಮಾರಂಭಕ್ಕೂ ಸ್ಥಳದಲ್ಲೇ ಅಡುಗೆ.</p>'),
    ('<h3>Outdoor catering</h3><p>We cater at your home or any venue.</p>',
     '<h3>ಹೊರಾಂಗಣ ಕ್ಯಾಟರಿಂಗ್</h3><p>ನಿಮ್ಮ ಮನೆಯಲ್ಲಿ ಅಥವಾ ಯಾವುದೇ ಸ್ಥಳದಲ್ಲಿ ಕ್ಯಾಟರಿಂಗ್.</p>'),
    ('<h3>Menus for your event</h3><p>Share your event and guest count - we\'ll suggest a menu.</p>',
     '<h3>ನಿಮ್ಮ ಕಾರ್ಯಕ್ರಮಕ್ಕೆ ಮೆನು</h3><p>ಕಾರ್ಯಕ್ರಮ ಮತ್ತು ಅತಿಥಿಗಳ ಸಂಖ್ಯೆ ತಿಳಿಸಿ - ನಾವು ಮೆನು ಸೂಚಿಸುತ್ತೇವೆ.</p>'),
    ('<a href="https://www.instagram.com/srishtigardenhall/" rel="noopener">Instagram</a>', '<a href="https://www.instagram.com/srishtigardenhall/" rel="noopener">Instagram</a>'),
    ('<a href="tel:+919945420100">+91 99454 20100</a> &middot;', '<a href="tel:+919945420100">+91 99454 20100</a> &middot;'),
    (WA_CAT_EN, WA_CAT_KN),
]

HOME = [
    ('<html lang="en">', '<html lang="kn">'),
    ('<title>Srishti Garden Hall, Moodbidri – Wedding Hall &amp; Caterers</title>', '<title>ಸೃಷ್ಟಿ ಗಾರ್ಡನ್ ಹಾಲ್, ಮೂಡುಬಿದಿರೆ – ಮದುವೆ ಹಾಲ್ ಮತ್ತು ಕ್ಯಾಟರಿಂಗ್</title>'),
    ('<meta name="description" content="Celebrate at Srishti Garden, a family-run wedding hall in Moodbidri. The hall is free when you choose our veg or non-veg catering for more than 500 guests. Two grand halls, parking, full power back-up.">',
     '<meta name="description" content="ಮೂಡುಬಿದಿರೆಯ ಸೃಷ್ಟಿ ಗಾರ್ಡನ್ - ಕುಟುಂಬದವರು ನಡೆಸುವ ಮದುವೆ ಹಾಲ್. 500ಕ್ಕೂ ಹೆಚ್ಚು ಅತಿಥಿಗಳಿಗೆ ನಮ್ಮ ಸಸ್ಯಾಹಾರ ಅಥವಾ ಮಾಂಸಾಹಾರ ಕ್ಯಾಟರಿಂಗ್ ಆರಿಸಿದರೆ ಹಾಲ್ ಉಚಿತ. ಎರಡು ಭವ್ಯ ಸಭಾಂಗಣಗಳು, ಪಾರ್ಕಿಂಗ್, ಪೂರ್ಣ ಪವರ್ ಬ್ಯಾಕಪ್.">'),
    (f'<link rel="canonical" href="{BASE}/">', f'<link rel="canonical" href="{BASE}/kn/">'),
    ('<meta property="og:title" content="Srishti Garden Hall, Moodbidri – Wedding Hall &amp; Caterers">', '<meta property="og:title" content="ಸೃಷ್ಟಿ ಗಾರ್ಡನ್ ಹಾಲ್, ಮೂಡುಬಿದಿರೆ – ಮದುವೆ ಹಾಲ್ ಮತ್ತು ಕ್ಯಾಟರಿಂಗ್">'),
    ('<meta property="og:description" content="Family-run wedding hall in Alangar, Moodbidri. Two banquet halls with 1,000 person capacity each. Call or WhatsApp to book.">',
     '<meta property="og:description" content="ಅಲಂಗಾರು, ಮೂಡುಬಿದಿರೆಯ ಕುಟುಂಬದವರು ನಡೆಸುವ ಮದುವೆ ಹಾಲ್. ತಲಾ 1,000 ಅತಿಥಿಗಳ ಎರಡು ಸಭಾಂಗಣಗಳು. ಬುಕಿಂಗ್‌ಗೆ ಕರೆ ಅಥವಾ ವಾಟ್ಸಾಪ್ ಮಾಡಿ.">'),
    (f'<meta property="og:url" content="{BASE}/">', f'<meta property="og:url" content="{BASE}/kn/">'),
    ('<meta property="og:image:alt" content="Srishti Garden Multipurpose Hall building in Moodbidri">', '<meta property="og:image:alt" content="ಮೂಡುಬಿದಿರೆಯ ಸೃಷ್ಟಿ ಗಾರ್ಡನ್ ಆ್ಯಂಡ್ ಮಲ್ಟಿಪರ್ಪಸ್ ಹಾಲ್ ಕಟ್ಟಡ">'),
    ('<meta property="og:locale" content="en_IN">', '<meta property="og:locale" content="kn_IN">'),
    ('<a href="/catering/">Catering</a>', '<a href="/kn/catering/">ಕ್ಯಾಟರಿಂಗ್</a>'),
    ('<p class="place">Moodbidri</p>', '<p class="place">ಮೂಡುಬಿದಿರೆ</p>'),
    ('<h1>Srishti Garden and<br>Multipurpose Hall</h1>', '<h1>ಸೃಷ್ಟಿ ಗಾರ್ಡನ್ ಆ್ಯಂಡ್<br>ಮಲ್ಟಿಪರ್ಪಸ್ ಹಾಲ್</h1>'),
    ('<p class="lede">The best wedding and function hall in Moodbidri. Two grand halls, our own catering, and a family team that looks after every detail.</p>',
     '<p class="lede">ಮೂಡುಬಿದಿರೆಯ ಅತ್ಯುತ್ತಮ ಮದುವೆ ಮತ್ತು ಸಮಾರಂಭ ಹಾಲ್. ಎರಡು ಭವ್ಯ ಸಭಾಂಗಣಗಳು, ನಮ್ಮದೇ ಕ್ಯಾಟರಿಂಗ್, ಮತ್ತು ಪ್ರತಿಯೊಂದು ವಿಷಯವನ್ನೂ ನೋಡಿಕೊಳ್ಳುವ ನಮ್ಮ ಕುಟುಂಬದ ತಂಡ.</p>'),
    ('<p class="events">Wedding &middot; Reception &middot; Engagement &middot; Corporate events</p>', '<p class="events">ಮದುವೆ &middot; ಆರತಕ್ಷತೆ &middot; ನಿಶ್ಚಿತಾರ್ಥ &middot; ಕಾರ್ಪೊರೇಟ್ ಕಾರ್ಯಕ್ರಮಗಳು</p>'),
    (WA_BOOK_EN, WA_BOOK_KN),
    ('alt="Srishti Garden Multipurpose Hall building in Moodbidri" fetchpriority', 'alt="ಮೂಡುಬಿದಿರೆಯ ಸೃಷ್ಟಿ ಗಾರ್ಡನ್ ಆ್ಯಂಡ್ ಮಲ್ಟಿಪರ್ಪಸ್ ಹಾಲ್ ಕಟ್ಟಡ" fetchpriority'),
    ('<ul class="wrap" aria-label="Highlights">', '<ul class="wrap" aria-label="ಮುಖ್ಯಾಂಶಗಳು">'),
    ('<li>2 halls &middot; 1,000 guests each</li>', '<li>2 ಸಭಾಂಗಣಗಳು &middot; ತಲಾ 1,000 ಅತಿಥಿಗಳು</li>'),
    ('<li><a href="/catering/">Veg and non-veg catering</a></li>', '<li><a href="/kn/catering/">ಸಸ್ಯಾಹಾರ ಮತ್ತು ಮಾಂಸಾಹಾರ ಕ್ಯಾಟರಿಂಗ್</a></li>'),
    ('<li>Ample parking</li>', '<li>ವಿಶಾಲ ಪಾರ್ಕಿಂಗ್</li>'),
    ('<li>Full power back-up</li>', '<li>ಪೂರ್ಣ ಪವರ್ ಬ್ಯಾಕಪ್</li>'),
    ('<li>500+ events hosted</li>', '<li>500ಕ್ಕೂ ಹೆಚ್ಚು ಕಾರ್ಯಕ್ರಮಗಳು</li>'),
    ('<span class="eyebrow">The Venue</span>', '<span class="eyebrow">ಸಭಾಂಗಣ</span>'),
    ('<h2>Room for everyone you love</h2>', '<h2>ನಿಮ್ಮ ಪ್ರೀತಿಪಾತ್ರರೆಲ್ಲರಿಗೂ ಸ್ಥಳಾವಕಾಶ</h2>'),
    ('<p class="intro">From intimate engagements to 1,000-guest weddings - space, food, and parking, all in one place.</p>',
     '<p class="intro">ಸರಳ ನಿಶ್ಚಿತಾರ್ಥದಿಂದ 1,000 ಅತಿಥಿಗಳ ಮದುವೆಯವರೆಗೆ - ಸ್ಥಳ, ಊಟ, ಪಾರ್ಕಿಂಗ್ ಎಲ್ಲವೂ ಒಂದೇ ಕಡೆ.</p>'),
    ('alt="Srishti Garden lit up at dusk for a wedding"', 'alt="ಮದುವೆಗಾಗಿ ಸಂಜೆ ದೀಪಗಳಿಂದ ಅಲಂಕೃತ ಸೃಷ್ಟಿ ಗಾರ್ಡನ್"'),
    ('<h3>2 grand banquet halls</h3><p>Up to 1,000 guests each. Ceremony in one, dinner in the other.</p>',
     '<h3>2 ಭವ್ಯ ಸಭಾಂಗಣಗಳು</h3><p>ತಲಾ 1,000 ಅತಿಥಿಗಳು. ಒಂದರಲ್ಲಿ ಮುಹೂರ್ತ, ಇನ್ನೊಂದರಲ್ಲಿ ಊಟ.</p>'),
    ('<h3>Our own catering</h3><p>Veg and non-veg, cooked on site by Srishti Caterers.</p>',
     '<h3>ನಮ್ಮದೇ ಕ್ಯಾಟರಿಂಗ್</h3><p>ಸೃಷ್ಟಿ ಕ್ಯಾಟರರ್ಸ್ ಸ್ಥಳದಲ್ಲೇ ತಯಾರಿಸುವ ಸಸ್ಯಾಹಾರ ಮತ್ತು ಮಾಂಸಾಹಾರ.</p>'),
    ('<h3>Bride and groom rooms</h3><p>Private dressing rooms, steps from the stage.</p>',
     '<h3>ವಧು-ವರರ ಕೊಠಡಿಗಳು</h3><p>ವೇದಿಕೆಯ ಪಕ್ಕದಲ್ಲೇ ಖಾಸಗಿ ಡ್ರೆಸ್ಸಿಂಗ್ ಕೊಠಡಿಗಳು.</p>'),
    ('<h3>Parking for everyone</h3><p>A spacious on-site car park for all your guests.</p>',
     '<h3>ಎಲ್ಲರಿಗೂ ಪಾರ್ಕಿಂಗ್</h3><p>ನಿಮ್ಮ ಎಲ್ಲಾ ಅತಿಥಿಗಳಿಗೆ ವಿಶಾಲ ಪಾರ್ಕಿಂಗ್ ಸ್ಥಳ.</p>'),
    ('<h3>Full power back-up</h3><p>Full back-up, so the lights and music never stop.</p>',
     '<h3>ಪೂರ್ಣ ಪವರ್ ಬ್ಯಾಕಪ್</h3><p>ಲೈಟ್ ಮತ್ತು ಸಂಗೀತ ಎಂದಿಗೂ ನಿಲ್ಲುವುದಿಲ್ಲ.</p>'),
    ('<h3>500+ celebrations</h3><p>Five years of weddings and functions. Rated 4.5 on WeddingBazaar.</p>',
     '<h3>500+ ಸಂಭ್ರಮಗಳು</h3><p>ಐದು ವರ್ಷಗಳ ಮದುವೆ ಮತ್ತು ಸಮಾರಂಭಗಳು. WeddingBazaar ನಲ್ಲಿ 4.5 ರೇಟಿಂಗ್.</p>'),
    ('<span class="eyebrow">Check availability</span>', '<span class="eyebrow">ಲಭ್ಯತೆ ಪರಿಶೀಲಿಸಿ</span>'),
    ('<h2>Is your date still free?</h2>', '<h2>ನಿಮ್ಮ ದಿನಾಂಕ ಇನ್ನೂ ಖಾಲಿ ಇದೆಯೇ?</h2>'),
    ("<p class=\"intro\">Dates go quickly. Share a few details and we'll confirm on WhatsApp.</p>",
     '<p class="intro">ದಿನಾಂಕಗಳು ಬೇಗ ಬುಕ್ ಆಗುತ್ತವೆ. ಕೆಲವು ವಿವರ ತಿಳಿಸಿ, ವಾಟ್ಸಾಪ್‌ನಲ್ಲಿ ನಾವು ಖಚಿತಪಡಿಸುತ್ತೇವೆ.</p>'),
    ('</svg>Two halls of up to 1,000 guests each</li>', '</svg>ತಲಾ 1,000 ಅತಿಥಿಗಳ ಎರಡು ಸಭಾಂಗಣಗಳು</li>'),
    ('</svg>Hall and catering in one booking</li>', '</svg>ಹಾಲ್ ಮತ್ತು ಕ್ಯಾಟರಿಂಗ್ ಒಂದೇ ಬುಕಿಂಗ್‌ನಲ್ಲಿ</li>'),
    ('</svg>Your enquiry goes straight to our WhatsApp</li>', '</svg>ನಿಮ್ಮ ವಿಚಾರಣೆ ನೇರವಾಗಿ ನಮ್ಮ ವಾಟ್ಸಾಪ್‌ಗೆ</li>'),
    ('<p class="enquiry-call">Prefer to talk?<a', '<p class="enquiry-call">ಮಾತನಾಡಲು ಬಯಸುವಿರಾ?<a'),
    ('<p class="form-title">Tell us about your event</p>', '<p class="form-title">ನಿಮ್ಮ ಕಾರ್ಯಕ್ರಮದ ಬಗ್ಗೆ ತಿಳಿಸಿ</p>'),
    ('<label for="eq-name">Your name</label>', '<label for="eq-name">ನಿಮ್ಮ ಹೆಸರು</label>'),
    ('placeholder="Full name"', 'placeholder="ಪೂರ್ಣ ಹೆಸರು"'),
    ('<label for="eq-type">Event type</label>', '<label for="eq-type">ಕಾರ್ಯಕ್ರಮದ ಪ್ರಕಾರ</label>'),
    ('<option>Wedding</option>', '<option>ಮದುವೆ</option>'),
    ('<option>Reception</option>', '<option>ಆರತಕ್ಷತೆ</option>'),
    ('<option>Engagement</option>', '<option>ನಿಶ್ಚಿತಾರ್ಥ</option>'),
    ('<option>Corporate event</option>', '<option>ಕಾರ್ಪೊರೇಟ್ ಕಾರ್ಯಕ್ರಮ</option>'),
    ('<option>Family function</option>', '<option>ಕುಟುಂಬ ಸಮಾರಂಭ</option>'),
    ('<option>Other</option>', '<option>ಇತರೆ</option>'),
    ('<label for="eq-date">Event date</label>', '<label for="eq-date">ಕಾರ್ಯಕ್ರಮದ ದಿನಾಂಕ</label>'),
    ('<label for="eq-guests">Approx. guests</label>', '<label for="eq-guests">ಅಂದಾಜು ಅತಿಥಿಗಳು</label>'),
    ('<span class="long">Check availability on WhatsApp</span><span class="short">Send on WhatsApp</span>',
     '<span class="long">ವಾಟ್ಸಾಪ್‌ನಲ್ಲಿ ಲಭ್ಯತೆ ಪರಿಶೀಲಿಸಿ</span><span class="short">ವಾಟ್ಸಾಪ್‌ನಲ್ಲಿ ಕಳುಹಿಸಿ</span>'),
    ('<p class="note">Opens WhatsApp with your message ready to send.</p>', '<p class="note">ನಿಮ್ಮ ಸಂದೇಶ ಸಿದ್ಧವಾಗಿ ವಾಟ್ಸಾಪ್ ತೆರೆಯುತ್ತದೆ.</p>'),
    ('<span class="eyebrow">Reviews</span>', '<span class="eyebrow">ವಿಮರ್ಶೆಗಳು</span>'),
    ('<h2>What our guests say</h2>', '<h2>ನಮ್ಮ ಅತಿಥಿಗಳು ಏನು ಹೇಳುತ್ತಾರೆ</h2>'),
    ("<p class=\"summary\">500+ celebrations and counting. Here's what families say.</p>", '<p class="summary">500ಕ್ಕೂ ಹೆಚ್ಚು ಸಂಭ್ರಮಗಳು. ಕುಟುಂಬಗಳ ಮಾತು ಇಲ್ಲಿದೆ.</p>'),
    ('aria-label="4.2 out of 5 stars"', 'aria-label="5 ರಲ್ಲಿ 4.2 ನಕ್ಷತ್ರಗಳು"'),
    ('aria-label="4.5 out of 5 stars"', 'aria-label="5 ರಲ್ಲಿ 4.5 ನಕ್ಷತ್ರಗಳು"'),
    ('aria-label="5 out of 5 stars"', 'aria-label="5 ರಲ್ಲಿ 5 ನಕ್ಷತ್ರಗಳು"'),
    ('<span class="rsource">97 Google reviews</span>', '<span class="rsource">97 Google ವಿಮರ್ಶೆಗಳು</span>'),
    ('<span class="rsource">Rated on WeddingBazaar</span>', '<span class="rsource">WeddingBazaar ರೇಟಿಂಗ್</span>'),
    (', Google review</figcaption>', ', Google ವಿಮರ್ಶೆ</figcaption>'),
    ('>Read all 97 reviews on Google</a>', '>Google ನಲ್ಲಿ ಎಲ್ಲಾ 97 ವಿಮರ್ಶೆಗಳನ್ನು ಓದಿ</a>'),
    ('<span class="eyebrow">Srishti Caterers</span>', '<span class="eyebrow">ಸೃಷ್ಟಿ ಕ್ಯಾಟರರ್ಸ್</span>'),
    ('<h2>Food your guests will remember</h2>', '<h2>ಅತಿಥಿಗಳು ನೆನಪಿಡುವ ಊಟ</h2>'),
    ('<p class="tagline">Elevate your events with our exquisite flavours.</p>', '<p class="tagline">ನಮ್ಮ ವಿಶೇಷ ರುಚಿಗಳಿಂದ ನಿಮ್ಮ ಸಮಾರಂಭಕ್ಕೆ ಮೆರುಗು.</p>'),
    ('<p class="intro">Veg and non-veg from our own kitchen - at our hall or at your venue.</p>',
     '<p class="intro">ನಮ್ಮದೇ ಅಡುಗೆಮನೆಯ ಸಸ್ಯಾಹಾರ ಮತ್ತು ಮಾಂಸಾಹಾರ - ನಮ್ಮ ಹಾಲ್‌ನಲ್ಲಿ ಅಥವಾ ನಿಮ್ಮ ಸ್ಥಳದಲ್ಲಿ.</p>'),
    ('<a class="btn-call" href="/catering/">See catering details</a>', '<a class="btn-call" href="/kn/catering/">ಕ್ಯಾಟರಿಂಗ್ ವಿವರ ನೋಡಿ</a>'),
    ('>Ask about catering on WhatsApp</a>', '>ಕ್ಯಾಟರಿಂಗ್ ಬಗ್ಗೆ ವಾಟ್ಸಾಪ್‌ನಲ್ಲಿ ಕೇಳಿ</a>'),
    ('<span class="eyebrow">Gallery</span>', '<span class="eyebrow">ಗ್ಯಾಲರಿ</span>'),
    ('<h2>Picture your celebration here</h2>', '<h2>ನಿಮ್ಮ ಸಂಭ್ರಮವನ್ನು ಇಲ್ಲಿ ಕಲ್ಪಿಸಿಕೊಳ್ಳಿ</h2>'),
    ('alt="Front view of the venue"', 'alt="ಸಭಾಂಗಣದ ಮುಂಭಾಗ"'),
    ('alt="Decorated wedding stage with mandap pillars"', 'alt="ಮಂಟಪ ಕಂಬಗಳೊಂದಿಗೆ ಅಲಂಕರಿಸಿದ ಮದುವೆ ವೇದಿಕೆ"'),
    ('alt="Wedding stage with floral arch and seating"', 'alt="ಹೂವಿನ ಕಮಾನು ಮತ್ತು ಆಸನಗಳಿರುವ ಮದುವೆ ವೇದಿಕೆ"'),
    ('alt="Venue exterior in the evening"', 'alt="ಸಂಜೆಯ ವೇಳೆ ಸಭಾಂಗಣದ ಹೊರನೋಟ"'),
    ('alt="Stage decorated for a family function"', 'alt="ಕುಟುಂಬ ಸಮಾರಂಭಕ್ಕೆ ಅಲಂಕರಿಸಿದ ವೇದಿಕೆ"'),
    ('alt="Venue entrance with Srishti Garden sign"', 'alt="ಸೃಷ್ಟಿ ಗಾರ್ಡನ್ ಫಲಕವಿರುವ ಪ್ರವೇಶದ್ವಾರ"'),
    ('<p style="margin-top:1.5rem">More photos on <a href="https://www.instagram.com/srishtigardenhall/" rel="noopener">Instagram @srishtigardenhall</a>.</p>',
     '<p style="margin-top:1.5rem">ಇನ್ನಷ್ಟು ಫೋಟೋಗಳು <a href="https://www.instagram.com/srishtigardenhall/" rel="noopener">Instagram @srishtigardenhall</a> ನಲ್ಲಿ.</p>'),
    ('<span class="eyebrow">Location</span>', '<span class="eyebrow">ವಿಳಾಸ</span>'),
    ('<h2>Easy to reach, easy to park</h2>', '<h2>ತಲುಪಲು ಸುಲಭ, ಪಾರ್ಕಿಂಗ್ ಸುಲಭ</h2>'),
    ('''            <strong>Srishti Garden and Multipurpose Hall</strong><br>
            Ontikatte, Alangar<br>
            Near Kadalakere Nisargadhama<br>
            Moodbidri, Karnataka 574227''',
     '''            <strong>ಸೃಷ್ಟಿ ಗಾರ್ಡನ್ ಆ್ಯಂಡ್ ಮಲ್ಟಿಪರ್ಪಸ್ ಹಾಲ್</strong><br>
            ಒಂಟಿಕಟ್ಟೆ, ಅಲಂಗಾರು<br>
            ಕಡಲಕೆರೆ ನಿಸರ್ಗಧಾಮದ ಹತ್ತಿರ<br>
            ಮೂಡುಬಿದಿರೆ, ಕರ್ನಾಟಕ 574227'''),
    ('<li>Call: <a', '<li>ಕರೆ: <a'),
    ('<li>Alternate: <a', '<li>ಪರ್ಯಾಯ ಸಂಖ್ಯೆ: <a'),
    ('<li>WhatsApp: <a', '<li>ವಾಟ್ಸಾಪ್: <a'),
    ('rel="noopener">Get directions</a>', 'rel="noopener">ದಾರಿ ತಿಳಿಯಿರಿ</a>'),
    ('title="Map showing Srishti Garden and Multipurpose Hall, Moodbidri"', 'title="ಮೂಡುಬಿದಿರೆಯ ಸೃಷ್ಟಿ ಗಾರ್ಡನ್ ನಕ್ಷೆ"'),
    ('<p>Srishti Garden and Multipurpose Hall &middot; Moodbidri <span class="marigold">&#10047;</span> Family owned and run</p>',
     '<p>ಸೃಷ್ಟಿ ಗಾರ್ಡನ್ ಆ್ಯಂಡ್ ಮಲ್ಟಿಪರ್ಪಸ್ ಹಾಲ್ &middot; ಮೂಡುಬಿದಿರೆ <span class="marigold">&#10047;</span> ಕುಟುಂಬದ ಮಾಲೀಕತ್ವ ಮತ್ತು ನಿರ್ವಹಣೆ</p>'),
    ('<a href="/catering/">Srishti Caterers</a>', '<a href="/kn/catering/">ಸೃಷ್ಟಿ ಕ್ಯಾಟರರ್ಸ್</a>'),
    ('<dialog class="lightbox" id="lightbox" aria-label="Photo viewer">', '<dialog class="lightbox" id="lightbox" aria-label="ಫೋಟೋ ವೀಕ್ಷಕ">'),
    ('aria-label="Previous photo"', 'aria-label="ಹಿಂದಿನ ಫೋಟೋ"'),
    ('aria-label="Next photo"', 'aria-label="ಮುಂದಿನ ಫೋಟೋ"'),
    ('aria-label="Close"', 'aria-label="ಮುಚ್ಚಿ"'),
    # WhatsApp message built by the form
    ("var lines = ['Hi, I\\'d like to check availability at Srishti Garden.'];", "var lines = ['ನಮಸ್ಕಾರ, ಸೃಷ್ಟಿ ಗಾರ್ಡನ್‌ನಲ್ಲಿ ದಿನಾಂಕ ಲಭ್ಯತೆ ತಿಳಿಯಬೇಕಿತ್ತು.'];"),
    ("lines.push('Name: ' + name);", "lines.push('ಹೆಸರು: ' + name);"),
    ("lines.push('Date: ' + dt.toLocaleDateString('en-IN',", "lines.push('ದಿನಾಂಕ: ' + dt.toLocaleDateString('kn-IN',"),
    ("lines.push('Event: ' + type);", "lines.push('ಕಾರ್ಯಕ್ರಮ: ' + type);"),
    ("lines.push('Guests: about ' + guests);", "lines.push('ಅತಿಥಿಗಳು: ಸುಮಾರು ' + guests);"),
]

CAT = [
    ('<html lang="en">', '<html lang="kn">'),
    ('<a class="skip" href="#services">Skip to content</a>', '<a class="skip" href="#services">ಮುಖ್ಯ ವಿಷಯಕ್ಕೆ ಹೋಗಿ</a>'),
    ('<title>Srishti Caterers – Veg and Non-Veg Catering, Moodbidri</title>', '<title>ಸೃಷ್ಟಿ ಕ್ಯಾಟರರ್ಸ್ – ಸಸ್ಯಾಹಾರ ಮತ್ತು ಮಾಂಸಾಹಾರ ಕ್ಯಾಟರಿಂಗ್, ಮೂಡುಬಿದಿರೆ</title>'),
    (f'<link rel="canonical" href="{BASE}/catering/">', f'<link rel="canonical" href="{BASE}/kn/catering/">'),
    ('<meta property="og:title" content="Srishti Caterers – Veg and Non-Veg Catering, Moodbidri">', '<meta property="og:title" content="ಸೃಷ್ಟಿ ಕ್ಯಾಟರರ್ಸ್ – ಸಸ್ಯಾಹಾರ ಮತ್ತು ಮಾಂಸಾಹಾರ ಕ್ಯಾಟರಿಂಗ್, ಮೂಡುಬಿದಿರೆ">'),
    (f'<meta property="og:url" content="{BASE}/catering/">', f'<meta property="og:url" content="{BASE}/kn/catering/">'),
    ('<meta property="og:locale" content="en_IN">', '<meta property="og:locale" content="kn_IN">'),
    ('<a class="brand" href="/">', '<a class="brand" href="/kn/">'),
    ('<a href="/#venue">', '<a href="/kn/#venue">'),
    ('<a href="/catering/" aria-current="page">', '<a href="/kn/catering/" aria-current="page">'),
    ('<a class="nav-gallery" href="/#gallery">', '<a class="nav-gallery" href="/kn/#gallery">'),
    ('<a href="/#location">', '<a href="/kn/#location">'),
    ('<p class="place">Srishti Caterers &middot; Moodbidri</p>', '<p class="place">ಸೃಷ್ಟಿ ಕ್ಯಾಟರರ್ಸ್ &middot; ಮೂಡುಬಿದಿರೆ</p>'),
    ('<h1>Veg and non-veg catering in Moodbidri</h1>', '<h1>ಮೂಡುಬಿದಿರೆಯಲ್ಲಿ ಸಸ್ಯಾಹಾರ ಮತ್ತು ಮಾಂಸಾಹಾರ ಕ್ಯಾಟರಿಂಗ್</h1>'),
    ('<p class="lede">Elevate your events with our exquisite flavours - at Srishti Garden or wherever you celebrate.</p>',
     '<p class="lede">ನಮ್ಮ ವಿಶೇಷ ರುಚಿಗಳಿಂದ ನಿಮ್ಮ ಸಮಾರಂಭಕ್ಕೆ ಮೆರುಗು - ಸೃಷ್ಟಿ ಗಾರ್ಡನ್‌ನಲ್ಲಿ ಅಥವಾ ನೀವು ಆಚರಿಸುವ ಯಾವುದೇ ಸ್ಥಳದಲ್ಲಿ.</p>'),
    ('<div class="wrap crumbs"><a href="/">Srishti Garden Hall</a> &rsaquo; Catering</div>', '<div class="wrap crumbs"><a href="/kn/">ಸೃಷ್ಟಿ ಗಾರ್ಡನ್ ಹಾಲ್</a> &rsaquo; ಕ್ಯಾಟರಿಂಗ್</div>'),
    ('<span class="eyebrow">What we offer</span>', '<span class="eyebrow">ನಮ್ಮ ಸೇವೆಗಳು</span>'),
    ('<h2>Catering by Srishti Caterers</h2>', '<h2>ಸೃಷ್ಟಿ ಕ್ಯಾಟರರ್ಸ್ ಕ್ಯಾಟರಿಂಗ್</h2>'),
    ('<p class="intro">The in-house kitchen of Srishti Garden, Alangar, Moodbidri. We cater at our hall and at yours.</p>',
     '<p class="intro">ಅಲಂಗಾರು, ಮೂಡುಬಿದಿರೆಯ ಸೃಷ್ಟಿ ಗಾರ್ಡನ್‌ನ ಸ್ವಂತ ಅಡುಗೆಮನೆ. ನಮ್ಮ ಹಾಲ್‌ನಲ್ಲೂ ನಿಮ್ಮ ಸ್ಥಳದಲ್ಲೂ ಕ್ಯಾಟರಿಂಗ್.</p>'),
    ('href="/#enquire">', 'href="/kn/#enquire">'),
    ('<span class="eyebrow">Events we cater</span>', '<span class="eyebrow">ನಾವು ಕ್ಯಾಟರ್ ಮಾಡುವ ಕಾರ್ಯಕ್ರಮಗಳು</span>'),
    ('<h2>For every celebration, big or small</h2>', '<h2>ದೊಡ್ಡದಿರಲಿ ಸಣ್ಣದಿರಲಿ, ಪ್ರತಿಯೊಂದು ಸಂಭ್ರಮಕ್ಕೂ</h2>'),
    ('<li>Weddings</li>', '<li>ಮದುವೆ</li>'),
    ('<li>Receptions</li>', '<li>ಆರತಕ್ಷತೆ</li>'),
    ('<li>Engagements</li>', '<li>ನಿಶ್ಚಿತಾರ್ಥ</li>'),
    ('<li>Baby showers</li>', '<li>ಸೀಮಂತ</li>'),
    ('<li>Corporate events</li>', '<li>ಕಾರ್ಪೊರೇಟ್ ಕಾರ್ಯಕ್ರಮಗಳು</li>'),
    ('<li>Family functions</li>', '<li>ಕುಟುಂಬ ಸಮಾರಂಭಗಳು</li>'),
    ('<span class="eyebrow">Questions</span>', '<span class="eyebrow">ಪ್ರಶ್ನೆಗಳು</span>'),
    ('<h2>Catering FAQs</h2>', '<h2>ಕ್ಯಾಟರಿಂಗ್ ಬಗ್ಗೆ ಪ್ರಶ್ನೆಗಳು</h2>'),
    ('<summary>Is the hall free if we book your catering?</summary>', '<summary>ನಿಮ್ಮ ಕ್ಯಾಟರಿಂಗ್ ಬುಕ್ ಮಾಡಿದರೆ ಹಾಲ್ ಉಚಿತವೇ?</summary>'),
    ('<p>Yes. When you choose Srishti Caterers for more than 500 guests, the hall at Srishti Garden is free. Call or WhatsApp <a href="tel:+919945420100">+91 99454 20100</a> to check your date.</p>',
     '<p>ಹೌದು. 500ಕ್ಕೂ ಹೆಚ್ಚು ಅತಿಥಿಗಳಿಗೆ ಸೃಷ್ಟಿ ಕ್ಯಾಟರರ್ಸ್ ಆರಿಸಿದರೆ ಸೃಷ್ಟಿ ಗಾರ್ಡನ್ ಹಾಲ್ ಉಚಿತ. ನಿಮ್ಮ ದಿನಾಂಕ ಪರಿಶೀಲಿಸಲು <a href="tel:+919945420100">+91 99454 20100</a> ಗೆ ಕರೆ ಅಥವಾ ವಾಟ್ಸಾಪ್ ಮಾಡಿ.</p>'),
    ('<summary>Do you serve both veg and non-veg food?</summary>', '<summary>ಸಸ್ಯಾಹಾರ ಮತ್ತು ಮಾಂಸಾಹಾರ ಎರಡೂ ಲಭ್ಯವಿದೆಯೇ?</summary>'),
    ('<p>Yes. Srishti Caterers prepare both veg and non-veg menus.</p>', '<p>ಹೌದು. ಸೃಷ್ಟಿ ಕ್ಯಾಟರರ್ಸ್ ಸಸ್ಯಾಹಾರ ಮತ್ತು ಮಾಂಸಾಹಾರ ಎರಡೂ ಮೆನುಗಳನ್ನು ತಯಾರಿಸುತ್ತಾರೆ.</p>'),
    ('<summary>Can you cater at another venue or at home?</summary>', '<summary>ಬೇರೆ ಸ್ಥಳದಲ್ಲಿ ಅಥವಾ ಮನೆಯಲ್ಲಿ ಕ್ಯಾಟರ್ ಮಾಡುತ್ತೀರಾ?</summary>'),
    ('<p>Yes. Along with in-house catering at Srishti Garden Hall, we offer outdoor catering at your venue.</p>',
     '<p>ಹೌದು. ಸೃಷ್ಟಿ ಗಾರ್ಡನ್ ಹಾಲ್‌ನಲ್ಲಿನ ಕ್ಯಾಟರಿಂಗ್ ಜೊತೆಗೆ, ನಿಮ್ಮ ಸ್ಥಳದಲ್ಲೂ ಹೊರಾಂಗಣ ಕ್ಯಾಟರಿಂಗ್ ಒದಗಿಸುತ್ತೇವೆ.</p>'),
    ('<summary>What kinds of events do you cater?</summary>', '<summary>ಯಾವೆಲ್ಲಾ ಕಾರ್ಯಕ್ರಮಗಳಿಗೆ ಕ್ಯಾಟರ್ ಮಾಡುತ್ತೀರಿ?</summary>'),
    ('<p>Weddings, receptions, engagements, baby showers, corporate events, and family functions.</p>',
     '<p>ಮದುವೆ, ಆರತಕ್ಷತೆ, ನಿಶ್ಚಿತಾರ್ಥ, ಸೀಮಂತ, ಕಾರ್ಪೊರೇಟ್ ಕಾರ್ಯಕ್ರಮಗಳು ಮತ್ತು ಕುಟುಂಬ ಸಮಾರಂಭಗಳು.</p>'),
    ('<summary>How do I book catering or ask about menus?</summary>', '<summary>ಕ್ಯಾಟರಿಂಗ್ ಬುಕ್ ಮಾಡುವುದು ಅಥವಾ ಮೆನು ಬಗ್ಗೆ ಕೇಳುವುದು ಹೇಗೆ?</summary>'),
    ("<p>Call or WhatsApp <a href=\"tel:+919945420100\">+91 99454 20100</a> with your event date and approximate guest count, and we'll talk you through menu options.</p>",
     '<p>ನಿಮ್ಮ ಕಾರ್ಯಕ್ರಮದ ದಿನಾಂಕ ಮತ್ತು ಅಂದಾಜು ಅತಿಥಿಗಳ ಸಂಖ್ಯೆಯೊಂದಿಗೆ <a href="tel:+919945420100">+91 99454 20100</a> ಗೆ ಕರೆ ಅಥವಾ ವಾಟ್ಸಾಪ್ ಮಾಡಿ. ಮೆನು ಆಯ್ಕೆಗಳನ್ನು ನಾವು ವಿವರಿಸುತ್ತೇವೆ.</p>'),
    ("<h2>Let's plan your menu</h2>", '<h2>ನಿಮ್ಮ ಮೆನು ಯೋಜಿಸೋಣ</h2>'),
    ('<p>Hall and food in one booking - or just the catering.</p>', '<p>ಹಾಲ್ ಮತ್ತು ಊಟ ಒಂದೇ ಬುಕಿಂಗ್‌ನಲ್ಲಿ - ಅಥವಾ ಕೇವಲ ಕ್ಯಾಟರಿಂಗ್.</p>'),
    ('>WhatsApp us</a>', '>ವಾಟ್ಸಾಪ್ ಮಾಡಿ</a>'),
    ('<p style="margin:1.4rem 0 0"><a href="/">See Srishti Garden Hall</a></p>', '<p style="margin:1.4rem 0 0"><a href="/kn/">ಸೃಷ್ಟಿ ಗಾರ್ಡನ್ ಹಾಲ್ ನೋಡಿ</a></p>'),
    ('<p>Srishti Caterers &middot; Srishti Garden and Multipurpose Hall &middot; Ontikatte, Alangar, Moodbidri 574227 <span class="marigold">&#10047;</span> Family owned and run</p>',
     '<p>ಸೃಷ್ಟಿ ಕ್ಯಾಟರರ್ಸ್ &middot; ಸೃಷ್ಟಿ ಗಾರ್ಡನ್ ಆ್ಯಂಡ್ ಮಲ್ಟಿಪರ್ಪಸ್ ಹಾಲ್ &middot; ಒಂಟಿಕಟ್ಟೆ, ಅಲಂಗಾರು, ಮೂಡುಬಿದಿರೆ 574227 <span class="marigold">&#10047;</span> ಕುಟುಂಬದ ಮಾಲೀಕತ್ವ ಮತ್ತು ನಿರ್ವಹಣೆ</p>'),
]

KN_CAT_DESC = 'ಸೃಷ್ಟಿ ಕ್ಯಾಟರರ್ಸ್, ಮೂಡುಬಿದಿರೆ - 500ಕ್ಕೂ ಹೆಚ್ಚು ಅತಿಥಿಗಳಿಗೆ ನಮ್ಮ ಕ್ಯಾಟರಿಂಗ್ ಬುಕ್ ಮಾಡಿದರೆ ಹಾಲ್ ಉಚಿತ. ಮದುವೆ, ಆರತಕ್ಷತೆ, ನಿಶ್ಚಿತಾರ್ಥ ಮತ್ತು ಎಲ್ಲಾ ಸಮಾರಂಭಗಳಿಗೆ ಸಸ್ಯಾಹಾರ ಮತ್ತು ಮಾಂಸಾಹಾರ ಕ್ಯಾಟರಿಂಗ್. ಕರೆ: +91 99454 20100.'

KN_FAQ = [
    ('ನಿಮ್ಮ ಕ್ಯಾಟರಿಂಗ್ ಬುಕ್ ಮಾಡಿದರೆ ಹಾಲ್ ಉಚಿತವೇ?', 'ಹೌದು. 500ಕ್ಕೂ ಹೆಚ್ಚು ಅತಿಥಿಗಳಿಗೆ ಸೃಷ್ಟಿ ಕ್ಯಾಟರರ್ಸ್ ಆರಿಸಿದರೆ ಸೃಷ್ಟಿ ಗಾರ್ಡನ್ ಹಾಲ್ ಉಚಿತ.'),
    ('ಸಸ್ಯಾಹಾರ ಮತ್ತು ಮಾಂಸಾಹಾರ ಎರಡೂ ಲಭ್ಯವಿದೆಯೇ?', 'ಹೌದು. ಸೃಷ್ಟಿ ಕ್ಯಾಟರರ್ಸ್ ಸಸ್ಯಾಹಾರ ಮತ್ತು ಮಾಂಸಾಹಾರ ಎರಡೂ ಮೆನುಗಳನ್ನು ತಯಾರಿಸುತ್ತಾರೆ.'),
    ('ಬೇರೆ ಸ್ಥಳದಲ್ಲಿ ಅಥವಾ ಮನೆಯಲ್ಲಿ ಕ್ಯಾಟರ್ ಮಾಡುತ್ತೀರಾ?', 'ಹೌದು. ಸೃಷ್ಟಿ ಗಾರ್ಡನ್ ಹಾಲ್‌ನಲ್ಲಿನ ಕ್ಯಾಟರಿಂಗ್ ಜೊತೆಗೆ, ನಿಮ್ಮ ಸ್ಥಳದಲ್ಲೂ ಹೊರಾಂಗಣ ಕ್ಯಾಟರಿಂಗ್ ಒದಗಿಸುತ್ತೇವೆ.'),
    ('ಯಾವೆಲ್ಲಾ ಕಾರ್ಯಕ್ರಮಗಳಿಗೆ ಕ್ಯಾಟರ್ ಮಾಡುತ್ತೀರಿ?', 'ಮದುವೆ, ಆರತಕ್ಷತೆ, ನಿಶ್ಚಿತಾರ್ಥ, ಸೀಮಂತ, ಕಾರ್ಪೊರೇಟ್ ಕಾರ್ಯಕ್ರಮಗಳು ಮತ್ತು ಕುಟುಂಬ ಸಮಾರಂಭಗಳು.'),
    ('ಕ್ಯಾಟರಿಂಗ್ ಬುಕ್ ಮಾಡುವುದು ಅಥವಾ ಮೆನು ಬಗ್ಗೆ ಕೇಳುವುದು ಹೇಗೆ?', 'ನಿಮ್ಮ ಕಾರ್ಯಕ್ರಮದ ದಿನಾಂಕ ಮತ್ತು ಅಂದಾಜು ಅತಿಥಿಗಳ ಸಂಖ್ಯೆಯೊಂದಿಗೆ +91 99454 20100 ಗೆ ಕರೆ ಅಥವಾ ವಾಟ್ಸಾಪ್ ಮಾಡಿ.'),
]

def localise_assets(s):
    # relative static paths -> absolute, so they resolve from /kn/
    s = s.replace('"static/', '"/static/').replace(' static/', ' /static/').replace(',static/', ',/static/')
    return s

def lang_link(href, label, hreflang):
    return f'      <a class="lang" href="{href}" hreflang="{hreflang}" lang="{hreflang}">{label}</a>\n'

def insert_lang(s, link):
    anchor = '      <a class="call" href="tel:+919945420100">'
    assert s.count(anchor) == 1
    return s.replace(anchor, link + anchor)

def insert_after_canonical(s, extra):
    i = s.index('<link rel="canonical"')
    j = s.index('\n', i) + 1
    return s[:j] + extra + s[j:]

home = open(SRC_HOME, encoding='utf-8').read()
cat = open(SRC_CAT, encoding='utf-8').read()

# ---- Kannada home ----
kh = rep(home, HOME, 'home')
kh = rep(kh, [p for p in COMMON if kh.count(p[0])], 'home-common')
kh = localise_assets(kh)
kh = insert_after_canonical(kh, alternates(f'{BASE}/', f'{BASE}/kn/'))
kh = kh.replace('<link href="https://fonts.googleapis.com/css2?family=Fraunces', FONT_LINK + '<link href="https://fonts.googleapis.com/css2?family=Fraunces', 1)
kh = add_css(kh, LANG_CSS + KN_CSS)
kh = insert_lang(kh, lang_link('/', 'English', 'en'))

# ---- Kannada catering ----
kc = rep(cat, CAT, 'cat')
kc = rep(kc, [p for p in COMMON if kc.count(p[0])], 'cat-common')
kc = re.sub(r'<meta name="description" content="[^"]*">', f'<meta name="description" content="{KN_CAT_DESC}">', kc, count=1)
faq_json = ',\n'.join(
    '    {"@type": "Question", "name": "%s",\n     "acceptedAnswer": {"@type": "Answer", "text": "%s"}}' % (qq, aa) for qq, aa in KN_FAQ)
kc = re.sub(r'("@type": "FAQPage",\n  "mainEntity": \[\n).*?(\n  \]\n)', lambda m: m.group(1) + faq_json + m.group(2), kc, count=1, flags=re.S)
kc = localise_assets(kc)
kc = insert_after_canonical(kc, alternates(f'{BASE}/catering/', f'{BASE}/kn/catering/'))
kc = kc.replace('<link href="https://fonts.googleapis.com/css2?family=Fraunces', FONT_LINK + '<link href="https://fonts.googleapis.com/css2?family=Fraunces', 1)
kc = add_css(kc, LANG_CSS + KN_CSS)
kc = insert_lang(kc, lang_link('/catering/', 'English', 'en'))

# ---- English pages: add switch + alternates ----
eh = insert_after_canonical(home, alternates(f'{BASE}/', f'{BASE}/kn/'))
eh = add_css(eh, LANG_CSS)
eh = insert_lang(eh, lang_link('/kn/', 'ಕನ್ನಡ', 'kn'))
eh = eh.replace('<link href="https://fonts.googleapis.com/css2?family=Fraunces', '<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+Kannada:wght@700&text=%E0%B2%95%E0%B2%A8%E0%B3%8D%E0%B2%A8%E0%B2%A1&display=swap" rel="stylesheet">\n<link href="https://fonts.googleapis.com/css2?family=Fraunces', 1)
ec = insert_after_canonical(cat, alternates(f'{BASE}/catering/', f'{BASE}/kn/catering/'))
ec = add_css(ec, LANG_CSS)
ec = insert_lang(ec, lang_link('/kn/catering/', 'ಕನ್ನಡ', 'kn'))
ec = ec.replace('<link href="https://fonts.googleapis.com/css2?family=Fraunces', '<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+Kannada:wght@700&text=%E0%B2%95%E0%B2%A8%E0%B3%8D%E0%B2%A8%E0%B2%A1&display=swap" rel="stylesheet">\n<link href="https://fonts.googleapis.com/css2?family=Fraunces', 1)

for path, txt in [(OUT_HOME, kh), (OUT_CAT, kc), (EN_HOME_OUT, eh), (EN_CAT_OUT, ec)]:
    open(path, 'w', encoding='utf-8').write(txt)

# report any English left in visible Kannada text (rough check)
for label, txt in [('kn home', kh), ('kn cat', kc)]:
    body = re.sub(r'<script.*?</script>|<style.*?</style>|<[^>]+>', '\n', txt.split('<body>')[1], flags=re.S)
    left = [l.strip() for l in body.split('\n') if re.search(r'[A-Za-z]{4,}', l) and not re.search(r'[ಀ-೿]', l)]
    print(label, 'lines without Kannada:', sorted(set(left)))
print('built')
