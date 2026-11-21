# alota jo -sovellus

Yhden sivun, riippuvuudeton Python-to-do-sovellus pisteiden keräyksellä.
Projektin tarkoitus on harjoitella vibe koodausta agentin avulla.
## 1. Käynnistys Linuxissa
Tarvitset:
- Linux terminaalin
- Gitin
- Python 3:n tai uudemman



### 2. Kloonaa sovellus

Suorita komennot kansiossa, johon haluat ladata projektin:

```bash
git clone git@github.com:juju1237/kissa123.git
cd kissa123
```

### 3. Käynnistä sovellus

```bash
python3 app.py
```

Jätä terminaali käyntiin ja avaa selaimessa [http://127.0.0.1:8000](http://127.0.0.1:8000). Pysäytä sovellus painamalla terminaalissa `Ctrl+C`. Tehtävät, palkinnot, lemmikin valinta ja kokemuspisteet tallennetaan paikallisesti `data/state.json`-tiedostoon.

## Ominaisuudet

- Valmiin tehtävän valitseminen tai oman tehtävän lisääminen.
- Ensimmäisellä käynnistyksellä valitaan lemmikiksi kissa, sitruuna tai käpy ja annetaan sille nimi.
- Viisi vaikeustasoa: super helppo (1–5 min), eezy (10 min), keskivaikea (30 min), vaikea (1 tunti) ja Kill (yli 2 tuntia).
- Tehtävän valmistumisesta saa tasoon perustuvia puupalikoita, kangasta, kalaa ja rahaa.
- Tehtävä poistuu listalta valmistuessaan. Lemmikin taso kasvaa kokemuspisteillä; seuraava taso vaatii 100 pistettä.
- Tehtävän voi jakaa 2–10 osaan kirjoittamalla osat omille riveilleen. Jokaisesta osasta saa 5 XP:tä, kalaa ja rahaa; kaikkien osien jälkeen saa vaikeustason mukaisen kokonaisbonuksen.
- Viikkotavoitteena on tehdä vähintään 15 tehtävää. Jaettu tehtävä lasketaan yhdeksi vasta kaikkien osien valmistuttua; viikko vaihtuu ilman katkenneesta putkesta rankaisemista.
- Päivän yllätystehtävä arvotaan kerran päivässä valmiista tehtävistä. Sen voi lisätä tehtävälistalle kerran päivässä, ja valmistumisesta saa kaksinkertaiset XP- ja resurssipalkinnot.
- Tehtävän ja jokaisen osatehtävän valmistumisesta saa lisäksi yhden satunnaisen resurssin yllätyspaketista. Paketin avaamisen jälkeen ikkuna sulkeutuu häivytyksellä noin kolmen sekunnin kuluttua.
- Inventaarion kala- ja rahakuvakkeet sekä yllätyspaketin kuvat ladataan `pictures/`-kansiosta.
- Sivun alareunan "Aloita alusta" -painike pyytää vahvistuksen ja nollaa tehtävät, palkinnot, kokemuspisteet sekä lemmikin valinnan.
