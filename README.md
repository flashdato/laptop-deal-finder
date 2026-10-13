# Laptop Deal Finder

My research into flipping used and damaged laptops in Georgia: listings scanned from Facebook Marketplace, mymarket.ge, unlim.ge, minda.city and ss.ge, each with a fault estimate, repair cost, the most worth paying and a flip score. My own ratings, statuses and notes are included, and the **My reviews** filter shows the laptops I reviewed or bought.

**Website:** https://flashdato.github.io/laptop-deal-finder/ (a read-only copy; anything you change stays in your browser)

Seller names and phone numbers are left out. Each listing links to the original post.

## Run it on your PC

```
cd deal-finder && ./start.sh
```

It opens http://localhost:8770, reads every CSV in `deal-finder/` plus `laptop-listings.csv`, drops duplicate listings, and saves ratings to `ratings.csv` and statuses and notes to `meta.json`.

The `scanners/` and `facebook-scan/` folders hold the scripts that collected the listings.
