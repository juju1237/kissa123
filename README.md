# Tassutehtävät

Yhden sivun, riippuvuudeton Python-to-do-sovellus virtuaalikissalla.

## Käynnistys

Tarvitset Python 3.9:n tai uudemman. Käynnistä sovellus projektikansiosta:

```bash
python3 app.py
```

Avaa selaimessa [http://127.0.0.1:8000](http://127.0.0.1:8000). Tehtävät, palkinnot, lemmikin valinta ja kokemuspisteet tallennetaan paikallisesti `data/state.json`-tiedostoon.

## Ominaisuudet

- Valmiin tehtävän valitseminen tai oman tehtävän lisääminen.
- Ensimmäisellä käynnistyksellä valitaan lemmikiksi kissa, sitruuna tai käpy ja annetaan sille nimi.
- Viisi vaikeustasoa: super helppo (1–5 min), eezy (10 min), keskivaikea (30 min), vaikea (1 tunti) ja Kill (yli 2 tuntia).
- Tehtävän valmistumisesta saa tasoon perustuvia puupalikoita, kangasta, kalaa ja rahaa.
- Tehtävä poistuu listalta valmistuessaan. Lemmikin taso kasvaa kokemuspisteillä; seuraava taso vaatii 100 pistettä.
- Tehtävän voi jakaa 2–10 osaan kirjoittamalla osat omille riveilleen. Jokaisesta osasta saa 5 XP:tä, kalaa ja rahaa; kaikkien osien jälkeen saa vaikeustason mukaisen kokonaisbonuksen.
- Päivän yllätystehtävä arvotaan kerran päivässä valmiista tehtävistä. Sen voi lisätä tehtävälistalle kerran päivässä, ja valmistumisesta saa kaksinkertaiset XP- ja resurssipalkinnot.
- Tehtävän ja jokaisen osatehtävän valmistumisesta saa lisäksi yhden satunnaisen resurssin yllätyspaketista. Paketin avaamisen jälkeen ikkuna sulkeutuu häivytyksellä noin kolmen sekunnin kuluttua.
- Inventaarion kala- ja rahakuvakkeet sekä yllätyspaketin kuvat ladataan `pictures/`-kansiosta.
- Sivun alareunan "Aloita alusta" -painike pyytää vahvistuksen ja nollaa tehtävät, palkinnot, kokemuspisteet sekä lemmikin valinnan.
