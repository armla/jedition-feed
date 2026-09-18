# JamesEdition Floors (`Stories__c`) Field Mapping

**Status:** Generator mapping deployed; source API exposure pending.

## Finding

Neither live JamesEdition feed currently contains a `<floors>` element. The element is correctly supported by the JamesEdition 3.9 single-office specification and means the **total number of storeys in the property**, not the floor on which an apartment or condominium unit sits.

The source field is available in Propertybase/Salesforce as:

| Source object | Salesforce API name | Data type | JamesEdition XML element |
| --- | --- | --- | --- |
| Property | `Stories__c` | `Number(2, 0)` | `<floors>` |

The public endpoint used by both the JamesEdition and Encuentra24 feeds—`https://api.lxcostarica.com/api/v1/listings`—does **not** currently serialize `Stories__c`. This was verified in the bulk inventory response and in the listing-detail response. The branded property page likewise does not expose a structured stories value. Therefore, no automated feed can publish a reliable floor count until the property API includes it.

## Implemented feed-side behavior

The JamesEdition generator is prepared to consume these fields in order:

1. `property.Stories__c`
2. `property.stories`
3. `property.floors`
4. `listing.Stories__c`
5. `listing.stories`
6. `listing.floors`

It emits `<floors>` only where the value is a positive integer between **1 and 99**. Fractional, zero, negative, empty, and implausible values are safely omitted. This avoids presenting a unit-floor number or corrupt source value as a building-storey count.

## Required source API change

Expose the Salesforce field in the public listing serializer. Either of the following JSON shapes is accepted by the feed generator:

```json
{
  "Stories__c": 2
}
```

or, preferably as a normalized public API contract:

```json
{
  "stories": 2
}
```

The value may be present at the property level (preferred) or the nested listing level. After the endpoint returns the field, the next scheduled feed refresh will automatically add `<floors>2</floors>` for each eligible listing with a populated value. No JamesEdition URL, credential, workflow, or further manual data entry is required.

## Verification protocol

1. Update a controlled, published property such as `LXER10658` with `Stories__c = 2` in Salesforce/Propertybase.
2. Confirm the public detail response includes the field, for example `https://api.lxcostarica.com/api/v1/listings/<listing-id-or-permalink>`.
3. Run the relevant JamesEdition GitHub workflow in manual refresh mode with activity delivery set to **off**.
4. Confirm the generated XML includes `<floors>2</floors>` under the matching `<advert reference="LXER10658">`.
5. Leave the nightly schedule unchanged; subsequent source changes will flow through automatically.

## Reference

JamesEdition lists `floors` as an optional integer field in its current [Real Estate — Single Office specification](https://docs.jamesedition.com/docs/real-estate/single-office): “Total floors in the property (how many storeys the building has) — not the floor the unit is on.”
