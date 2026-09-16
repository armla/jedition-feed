# JamesEdition Media Quality Assessment

**Assessment date:** 2026-09-16
**Scope:** The current 50-record ELITE feed and 100-record standard portal feed.
**Purpose:** Document the verified image-resolution remediation and virtual-tour compatibility decision.

## Executive conclusion

The feed had been delivering Propertybase/S3 **display renditions**, primarily `1277 × 640` pixels. This was an avoidable quality constraint: the same stable S3 paths expose the corresponding canonical original objects when the rendition segment is removed. The generator now emits those canonical original-object URLs, preserving the listing's source order and the identical underlying image while avoiding the reduced display rendition.

The audit verified that **all 1,707 original-object URLs were reachable**. JamesEdition recommends at least **1024 × 641** pixels and permits higher dimensions up to 20 MB per image. The revised feed therefore materially improves the delivered assets without creating a new image-hosting dependency.

A YouTube vertical clip is **not a valid `media/virtual_tour_link`**. JamesEdition permits virtual-tour links only from approved immersive-tour providers. The source data currently contains no approved-provider tour URL, so the generator deliberately emits no invalid virtual-tour field. It is now ready to emit a compliant link automatically when a supported provider URL is added to the source tour field.

## Verified image results

| Measure | Former feed delivery | Revised feed behavior |
| --- | --- | --- |
| Exact URLs evaluated | 1,707 | 1,707 canonical original-object URLs |
| Reachable images | 1,707 | 1,707 (0 failed) |
| Predominant display rendition | `1277 × 640` (1,567 images) | Original object dimensions preserved |
| `1277 × 640` display renditions | 1,567 | 0 |
| Original images with a long edge under 1,000 px | Not measured | 11 (3 ELITE; 8 portal) |
| Portrait originals narrower than the 1,024 px **landscape** recommendation | Not applicable | 42 |

> JamesEdition's 1024 × 641 guidance is explicitly for **horizontal** imagery. Accordingly, the 42 portrait images narrower than 1,024 px are not all genuinely low-resolution; only **11 original assets** have both a sub-1,000 px long edge and fewer pixels than the 1024 × 641 landscape benchmark. The feed retains otherwise valid originals so that an individual lower-resolution asset does not reduce a listing below the two-image publication minimum. The durable remedy is a higher-resolution replacement in the source CMS.

## Source-image remediation queue

The table identifies listings with at least one portrait original narrower than the 1,024 px horizontal recommendation. It is a source-CMS improvement queue, not a reason to block the feed. The most material files are the **11 assets with a long edge below 1,000 px**, concentrated in `LXGR14344`, `LXER14267`, `LXHR12134`, and `LXSR13825`.

| Feed | MLS reference | Images below recommendation | Original dimensions requiring review |
| --- | --- | ---: | --- |
| ELITE | `LXER10658` | 1 | 939 × 1406 |
| ELITE | `LXER11026` | 1 | 737 × 1106 |
| ELITE | `LXER11158` | 1 | 964 × 1444 |
| ELITE | `LXER12675` | 2 | 964 × 1444 |
| ELITE | `LXGR14010` | 2 | 772 × 1158, 772 × 1540 |
| ELITE | `LXGR14344` | 3 | 515 × 772 |
| ELITE | `LXPR13368` | 1 | 772 × 1158 |
| ELITE | `LXSR13699` | 1 | 772 × 1158 |
| PORTAL | `LXCR10808` | 2 | 964 × 1444 |
| PORTAL | `LXCR11151` | 1 | 964 × 1445 |
| PORTAL | `LXCR13384` | 1 | 964 × 1445 |
| PORTAL | `LXER10326` | 1 | 994 × 1536 |
| PORTAL | `LXER12034` | 2 | 964 × 1444, 965 × 1445 |
| PORTAL | `LXER12828` | 2 | 964 × 1444 |
| PORTAL | `LXER13140` | 1 | 772 × 1158 |
| PORTAL | `LXER13451` | 1 | 772 × 1158 |
| PORTAL | `LXER13478` | 1 | 772 × 1158 |
| PORTAL | `LXER14267` | 2 | 515 × 772 |
| PORTAL | `LXHR11130` | 3 | 964 × 1444 |
| PORTAL | `LXHR12134` | 5 | 482 × 722, 483 × 723, 483 × 724, 484 × 726, 486 × 728 |
| PORTAL | `LXHR12407` | 1 | 964 × 1444 |
| PORTAL | `LXHR12491` | 1 | 965 × 1444 |
| PORTAL | `LXHR12513` | 3 | 964 × 1444, 964 × 1445 |
| PORTAL | `LXHR12778` | 1 | 964 × 1444 |
| PORTAL | `LXHR14162` | 1 | 772 × 1540 |
| PORTAL | `LXSR13825` | 1 | 514 × 772 |

## Video and virtual-tour compatibility

| Source field | Available records in inventory | Meaning in JamesEdition feed |
| --- | ---: | --- |
| `property.virtual_tour_video_url` | 297 | Primary horizontal YouTube walkthrough when populated; emitted as the one supported video. |
| `listing.live_tour_url` | 70 | Secondary horizontal YouTube walkthrough; used only if the primary value is absent. |
| `listing.vertical_video_1` | 48 | Valid only as a fallback `media/video/video_url`, never as a virtual-tour link. |
| `listing.vertical_video_2` | 11 | Lower-priority fallback video only. |
| Approved immersive-tour provider URL | 0 | Required before `media/virtual_tour_link` can be emitted. |

JamesEdition permits exactly **one** `media/video/video_url` per listing and supports YouTube, Vimeo, and Brightcove as video providers. Its `media/virtual_tour_link` must instead use a public share URL from an approved provider such as Matterport, My360, YouriGuide, Realistico, Nodalview, CloudPano, Kuula, Giraffe360, Floorfy, or the other documented providers. The generator enforces these separate rules.

## Operating standard

1. Keep image ordering in the source `sortonportalfeed` field; the feed continues to publish the first 12 eligible images only.
2. Upload and retain original, watermark-free images in the source CMS. The feed now resolves the canonical original S3 object rather than an application display rendition.
3. Replace the 11 materially low-resolution source assets first, then review the remaining portrait images in the table during normal media maintenance. Prioritize ELITE listings and any image used in the first three feed positions.
4. When a Matterport or another approved immersive-tour provider is available, store its public share URL in the source tour field. Do not use YouTube links in that field.
5. Do not rely on feed-side image upscaling. It would fabricate pixels, not recover the photographer's source quality.

## Evidence and references

JamesEdition's current [Getting Started documentation](https://docs.jamesedition.com/docs/) requires stable image URLs, permits JPEG/PNG/WEBP files up to 20 MB, and documents the supported video and virtual-tour providers. Its [listing performance guidance](https://help.jamesedition.com/en/how-can-i-increase-the-performance-of-my-listings) recommends horizontal imagery of at least 1024 × 641 pixels and encourages higher resolution where the file-size limit permits.
