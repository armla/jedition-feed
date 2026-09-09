# JamesEdition Feed Operations Tracker

## Completed

- [x] Create an isolated public repository for the JamesEdition feed.
- [x] Generate and validate a 50-listing XML 3.9 feed with an exclusive-first allocation.
- [x] Restrict feed images to the first 12 `isonportalfeed` items ordered by `sortonportalfeed`.
- [x] Include all available primary and supplementary source video links.
- [x] Populate verified English descriptions and authoritative coordinates.
- [x] Add a safe-failure generator design that retains the last known-good feed.
- [x] Prepare a nightly workflow for 10:58 PM Costa Rica time (04:58 UTC).
- [x] Add ownership policy, pinned action revisions, and monthly GitHub Actions dependency review.
- [x] Apply main-branch protections: pull-request review, code-owner review, stale-review dismissal, linear history, no force pushes, no deletions, and conversation resolution.

## Operating Decisions Pending

- [x] Deploy the nightly GitHub Actions publisher to the dedicated `jamesedition-live` branch.
- [x] Confirm a complete production update and public crawler retrieval from the tokenized raw GitHub URL.
- [x] Implement idempotent first-publication activity delivery for **External Website - James Edition**.
- [ ] Confirm whether the four exclusive listings with a commercial source classification should be eligible for JamesEdition; they are excluded under the current conservative policy.
- [ ] Establish an approved coordinate precision policy for high-profile or owner-occupied residences.
- [ ] Add the dedicated `JAMESEDITION_PUBLISH_WEBHOOK_URL` secret and activate the JamesEdition Zapier-to-Salesforce mapping; this will backfill the current feed roster once.

## Maintenance

- [ ] Review the 50-listing selection, prices, availability, agent contact data, location precision, and media quality monthly.
- [ ] Review repository collaborators and GitHub Actions workflow changes quarterly.
- [ ] Rotate the random delivery URL and inform JamesEdition if the URL is disclosed or materially abused.
