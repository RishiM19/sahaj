# The problem

PMJDY has crossed 530 million bank accounts. UPI clears 15 billion transactions a month. The access story — does a person have a bank account, can they move money digitally — is basically solved in India. But owning an account and being *served* by the financial system are two different things, and for a large slice of working India, only the first is true.

Four people, none of them an edge case:

- **Rajesh** drives for Swiggy in Mumbai. His income swings between ₹15,000 and ₹40,000 a month with no salary slip, so every financial product he meets assumes an income shape he doesn't have. In a lean week his only options are a 40%-interest loan app or a moneylender.
- **Priya** teaches in Thane. She has a stable salary and asked about a small SIP — she walked out with a ULIP instead. Not because she couldn't follow the difference, but because nobody framed the products against her actual money first.
- **Kisan** grows paddy on three acres in Karnataka. He knows the Kisan Credit Card exists. The form is in English and the nearest branch is 14km away, so every sowing season he's back with the same moneylender at 36%.
- **Divya** is a visually impaired writer in Pune. She can't independently use any mainstream finance app to file a disability tax claim, let alone manage her money day to day.

The common thread isn't a missing literacy course. It's that no system has ever modelled *who these people actually are* — how their income moves, how they behave under financial stress, exactly how predatory products are built to target them. Every existing financial tool waits to be asked the right question. The people who need help most are the least equipped to go and ask it.

## What SAHAJ does instead

SAHAJ sits as a proactive intelligence layer above the banking and payments rails that already exist. It doesn't wait for a question — it keeps a live model of each user's money situation and mental state (the **Behavioral Financial Twin**) and acts on it automatically, before a harmful decision is made. Same intelligence, four different interfaces, depending on what device and connection a person actually has:

1. **USSD `*99#` + SMS** — no internet, works on any GSM feature phone, ~90% of features.
2. **WhatsApp on 2G** — async queue and sync, ~98% of features.
3. **On-device (Android, intermittent 3G)** — voice-first, local inference, no server round-trip needed for reasoning.
4. **Full PWA on 4G** — everything, real-time.

See [`ARCHITECTURE.md`](ARCHITECTURE.md) for how that's actually built, and [`AGENTS.md`](AGENTS.md) for the ten specialists that do the reasoning.
