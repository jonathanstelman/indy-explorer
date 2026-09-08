# How Many Resorts Are On The Indy Pass? An Honest Accounting

*Published 2026-09-08. Data from [Indy Explorer](https://indy-explorer.vercel.app), which scrapes
[indyskipass.com/our-resorts](https://www.indyskipass.com/our-resorts) and has kept dated snapshots
of the roster since December 2024.*

---

## The short version

As of today, **291 resorts are listed on the Indy Pass website**. Indy's marketing says **"300+."**

The gap has a clear, non-mysterious explanation: **the additions are counted, and the departures
aren't.** Since the start of last season Indy has added 58 resorts and lost 23. Add the first number
to last season's total and skip the second, and you get 314 — comfortably "300+." Do the full
arithmetic and you get 291.

This isn't an accusation, and it isn't a gotcha. Every claim Indy makes about *new* resorts checks
out against our data — the growth is real and substantial. But a pass holder deciding whether to buy
is asking a different question: *how many resorts can I actually ski this season?* Today that answer
is 291.

## What Indy claims

From indyskipass.com as of 2026-09-08:

- **"300+ Resorts"** (site header)
- **"300 Resort Guarantee"** — a stated commitment for the upcoming season, which the site says Indy
  has "surpassed"
- **"60 New Resorts announced SINCE LAST SEASON"**
- **"40+ top cross-country resorts"** for the Indy XC Pass

## What the data shows

Taking the start of last season (2025-09-20) as the baseline:

| | Resorts |
|---|---|
| Baseline — start of last season (2025-09-20) | 256 |
| Genuinely new since then | **+58** |
| Departures since then | **−23** |
| **Actual roster today (2026-09-08)** | **291** |
| For comparison — additions counted, departures ignored | *314* |

The arithmetic closes exactly: 256 + 58 − 23 = 291.

**Indy's "60 new resorts" claim is essentially correct.** We independently count 58 genuinely new
resorts over the same period. The difference between 58 and 60 is well within the resolution of our
snapshots. The growth is real, and it deserves the credit Indy gives it.

The "300+" figure is where the two accounts diverge, and the 23 departures are the entire difference.

## Roster over time

| Snapshot | Resorts | Arrivals | Departures |
|---|---|---|---|
| 2024-12-16 | 218 | — | — |
| 2025-09-01 | 252 | 45 | 11 |
| 2025-09-20 | 256 | 7 | 3 |
| 2025-12-24 | 256 | 9 | 9 |
| 2026-03-15 | 271 | 17 | 2 |
| 2026-04-21 | 277 | 8 | 2 |
| 2026-07-12 | 277 | 1 | 1 |
| **2026-09-03** | **267** | 7 | **17** |
| 2026-09-05 | 279 | 13 | 1 |
| 2026-09-08 | 291 | 12 | 0 |

*(Arrival and departure columns here are raw snapshot-to-snapshot differences and include renames and
location relabels; the filtered 58 / 23 figures above exclude those. The 2025-12-24 row, 9 in and 9
out for no net change, is almost entirely a data cleanup on Indy's end.)*

The roster genuinely grew a great deal over two years — 218 to 291 is real expansion. It also went
*down* on 2026-09-03, and that dip is what the "300+" framing doesn't capture.

## What left

Departures were not gradual attrition. **17 listings disappeared in a single update on 2026-09-03**,
which is why the roster fell from 277 to 267 that day even as 7 new resorts arrived:

> Granite Peak · Lutsen Mountains · Snowriver · Nordic Mountain · Little Switzerland · Caberfae Peaks
> · Mission Ridge · Blacktail Mountain · Kiroro Snow World · Ani · Crystal Ridge · LOGE Glacier
> · Meadowlark · Mont Habitant · Mt. Washington Nordic Centre · Tangram Ski Circus · Innsbruck

Five of those — Granite Peak, Lutsen Mountains, Snowriver, Nordic Mountain and Little Switzerland —
are Midwest Family Ski Resorts properties. That points to a portfolio-level exit rather than
independent resorts drifting away one at a time, and it removed several of the most prominent Midwest
options at once. *(Ownership is outside our dataset; that grouping comes from public knowledge, not
from the scrape.)*

Six more left at other points in the year: Hickory Ski Center, Madarao, Kurohime Kogen, Methow Trails
XC, Valmorel, and Cape Smokey.

The full list of 23, with locations, is at the end of this document.

## Corrections applied before counting

Naive diffing badly overstates churn. Three artifacts had to be filtered out, and we mention them so
others can check our work:

**Renames** (same location, new name) — 5 found, excluded from both counts:

| Old name | New name |
|---|---|
| Whitepine Mountain Resort | White Pine Resort |
| Mt. Racey Ski Resort | Mount Racey Ski Resort |
| Magic Mountain (Kimberly, ID) | Magic Mountain Idaho |
| Kaya Palazzo Kartalkaya Ski & Mountain Resort. | Kaya Palazzo Kartalkaya Ski & Mountain Resort |
| Corralco Mountain Resort | Corralco Resort de Montaña |

**Location relabels** (same resort, corrected location text) — 4 found, excluded: Destination Owls
Head (Masonville → Mansonville, QC), SkiWelt (Kufstein → Söll), Wintergreen (blank → Nellysford, VA),
High Point XC Ski Center (Millford → Sussex, NJ).

**Duplicate rows in our own older data.** Our 2025-09-20 snapshot contained four "Magic Mountain"
rows for two real resorts (Londonderry, VT and Kimberly, ID) — a bug in our pipeline that duplicated
rows whenever two resorts shared a name. It has since been fixed. Counting rows would have inflated
that baseline; counting distinct names would have merged the two real Magic Mountains into one.
Everything here is keyed on `(name, location)` instead, which handles both.

## Limitations of this analysis

Stated plainly, because they matter:

- **Our history is 10 dated snapshots over ~21 months, not a continuous record.** Any resort that
  joined and left between two snapshots is invisible to us. Both the 58 additions and the 23
  departures are *lower bounds*; real churn is somewhat higher.
- **One ambiguous case.** "Innsbruck Ski & City Network" vanished the same day "Innsbruck Region"
  appeared, but with a different location string and a different page URL on Indy's site
  (`innsbruck-ski-city-network` → `innsbruck-region`). If that's a rebrand rather than a swap, the
  true figures are 57 new and 22 departed. The conclusion doesn't change either way.
- **"Last season" is our chosen baseline** (2025-09-20). A different starting date shifts the
  arithmetic, though not the direction of the finding.
- **Indy may count resorts absent from the public `/our-resorts` page** — allied or partner
  properties, for instance. We can't rule this out. It seems unlikely to cover a 23-resort gap: our
  scrape finds only 2 allied resorts, and the "40+ cross-country" resorts Indy cites are already
  inside our 291. But it is the honest gap in the evidence.
- **The season hasn't started.** Indy may announce enough additional resorts to reach 300 legitimately
  before opening day, and the "300 Resort Guarantee" is a forward-looking commitment. Reading it as a
  present-tense inventory claim may be uncharitable. The site does say the guarantee has already been
  surpassed, and today the public roster is 291.

## A fair reading

There are reasonable interpretations under which Indy's numbers are defensible:

- A count published when it was accurate and not revised after departures is untidiness, not
  deception. Departures are frequently governed by contract timing that a resort partner — not Indy —
  controls, and may not be Indy's news to announce.
- "300 Resort Guarantee" may describe where the season lands, not where it stands today.
- Resorts come and go mid-negotiation, and a marketing page can't track that in real time.

What would settle it is simple: **a dated roster count on the Indy Pass site**, updated when resorts
join or leave. "291 resorts as of September 8" is a number nobody has to reverse-engineer, and it
costs nothing in appeal — a network that grew from 218 to 291 in under two years, and just added
Smugglers' Notch, doesn't need rounding up.

Until then, pass holders who want the current list can check
[Indy Explorer](https://indy-explorer.vercel.app), rebuilt from Indy's own public pages.

## Reproducing this

Every figure comes from dated snapshots of `data/resorts.csv` in the
[Indy Explorer repository](https://github.com/jonathanstelman/indy-explorer):

```bash
git log --format='%h %ad %s' --date=short -- data/resorts.csv   # list snapshots
git show <sha>:data/resorts.csv                                  # roster at that commit
```

Diff two snapshots on `(name, location_name)` — not on `name`, and not by row count. Two different
resorts named "Powder Ridge" (Middlefield, CT and Kimball, MN) are both on the pass today, and older
snapshots contain duplicate rows from the pipeline bug described above.

Corrections are welcome. If Indy publishes a count that differs from ours, we would rather understand
the discrepancy than assume our number is the right one.

---

## Appendix: the 23 departures since 2025-09-20

| Resort | Location |
|---|---|
| Ani Ski Resort | Akita, Tohoku, Japan |
| Blacktail Mountain Resort | Lakeside, MT, USA |
| Caberfae Peaks | Cadillac, MI, USA |
| Cape Smokey | Ingonish Beach, Nova Scotia, CA |
| Crystal Ridge | Franklin, WI, USA |
| Granite Peak | Wausau, WI, USA |
| Hickory Ski Center | Warrensburg, NY |
| Innsbruck Ski & City Network | Innsbruck, Austria |
| Kiroro Snow World | Otaru, Hokkaido, Japan |
| Kurohime Kogen | Nagano, Japan |
| LOGE Glacier | Essex, MT |
| Little Switzerland | Slinger, WI, USA |
| Lutsen Mountains | Lutsen, MN, USA |
| Madarao Ski Resort | Myoko Kogen, Nagano |
| Meadowlark Ski Resort | Ten Sleep, WY, USA |
| Methow Trails XC | Winthrop, WA, USA |
| Mission Ridge | Wenatchee, WA, USA |
| Mont Habitant | Saint-Sauveur, QC |
| Mount Washington Alpine Resort Nordic Centre at Raven Lodge | Mt. Washington, BC, Canada |
| Nordic Mountain | Wild Rose, WI, USA |
| Snowriver | Wakefield, MI, USA |
| Tangram Ski Circus | Shinano, Nagano, Japan |
| Valmorel Ski Resort | Les Avanchers-Valmorel, France |
