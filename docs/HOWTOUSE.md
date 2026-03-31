# How to Use Clint

## Core Commands

1. `clint init`
2. `clint config doctor`
3. `clint run --query "Dentists in California"`
4. `clint run --query "Dentists in California" --live`
5. `clint scrape --query "Hotels in London" --target 20`
6. `clint followup --days-since-last 3`
7. `clint export --table all`
8. `clint dashboard --host 127.0.0.1 --port 8000`

## Recommended Workflow

1. Configure with `clint init`.
2. Validate with `clint config doctor`.
3. Dry-run campaign first.
4. Launch live run after review.

## Safety Recommendation

For better deliverability and lower bot-detection risk:

- keep around 200 emails/day
- keep around 200 WhatsApp messages/day
