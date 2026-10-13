# Resale pricing task

Business context: a repair-and-resell laptop flipper in Georgia (Tbilisi/Batumi) needs, for each listing, a realistic price he could resell the laptop for in Georgia once it is working, plus the official new price where it is still sold.

Input: `analysis/price_in_<N>.json`, a list of `{id, model, specs, condition, fault, price_gel}`.

Output: `analysis/price_out_<N>.json`, one object per input listing in the same order:

```json
{"id": "...", "resale": 750, "price_source": "used: mymarket.ge 3 listings 650-850 GEL (T480 i5 8GB 256GB); new: not sold (discontinued)"}
```

- `resale`: realistic used sale price in GEL in Georgia for this model + specs in good working condition (integer). null only if the model is so vague no estimate is possible (then say why in price_source).
- `price_source`: short text naming where the used price came from (e.g. "mymarket.ge used listings", "ss.ge", "eBay sold listings converted at 2.7 GEL/USD", "estimate from similar i5-8th gen 8GB laptops") AND the official new price in Georgia if found ("new: Zoommer 1,899 GEL" / "new: ee.ge 2,099 GEL" / "new: alta.ge ..."), or "new: not sold".
- Research method: group listings by model and research each model once. Use WebSearch / WebFetch for: Georgian used prices (mymarket.ge, ss.ge used notebook listings), Georgian new prices (zoommer.ge, ee.ge, alta.ge), and when the model is not sold in Georgia, international used prices (eBay sold, back market) converted at 2.7 GEL per USD and 3.1 per EUR, adjusted down ~10% for the Georgian market. For vague models ("Dell laptop i5 10th gen 8GB"), estimate from comparable-spec used laptops and say "estimate from comparable specs".
- Be realistic and conservative: what a private buyer in Georgia actually pays, not asking prices of shops with warranty.
- Write valid JSON (UTF-8) with the Write tool and validate with python3. Do not modify any other file. Work only inside /home/flash/Laptop Research; no files anywhere else, not even temporary ones.
- Do not call any `mcp__hearthbot__` tools. Never contact sellers or post anything anywhere; read-only web research.
