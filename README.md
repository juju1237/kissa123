# Tassutehtävät

Yhden sivun, riippuvuudeton Python-to-do-sovellus virtuaalikissalla.

## Käynnistys

Tarvitset Python 3.9:n tai uudemman. Käynnistä sovellus projektikansiosta:

```bash
python3 app.py
```

Avaa selaimessa [http://127.0.0.1:8000](http://127.0.0.1:8000). Tehtävät, palkinnot ja kissan kokemuspisteet tallennetaan paikallisesti `data/state.json`-tiedostoon.

## Ominaisuudet

- Valmiin tehtävän valitseminen tai oman tehtävän lisääminen.
- Viisi vaikeustasoa: super helppo (1–5 min), helppo (10 min), keskivaikea (30 min), vaikea (1 tunti) ja Kill (yli 2 tuntia).
- Tehtävän valmistumisesta saa tasoon perustuvia puupalikoita, kangasta, kuivaruokaa ja kolikoita.
- Tehtävä poistuu listalta valmistuessaan. Muru-kissan taso kasvaa kokemuspisteillä; seuraava taso vaatii 100 pistettä.
