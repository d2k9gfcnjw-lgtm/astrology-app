# Golden test charts

Claude tests every calculation against these. Copy values from astro.com
(Extended Chart Selection, then the chart data table).

Add one file per chart, e.g. `natal_01.yaml`:

```yaml
name: My natal chart
datetime_local: 1990-05-01 14:23
timezone: America/New_York
utc_offset_used: -04:00
lat: 40.7128
lon: -74.0060
house_system: placidus
zodiac: tropical
planets:      # longitude as sign degree minute, e.g. "11 Tau 04"
  sun: ""
  moon: ""
  # ... all ten
cusps:        # houses 1 to 12
  1: ""
  # ...
```

Needed before Phase 1:

- [ ] Your own natal chart
- [ ] One born before 1970
- [ ] One Southern Hemisphere birth
- [ ] One above 55 degrees latitude
- [ ] One born near a daylight saving change

Needed before Phase 6: three of your past solar returns, one relocated.
