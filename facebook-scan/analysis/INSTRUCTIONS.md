# Listing analysis task

You read Facebook Marketplace laptop listings from Georgia (text in Georgian, Russian or English) and extract structured data for a laptop repair-and-resell business. The buyer is an electrical engineer who buys cheap or damaged laptops, repairs them and resells.

Input: `analysis/in_<N>.json`, a list of `{id, title, card_price, location, page_text}`. `page_text` is the full listing page text (title, price, "Listed X ago in ...", Details like Condition / Brand / Product line, then the seller's description).

Output: write `analysis/out_<N>.json` (same N), a JSON list with one object per input listing, in the same order:

```json
{
  "id": "...",
  "category": "sale | parts | buyer | skip",
  "model": "Brand + exact model, e.g. 'Lenovo ThinkPad T480' or 'HP Pavilion 15-eh1xxx'. Empty if truly unknown.",
  "specs": "CPU, RAM, storage, GPU, screen; compact, e.g. 'i5-8350U, 8GB RAM, 256GB SSD, Intel UHD 620, 14\" FHD touch'. Only what the listing states or the exact model implies with certainty.",
  "condition": "short English: e.g. 'Used - good', 'Used - fair, scratches', 'Like new', 'Not working'",
  "fault": "short English list of stated faults, joined by '; ' (e.g. 'cracked screen; weak battery; no charger'). Empty if none stated.",
  "price_gel": 450,
  "summary_ka": "One short Georgian sentence (max ~20 words) summarising model, key specs, condition/fault and price."
}
```

Rules:
- category: `sale` = a laptop offered for sale (working or with minor issues). `parts` = sold for parts / "იშლება" / "ნაწილებად" / dead / not turning on / motherboard or liquid damage. `buyer` = the poster wants to BUY laptops (ჩაბარება, ვყიდულობ, შევიძენ, куплю, скупка, "we buy"). `skip` = not a laptop at all (tablet, phone, monitor, desktop PC, accessory, RAM, screen panel only, service ad, a batch/shop of many laptops with no single price).
- price_gel: number in GEL. Convert `$` at 2.7 and `€` at 3.1. If the price is a placeholder (1, 11, 111, 1111, 0, "Free" when clearly not free) or "by agreement"/"შეთანხმებით"/"договорная", use null. If the description states a different real price than the card, use the description's.
- Never invent specs. If the title says "i5 10th gen" write "i5 10th gen", not a specific SKU, unless the exact model fixes it.
- Phone numbers: Facebook hides them as "[hidden information]"; ignore.
- Keep it fast: no web searches needed. Just read and extract.
- Write valid JSON (UTF-8). Do not modify any other file. Work only inside /home/flash/Laptop Research; put no files anywhere else, not even temporary ones.
- Do not call any `mcp__hearthbot__` tools.
