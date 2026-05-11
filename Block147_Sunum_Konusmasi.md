# Block 147 — 10 Dakikalık Sunum (TR) · Slayt Planı + AI Promptları

> **HUMS — Pervititch 1923 Block 147 · LOD3 BIM**
> Süre hedefi **~10 dk** (≈ 130 wpm) · Canlı viewer **https://hums.ilkeryoru.com**
> Hazırlık tarihi: 2026-05-12

Her slayt 4 katman içerir:
- **Görsel** → ekranda gösterilecek görsel + tek satırlık yerleşim
- **Slayt üzerindeki metin** → ekrana yazılacak kısa, başlık+madde
- **Konuşma metni** → o slayt için konuşulacak söz (notlar kısmı)
- **AI prompt** → Gamma / Beautiful.ai / Canva Magic gibi araca verilebilecek tek satırlık üretim promptu
- **Gerekli dosya / veri** → görseli oluşturmak için repodaki yol veya hesaplanmış değer

Tüm fotoğraf / veri yolları repo köküne göredir.

---

## Slayt 1 — Açılış · QR & live viewer (0:00 – 0:45 · ~45 sn)

**Görsel:** ekranın sağ yarısında büyük QR kod (hedef = `https://hums.ilkeryoru.com`), sol yarıda `block147.glb` ekran görüntüsü; alt orta: **hums.ilkeryoru.com**.

**Slayt üzerindeki metin:**
> # HUMS — Pervititch 1923 · Block 147
> ## Kağıttan dijital şehre, bir blok
> **hums.ilkeryoru.com**  ·  *QR'ı şimdi okutun — modeli kendi telefonunuzda döndürün*

**Konuşma metni:**
> Merhaba. Şu an gösterdiğim QR kodu telefonunuzla okutun: doğrudan **hums.ilkeryoru.com** açılacak, Kadıköy'de 1923'te yaşamış küçük bir kentsel adanın LOD3 düzeyinde 3 boyutlu modelini kendi telefonunuzdan döndürebilirsiniz. Sunum boyunca açık tutun — anlattıklarımı orada görürsünüz. Bugün size bir **kâğıt haritayı dijital bir BIM'e** dönüştürmenin hikâyesini, sonra da haritanın içindeki **iki binayı** — biri bir kilise, biri bir fırın — anlatacağım. Hikâyenin geri kalanı kendi kendini anlatıyor.

**AI prompt:**
> *"Title slide of a heritage informatics talk titled 'HUMS — Pervititch 1923 · Block 147'. Left half: a 3D BIM screenshot of a small Istanbul city block with a domed Greek Orthodox church and a corner bakery (warm sepia palette). Right half: a large clean QR code with the URL **hums.ilkeryoru.com** under it. Subtitle: 'Kağıttan dijital şehre, bir blok.' Minimal, museum-poster aesthetic, paper-cream + ink-black + terracotta accents."*

**Gerekli dosya / veri:**
- QR kod: `hums.ilkeryoru.com` (https://www.qrserver.com gibi araçla üret)
- Görsel: `output/buildings/W-34-36-FIRIN/` veya `output/gltf/` altından bir render — yoksa viewer ekran görüntüsü

---

## Slayt 2 — Pervititch haritaları (0:45 – 2:00 · ~75 sn)

**Görsel:** sol = `data/raw/raster/500_1938_APLPEKADI08.tif`'in geniş plan ekran görüntüsü (1938 Kadıköy 1:500 plaka 08); sağ = `map.png` (sadece Pafta 147). Aralarında ok.

**Slayt üzerindeki metin:**
> # Pervititch Haritaları
> - Jacques Pervititch · 1922-1945
> - **Yangın sigortası** için: malzeme, kat, tonoz, açıklık
> - İstanbul'un Cumhuriyet öncesi/erken Cumhuriyet **en ayrıntılı kayıtlı görüntüsü**
> - Bizim kaynağımız: **1938 · Kadıköy 1:500 · Plaka 08**  (SALT Araştırma)

**Konuşma metni:**
> Jacques Pervititch Hırvat asıllı bir sigorta haritacısıydı. 1920'lerden 1940'lara kadar İstanbul'un yangın sigortası için **mahalle mahalle, blok blok, bina bina** çıkardığı haritalar, bugün Osmanlı sonrası — Cumhuriyetin ilk on yıllarındaki — Istanbul'un en ayrıntılı kayıtlı görüntüsü. Pervititch sadece çatı izlerini değil; **duvar malzemesini** — taş, tuğla, ahşap — **kat sayısını**, **tonoz türünü** — Voûte Française, Voûte Turque — **dükkân girişlerini**, hatta bahçelerdeki ağaçları çiziyor. Yangın haritası olduğu için ihtiyacı vardı. Üzerinde çalıştığımız tabaka SALT Araştırma'nın dijitalleştirdiği **1938 tarihli Kadıköy 1:500 ölçekli plaka 08**. Buradan Pafta 147'ye odaklandık.

**AI prompt:**
> *"Slide titled 'Pervititch Haritaları'. Left: a wide screenshot of a 1938 Pervititch fire-insurance plate (sepia tones, colored parcels, dense annotations). Right: a zoomed-in single block from that same plate with a domed church and yellow/pink parcels. Arrow between them. Four bullets in Turkish: '1922-1945 · Pervititch'; 'Yangın sigortası: malzeme, kat, tonoz, açıklık'; 'En ayrıntılı kayıtlı İstanbul'; '1938 Kadıköy 1:500 Plaka 08'. Sepia + cream palette."*

**Gerekli dosya / veri:**
- `data/raw/raster/500_1938_APLPEKADI08.tif`  (36 MB — sunum için PNG'e indirgenebilir)
- `map.png`  (Pafta 147 kırpık)

---

## Slayt 3 — Pafta 147 nerede (2:00 – 3:30 · ~90 sn)

**Görsel:** sol = `map.png` (Pafta 147), üzerinde sokak ve mahalle etiketleri vurgulu; sağ = aynı koordinatın modern uydu/harita görüntüsü (Google/OSM, Osmanağa Mh.); ortada büyük "**147**" rozetı.

**Slayt üzerindeki metin:**
> # Pafta 147 — Kadıköy Çarşı'sının göbeği
> - **Mahalle:** Osmanağa
> - **Bugün:** Yasa Cd. × Mühürdar Cd. köşesi
> - **Pervititch sokakları:** Söğütlü Çeşme Cad. (B), İsmail Sok. (D)
> - **Boyut:** ≈ 46 × 52 m · **1 372 m²**
> - **Merkez:** 40.9907° K, 29.0251° D
> - **Hikâye:** 1855 yangınından sonra Osmanlı şehirciliğinin **ilk modern ızgara planı** burada uygulandı

**Konuşma metni:**
> Pafta 147, bugünkü Kadıköy Çarşı'sının tam göbeğinde: Osmanağa Mahallesi, Yasa Caddesi ile Mühürdar Caddesi'nin köşesinde, yaklaşık 40.99 K, 29.02 D. Pervititch'in dilinde — Söğütlü Çeşme Cad. batıda, İsmail Sok. doğuda. Yaklaşık 46 × 52 metre, 1372 m². Burayı sıradan kılan ne? Sıradan değil. Bu blok bir bütün olarak **1855 Kadıköy yangınından sonra yeniden örülmüş** bir dokunun parçası: 14 Ağustos 1855'te Caferağa'da çıkan yangın 400 civarında binayı yok etti, sonra mühendis **Hasan Tahsin Efendi**'nin çizdiği — Osmanlı şehirciliğinin **ilk modern ızgara planı** — uygulandı: 6 ve 4.5 metrelik iki tip sokak, çıkmaz yok, kavşaklarda küçük meydanlar, ana aks olarak Mühürdar Caddesi. Pafta 147'nin grid'i tam o plan. Bir başka katman: bu blok bugün **Kentsel Sit Alanı ve 3. Derece Arkeolojik Sit** kapsamında — 28 Eylül 2022'de Koruma Kurulu kararıyla 87 hektarlık Kadıköy Çarşı koruma alanı genişletildi, biz onun içindeyiz.

**AI prompt:**
> *"Slide 'Pafta 147 — Kadıköy Çarşı'sının göbeği'. Side-by-side: left a 1923 Pervititch insurance-map block (yellow/pink parcels, Greek Orthodox church with dome in the middle, labeled streets); right a modern satellite/OSM view of the same Kadıköy block with the church still visible. A bold red oval badge with '147' in the center. Six concise Turkish bullets listing district (Osmanağa), today's streets (Yasa × Mühürdar), Pervititch street names, dimensions (46×52 m, 1372 m²), coordinates, and the 1855 fire / grid-plan hook."*

**Gerekli dosya / veri:**
- `map.png`
- Modern uydu görüntüsü — Google Maps screenshot of `40.9907,29.0251`
- Sayılar: 46 × 52 m, 1372 m² (Pervititch block boundary KML)
- 1855 yangını → 400 bina · Hasan Tahsin Efendi · 1856 plan
- Sit kararı: 28.09.2022 · No. 9900 · Kentsel Sit + 3. Derece Arkeolojik Sit · 87 ha

---

## Slayt 4 — Veri hattı (3:30 – 4:30 · ~60 sn)

**Görsel:** üstte küçük bir akış diyagramı: **Pervititch raster → KML footprint → buildings.json (LOD3) → block147.glb (model-viewer) → IFC**; altta `output/viewer.html`'in canlı ekran görüntüsü.

**Slayt üzerindeki metin:**
> # Kağıttan LOD3 BIM'e
> Pervititch raster  →  **20+ KML footprint** (gerçek izdüşüm)
>                   →  `buildings.json` · 34 parsel
>                   →  **block147.glb**  (model-viewer)
>                   →  IFC export
> *Her cephe, açıklık, tonoz, çatı eğimi ayrı bir mesh elemanı.*

**Konuşma metni:**
> Pipeline kısaca şöyle: 20'den fazla KML poligonu ile binaların gerçek izdüşümlerini yer çizgisine sabitledik — kilise 320 m², kubbe, çeşme 7.6 m², kuzeydoğu sırası, batı fırın kompleksi 56 m², ahşap iç yapı, üç küçük magazin. Üzerine Pervititch'in malzeme ve kat kodlarını ekledik — sonuç **34 parselli, LOD3 düzeyinde bir BIM**: her cephe, her açıklık, her tonoz, her çatı eğimi ayrı bir mesh elemanı. Çıktı **glTF (block147.glb) + IFC**. Telefondaki o döndürdüğünüz model, doğrudan bu pipeline'ın ürünü. Pervititch'in kendi etiketlerinin %95'i anonim — sadece "Mg.", magasin, dükkân yazıyor. Ama bu blokta birkaç bina adı sanıyla çiziliyor. Şimdi onlardan ikisini anlatacağım.

**AI prompt:**
> *"Slide 'Kağıttan LOD3 BIM'e'. A clean horizontal arrow-flow diagram with 5 nodes: 'Pervititch raster' → '20+ KML footprint' → 'buildings.json (LOD3)' → 'block147.glb' → 'IFC export'. Below the flow, a screenshot of a web model-viewer showing a 3D city block. Small caption: 'Her cephe, açıklık, tonoz, çatı eğimi ayrı bir mesh elemanı.' Minimal sepia + ink palette."*

**Gerekli dosya / veri:**
- Akış diyagramı (Mermaid veya elle çizilir)
- `output/viewer.html` ekran görüntüsü
- Sayılar: 21 KML, 34 parsel (`data/parsed/kml_metrics.json`, `data/parsed/buildings.json`)

---

## Slayt 5 — Birinci kahraman: Ayia Efimia Kilisesi (4:30 – 6:30 · ~120 sn)

**Görsel:** sol = `map.png`'in kilise alanı yakın plan (kubbe sembolü, "Rum-Ortodoks Kilises Ayia-Eftimia", testere kenarlı "Enclos"); sağ = `output/gltf/CHURCH.glb`'nin viewer render'ı; alta üç madde fotoğraf — Pervititch çizimi · 3D model · bugünkü kilise.

**Slayt üzerindeki metin:**
> # Kahraman #1 — Ayia Efimia Rum Ortodoks Kilisesi
> *Adı = Kalkedon (Khalkedon) şehidi · 451 Konsili'nin azizi*
> - **1694**  Met. Gabriel — yeniden inşa
> - **1830**  Met. II. Zaharias — Rus bağışlarıyla büyütme
> - **1993**  Met. III. Iokeim — restorasyon
> - Tuğla beden · kiremit çatı · **4 fil ayağı pilastr** üzerinde yüksek tamburlu **merkezi kubbe** · üç camlı tambur açıklığı
> - Pervititch kodları doğruluyor: `Tt.` · `1=2` · `2p` · `1er V.T.` · "Enclos" testere kenarı

**Konuşma metni:**
> Adanın göbeğinde Ayia Efimia — Hagia Euphemia — Rum Ortodoks Kilisesi. İsim önemli: **Eufemia, Kadıköy'ün — Khalkedon'un — kendi şehidi**. **451'de bu şehirde toplanan Kalkedon Konsili**'nin ev sahibi azize. Yani kilise sadece bir cemaat yapısı değil, şehrin antik çağdan beri taşıdığı en büyük teolojik anının sembolik mührü. Yapı hikâyesi: Bizans döneminde aynı yerde "Ayia Basis" adıyla bir manastır vardı, sonra Ayia Euphemia Metropolitlik Manastırı oldu, harap düştü. **1694'te Kadıköy Metropoliti Gabriel**'in aldığı izinle yeniden inşa edildi. **1830'da Metropolit II. Zaharias** Rusya'dan topladığı bağışla kiliseyi büyüttü; bugün görülen biçim — tuğla beden, kiremit çatı, **dört "fil ayağı" pilastrın taşıdığı, yüksek tamburlu merkezi kubbe** — o aşamadan kalma. Pervititch'in plan üstüne yazdığı kodlar bunu birebir doğruluyor: `Tt.` kiremit çatı, `1=2` yüksek nef konvansiyonu, `2p` iki kısmi kat, `1er V.T.` birinci kat Türk tonozu, ortada kubbe sembolü, çevresinde testere kenarlı "Enclos" — avlu duvarı. Modelde bu blokun komşusu da var: (39/1) **"Camlı (Vitre)"** — kilisenin camekanlı batı narteksi, batı kapısının üzerinde — Pervititch onu mavi diyagonal taramayla ayırıyor, "cam yapı" sembolü. Yanındaki tek katlı çıkıntı **"Clocher"** — çan kulesi. (39/2)'de ise **"Çeşme"** — bütün caddeye adını veren söğüt gölgeli çeşme. Kilise 20. yüzyıl boyunca harap düştü, **1 Nisan 1993'te Metropolit III. Iokeim'in çalışmalarıyla restore edilip yeniden ibadete açıldı** — bugün de Kadıköy Çarşısı'nın orta noktasındaki küçük meydanın üzerinde, ayakta. Modelde dikkat ederseniz **kubbe tamburunun çevresinde üç küçük kemerli camlı açıklık** koyduk — haritada üç işaret var, bu sayıyı sadakatle korudum. Yüksek bir fener inşa etmedim; Pervititch çizmiyor, biz de eklemedik.

**AI prompt:**
> *"Slide 'Kahraman #1 — Ayia Efimia Rum Ortodoks Kilisesi'. Three vertical image panels: (1) a close-up of the 1923 Pervititch sheet showing the church footprint with the central dome symbol and the sawtoothed 'Enclos' wall; (2) a 3D model render of a small brick Greek Orthodox basilica with a high-drum dome and three small arched glazed windows on the drum; (3) a present-day photo of Aya Efimia church in Kadıköy. Five short Turkish bullets on the right covering: 1694 Met. Gabriel, 1830 Met. Zaharias II + Russian donations, 1993 Met. Iokeim restoration, brick walls + tiled roof + central high-drum dome on four pier pilasters with three glazed openings, and Pervititch code corroboration."*

**Gerekli dosya / veri:**
- `map.png` kilise yakın planı  (kırpılmış, hi-res)
- `output/gltf/CHURCH.glb`  (veya viewer'dan kilise render'ı)
- Bugünkü kilise fotoğrafı — örnek kaynaklar: Tarihi İstanbul, İstanbul Ansiklopedisi (atıf!)
- Tarihler: 1694 / 1830 / 1 Nisan 1993
- Sayılar: kilise footprint = **320.6 m²**, bbox **22 × 24 m** (`data/parsed/kml_metrics.json`)

---

## Slayt 6 — İkinci kahraman: NW köşesi · üç tarihi marka tek bir köşede (6:30 – 8:15 · ~105 sn)

**Görsel:** sol = `map.png`'in NW köşesi yakın planı (`FİRİN V.F. +MB 2½` + batı cephesindeki `Fırın TR.4 +3` + batı duvarındaki 3 küçük magazin); sağda üç dikey panel — **Beyaz Fırın** (1920) · **Akveren Makarna** (1925) · **Mehmet Efendi şubesi** (parent 1871); orta başlık: **"BİR KÖŞE · ÜÇ MARKA · 100+ YIL"**.

**Slayt üzerindeki metin:**
> # Kahraman #2 — NW köşesi · üç tarihi marka tek bir köşede
> *Pervititch'in tek bir `FİRİN` etiketi → bugün üç ayrı kurumsal kimlik*
>
> | Yıl | Marka | Pervititch karşılığı | Bugünkü adres |
> |---|---|---|---|
> | **1920** | **Beyaz Fırın** (Stoyanof ailesi, Bulgar Ortodoks, 5. nesil) | batı duvarındaki 3 küçük magazinden en güneyde ve en büyük olanı (≈ 10 m²) | Yasa Cd. **23** |
> | **1925** | **Akveren Makarna** (Coşkunsu ailesi, 4. nesil) | kuzey cephesi — parsel (40)/(42) bölgesi | Söğütlüçeşme Cd. **12/1** (~16) |
> | **1871 → ?** | **Kurukahveci Mehmet Efendi** *(Kadıköy şubesi)* | bitişiği — aynı kuzey cephesi | Söğütlüçeşme Cd. **12/1** |
>
> **Sokak adı göçü:** Pervititch "Söğütlü Çeşme Cad." (B) → **Yasa Cd.**  ·  Pervititch "T…L Sok." (K) → **Söğütlüçeşme Cd.**

**Konuşma metni:**
> Adanın kuzeybatı köşesinde Pervititch'in koyu vurguyla "**FİRİN**" yazdığı bir bina var: kuzey cephesinde parsel (40), batı cephesinde (34)–(36), batı duvarına yapışmış üç küçük ufak magazin daha — yani köşeyi saran, parça parça bir gıda tesisi. Kodlar `MB` tuğla, `V.F.` Fransız beton tonoz, `2½` kat, `TR.4` Türk kiremidi. Sigorta haritasının gözünde tek bir fırın bina-tipi. **Ama bugün baktığımızda, bu tek köşede üç ayrı tarihi marka yan yana duruyor — Türkiye'nin yaşayan gıda mirasının en yoğun istif edilmiş noktalarından biri.**
>
> Birincisi: **1836'da Balat'ta simit dükkânı açan Bulgar Ortodoks** **Kosma Stoyanof**'un oğlu **Dimitri Stoyanof** — Kadıköy'e geçiyor ve **1920'de Beyaz Fırın'ı açıyor**. Pervititch'in batı duvarındaki üç küçük magazinden en güneyde ve en büyük olanı — yaklaşık 10 m²'lik — bugün de aynı yerde, **Yasa Caddesi 23**'te, **5. nesil aynı aile** tarafından işletiliyor.
>
> İkincisi: **1925'te Mehmet Coşkunsu** aynı köşede — Pervititch'in büyük `FİRİN` etiketinin kuzey cephesinde — **Akveren Makarna**'yı kuruyor. Kendi sözleriyle *"yüzyıla yakın bir süredir Kadıköy Tarihi Çarşıdaki konumunda"*. Bugün **4. nesil**, hâlâ aynı bina. Yani Pervititch'in 1938'de "Fırın" yazdığında, Beyaz Fırın 18, Akveren 13 yaşında — ikisi de aynı köşede çalışıyor; sigorta haritası ikisini de tek bir "Fırın" bina-tipi etiketi altında topluyor, çünkü amacı yangın riski, marka değil.
>
> Üçüncüsü: **1871'de Eminönü Mısır Çarşısı'nda kurulan Kurukahveci Mehmet Efendi**'nin **Kadıköy şubesi** — bugün Akveren'in bitişiğinde, Söğütlüçeşme Caddesi 12'de. Şubenin tam açılış tarihi belge düzeyinde belgelenmemiş, ama "Kurukahveci" soyadı 1934'te alındıktan sonra büyüyen markanın 20. yüzyıl genişlemesinin bir parçası.
>
> Bir önemli detay: **sokak adları zaman içinde göç etmiş.** Pervititch'in "Söğütlü Çeşme Cad." dediği batı sokağı bugünkü **Yasa Caddesi**; Pervititch'in kuzeyde yazdığı "T…L Sok." ise bugünkü **Söğütlüçeşme Caddesi**. Yani çeşmenin adı, ana caddesini bile değiştirmiş — ama çeşmenin kendisi, parsel (39/2)'de, hâlâ yerinde duruyor.
>
> Sonuç: kilisenin (1694/1830) yanına 1920'de Bulgar Ortodoks bir fırın, 1925'te Türk-Müslüman bir makarnacı, 19. yüzyıl sonu marka olan bir kuru kahveci şubesi… **1372 m²'lik bir adada, en az 100 yıllık kesintisiz bir gıda-ve-mâbet omurgası, yedi ayrı kimlik.**

**AI prompt:**
> *"Slide titled 'Kahraman #2 — NW köşesi · üç tarihi marka tek bir köşede'. Layout: left panel a zoom of an old 1923/1938 Pervititch insurance-map corner with the 'FİRİN' label on parcel 40, smaller 'Fırın' on 34/36, and the three small magazines on the west wall — all highlighted with a glow. Right side a triptych of three logos/storefronts stacked vertically: Beyaz Fırın 1920, Akveren Makarna 1925, Kurukahveci Mehmet Efendi 1871. A bold centre headline: 'BİR KÖŞE · ÜÇ MARKA · 100+ YIL'. Below it a 3-row table with year / brand / Pervititch parcel / modern address. A small footer caption noting the street-name migration: 'Söğütlü Çeşme Cad. → Yasa Cd. · T…L Sok. → Söğütlüçeşme Cd.' Warm bread-crust + coffee-brown palette."*

**Gerekli dosya / veri:**
- `output/presentation/map_nw_corner_zoom.jpg` — NW köşesi yakın planı
- Beyaz Fırın storefront fotoğrafı (kendi çekersen en temizi · alternatif: beyazfirin.com'dan atıflı)
- Akveren Makarna storefront fotoğrafı (akveren.com / Foursquare'den atıflı)
- Kurukahveci Mehmet Efendi storefront / logo (mehmetefendi.com'dan atıflı)
- Sayılar: Beyaz Fırın koord. 40.9908 K, 29.0248 D · Mehmet Efendi koord. 40.990911 K, 29.025160 D
- Atıflar: beyazfirin.com/hikaye · yuzyillikhikayeler.com · kulturenvanteri.com · akveren.com · mehmetefendi.com · Kurukahveci Mehmet Efendi Wikipedia

---

## Slayt 7 — Ahşaplar: ne kaldı, ne gitti (8:15 – 9:00 · ~45 sn)

**Görsel:** sol = `map.png`'de **sarı (ahşap) parseller vurgulu**: (40)'ın cephesi, (42), (4), (4a), (39), INT-E2; sağ = bugünkü Kadıköy Çarşı ara sokak fotoğrafı (ayakta kalmış birkaç ahşap dokunun bulunduğu sokak).

**Slayt üzerindeki metin:**
> # Ahşap parseller — Pervititch'in zaman kapsülü
> - Sarı = `Class C` ahşap, küçük dükkân-evi tipolojisi
> - Bu adada: **(40)** cephesi · **(42)** vitrinli · **(4) + (4a)** İsmail Sok., bodrumlu · **(39)** SW köşesi · **INT-E2** avlu içi
> - 20. yy ortasından sonra çoğu 4-5 katlı betonarmeye dönüştü
> - Çarşının ara sokaklarında **bazıları hâlâ ayakta**, **2022'den beri tescilli koruma altında**
> - BIM = kaybolanın **dijital tanıklığı**

**Konuşma metni:**
> Pervititch'in sarı boyadığı parseller ahşap, C sınıfı yapılar — 19. yüzyılın küçük dükkân evleri. Adamızda: **(40)** Beyaz Fırın'ın ahşap çerçeveli cephesi, **(42)** dar bir vitrinli ahşap dükkân, **(4) ve (4a)** İsmail Sok. tarafında bodrumlu ahşap dükkân + iç avluya bakan ahşap eki, **(39)** güneybatı köşesi bodrumlu ahşap, **INT-E2** avlunun ortasında küçük bir bahçe-kenarı ahşap yapı. Bu parsellerin çoğu bugün yok: 20. yüzyıl ortasından sonra Kadıköy Çarşı'sındaki ahşap çevre, parça parça 4-5 katlı betonarme apartmanlarla değiştirildi. Ancak — ve bu önemli — çarşının ara sokaklarında hâlâ ahşap yapılar var, ve 2022'nin sit kararından sonra ne kalmışsa tescilli koruma altında. Söğütlü Çeşme'nin çevresindeki o 2½ katlı, vitrinli, cumbalı küçük ahşap dokuyu bugün toplu olarak tek yerde göremiyoruz; ama Pervititch'in çizdiği geometriyi BIM'e taşıyarak **"vardı bir zamanlar, şöyleydi"** diyebilen bir referans elde ettik. Kaybolanı kayıt altına almak — bu projenin asıl amacı.

**AI prompt:**
> *"Slide 'Ahşap parseller — Pervititch'in zaman kapsülü'. Left: a Pervititch sheet of a single Istanbul block with the wooden (yellow) parcels highlighted with a soft glow; small parcel numbers visible (40, 42, 4, 4a, 39, INT-E2). Right: a moody contemporary photograph of a narrow Kadıköy bazaar side-alley with a surviving 19th-century timber shop-house. Five Turkish bullets summarising: Class C, locations, mostly demolished, some surviving + 2022 listing, BIM as digital witness."*

**Gerekli dosya / veri:**
- `map.png` — sarı parsel vurgulu versiyon (Photoshop / PIL ile)
- Modern Kadıköy Çarşı ahşap sokak fotoğrafı — kaynak atıfla
- 2022 sit alanı kararı atfı

---

## Slayt 8 — Neden LOD3 BIM? · Kapanış argümanı (9:00 – 9:45 · ~45 sn)

**Görsel:** sol yarım = kâğıt harita, sağ yarım = canlı viewer'da döndürülen model, ortada büyük bir çift yönlü ok; altta 4 küçük ikon — koruma, mimarlık tarihi, simülasyon, kadastro karşılaştırması.

**Slayt üzerindeki metin:**
> # Neden LOD3? — sadece footprint değil
> - **Koruma planlaması** (planlama-öncesi referans)
> - **Mimarlık tarihi görselleştirmesi**
> - **Enerji / sismik / ışık simülasyonu**
> - **Kaybolan / değişen** binayı modern kadastroyla karşılaştırma
> *Pafta 147 bir laboratuvar · yöntem bütün Pervititch atlasına ölçeklenebilir*

**Konuşma metni:**
> Çoğu dijital tarihî İstanbul rekonstrüksiyonu footprint düzeyinde kalıyor — sadece kat planı. **LOD3** demek **cephe başına geometri, açıklık, malzeme, çatı strüktürü** demek. Bu seviye: **mirasın korunmasında planlama** için kullanılır, **mimarlık tarihi görselleştirmesinde** referans verir, **enerji, sismik, ışık simülasyonu** yapılabilir, **kaybolmuş veya değişmiş** binalar üzerinde modern kadastroyla karşılaştırma sağlar. Pafta 147 küçük bir laboratuvar — ama yöntem bütün Pervititch atlasına ölçeklenebilir. Yani prensip ispatlandığında, elimizde **kâğıttan dijital şehre geçen bir köprü** olur.

**AI prompt:**
> *"Slide 'Neden LOD3? — sadece footprint değil'. Split horizontal layout: left half a paper insurance map of one Istanbul block (sepia), right half a rotated 3D model of the same block in a web viewer. A large double-headed arrow in the middle. Below, four small flat icons with Turkish labels: 'Koruma planlaması', 'Mimarlık tarihi', 'Simülasyon', 'Kadastro karşılaştırması'. Closing tagline: 'Pafta 147 bir laboratuvar — yöntem bütün Pervititch atlasına ölçeklenebilir.'"*

**Gerekli dosya / veri:**
- `map.png` + viewer ekran görüntüsü
- (estetik için) 4 ikon

---

## Slayt 9 — Kapanış · QR & teşekkür (9:45 – 10:00 · ~15 sn)

**Görsel:** açılış slaytının sade kopyası — büyük QR, **hums.ilkeryoru.com**, altında "Teşekkürler."

**Slayt üzerindeki metin:**
> # Teşekkürler
> **hums.ilkeryoru.com**  —  modeli kendiniz döndürün
> *İlker Yörü · ilkeryoru.com · @1lker*

**Konuşma metni:**
> Modeli telefonunuzdan döndürmeye devam edin. Veri tablosuna da oradan ulaşabiliyorsunuz. Sorular için açığım. Teşekkürler.

**AI prompt:**
> *"Closing slide. Large clean QR code linking to **hums.ilkeryoru.com**, the URL written below in a calm serif. Sub-headline 'Teşekkürler — modeli kendiniz döndürün.' Author line: 'İlker Yörü · ilkeryoru.com'. Paper-cream + ink palette."*

**Gerekli dosya / veri:**
- QR kod (Slayt 1 ile aynı)

---

# Ek 1 — Master AI prompt (tüm sunumu tek seferde üretmek için)

**Gamma / Beautiful.ai / Canva Magic Design** gibi bir aracı kullanacaksanız aşağıdaki tek promptu yapıştırın; her başlık altındaki maddeyi ayrı slayt olarak üretecektir.

```
Title: HUMS — Pervititch 1923 · Block 147 (10-min talk, Turkish, museum-poster aesthetic, sepia + cream + terracotta accents)

Slide 1 — Açılış · QR & live viewer
- Headline: HUMS — Pervititch 1923 · Block 147
- Subhead: Kağıttan dijital şehre, bir blok
- Big QR linking to hums.ilkeryoru.com; URL beneath
- Background: a faint 3D render of a small Istanbul block with a domed church

Slide 2 — Pervititch Haritaları
- 1922-1945 · yangın sigortası haritaları · Jacques Pervititch
- Kayıt: malzeme, kat, tonoz, açıklık, ağaç
- Kaynak: 1938 Kadıköy 1:500 Plaka 08 (SALT Araştırma)
- Side-by-side: wide 1938 plate + zoomed Block 147

Slide 3 — Pafta 147 nerede
- Osmanağa Mh., Kadıköy · Yasa Cd. × Mühürdar Cd.
- Pervititch sokakları: Söğütlü Çeşme Cad. (B), İsmail Sok. (D)
- 46×52 m · 1 372 m² · 40.9907 K, 29.0251 D
- Hook: 1855 yangınından sonra Osmanlı'nın ilk ızgara planı burada
- 2022 sit alanı kapsamında
- Side-by-side: Pervititch sheet + modern satellite; '147' badge in the centre

Slide 4 — Veri hattı
- Pervititch raster → 20+ KML footprint → buildings.json (34 parsel) → block147.glb → IFC
- Horizontal flow arrow + viewer screenshot

Slide 5 — Kahraman #1 — Ayia Efimia Rum Ortodoks Kilisesi
- 451 Kalkedon Konsili'nin azizi
- 1694 Met. Gabriel · 1830 Met. II. Zaharias (Rus bağışı) · 1993 Met. III. Iokeim
- Tuğla beden, kiremit çatı, 4 fil ayağı pilastr, yüksek tamburlu merkezi kubbe, üç camlı tambur açıklığı
- Pervititch kodları: Tt. · 1=2 · 2p · 1er V.T. · "Enclos"
- Triptych: Pervititch sheet zoom + 3D church render + present-day photo

Slide 6 — Kahraman #2 — NW köşesi · üç tarihi marka tek bir köşede
- Bir tek Pervititch `FİRİN` etiketi, bugün ÜÇ marka:
  · Beyaz Fırın 1920 — Stoyanof ailesi (Bulgar Ortodoks, 5. nesil) — Yasa Cd. 23 — batı duvarındaki en güneydeki magazin (≈10 m²)
  · Akveren Makarna 1925 — Coşkunsu ailesi (4. nesil) — Söğütlüçeşme Cd. 12 — Pervititch parsel (40)/(42) kuzey cephesi
  · Kurukahveci Mehmet Efendi şubesi — ana marka 1871 (Eminönü) — Söğütlüçeşme Cd. 12, Akveren bitişiği
- Sokak adı göçü: "Söğütlü Çeşme Cad." → Yasa Cd.  ·  "T…L Sok." → Söğütlüçeşme Cd.
- Karakter cümlesi: Rum Ortodoks kilisesi + Bulgar Ortodoks fırını + Türk-Müslüman makarnacı + 1871 kuru kahveci şubesi + Ermeni eczacı + Rum şekerci + Osmanlı çeşmesi → bir 1372 m²'lik adada 100+ yıllık kesintisiz gıda-ve-mâbet omurgası
- Layout: Pervititch NW corner zoom (3 magazine + parsel 40/34/36 vurgulu) + 3 storefront/logo dikey triptych + tabloda yıl/marka/parsel/adres

Slide 7 — Ahşaplar: ne kaldı, ne gitti
- Sarı = Class C ahşap, 19. yy küçük dükkân evi
- Bu adada: (40), (42), (4), (4a), (39), INT-E2
- Çoğu yıkılıp 4-5 katlı betonarmeye dönüştü
- Çarşı ara sokaklarında bazıları ayakta · 2022'den beri tescilli koruma
- BIM = kaybolanın dijital tanıklığı
- Map (yellow parcels highlighted) + side-alley wooden-house photo

Slide 8 — Neden LOD3?
- Koruma planlaması · Mimarlık tarihi · Simülasyon · Kadastro karşılaştırması
- Pafta 147 laboratuvar · yöntem bütün Pervititch atlasına ölçeklenebilir
- Split: paper map ↔ web 3D viewer; 4 icons below

Slide 9 — Kapanış · QR
- Teşekkürler — hums.ilkeryoru.com
- Big QR; İlker Yörü · ilkeryoru.com
```

> *İpucu:* Gamma'ya bu blok-metni "create from text" olarak yapıştırın; tonu Türkçe ve "**museum poster · sepia · cream · terracotta**" diye belirleyin.

---

# Ek 2 — Asset envanteri (repo içi yollar)

| Tür | Yol | Açıklama |
|---|---|---|
| Pervititch master raster | `data/raw/raster/500_1938_APLPEKADI08.tif` (36 MB) | 1938 Kadıköy 1:500 plaka 08 |
| Pafta 147 kırpık | `map.png` | bloğun yakın planı |
| KML footprint klasörü | `data/raw/kml/*.kml` (21 dosya) | tüm gerçek izdüşümler |
| Block boundary KML | `data/raw/kml/blobk147layer-main.kml` | 1 372 m², 46×52 m |
| Church + kubbe KML | `data/raw/kml/churche-and-its-kubbe.kml` | 320 m², 22×24 m |
| Camlı + Clocher + (39/2) KML | `data/raw/kml/church-entrence-camli-area-(39-1*39-2)-with-clocher.kml` | 166 m² |
| Çeşme KML | `data/raw/kml/cesme-fountain.kml` | 7.6 m² |
| Fırın (40)+(42) KML | `data/raw/kml/building-entrence-40-42.kml` | 50.5 m² |
| Hesaplanmış KML metrikleri | `data/parsed/kml_metrics.json` | her KML için area / bbox / centroid |
| LOD3 buildings dataset | `data/parsed/buildings.json` | 34 parsel, tam LOD3 |
| 3D çıktı (model-viewer) | `output/gltf/block147.glb` | sunum modeli |
| Bağımsız kilise modeli | `output/gltf/CHURCH.glb` | yakın çekim için |
| Bina detay klasörleri | `output/buildings/{N-40, N-40-42, N-50, W-34-36-FIRIN}/` | parsel-bazlı çıktılar |
| Veri tablosu (Excel) | `output/block147_building_data.xlsx` | per-parcel master |
| Veri tablosu (HTML) | `output/data.html` | viewer'ın 'Data' linki |
| Canlı viewer | `output/viewer.html` ↔ **hums.ilkeryoru.com** | |
| Historical context MD | `Block147_Historical_Context.md` | tüm sunum verisinin ham kaynağı |
| Bu plan | `Block147_Sunum_Konusmasi.md` | bu dosya |

# Ek 3 — Sunum sırasında elden bırakmayacağınız numaralar

| Anahtar | Değer |
|---|---|
| Mahalle | Osmanağa Mh., Kadıköy |
| Bloğun bugünkü köşesi | Yasa Cd. × Mühürdar Cd. |
| Boyutlar | 46 × 52 m · **1 372 m²** |
| Merkez koord. | 40.9907° K, 29.0251° D |
| Pervititch sokakları (1923/38) | Söğütlü Çeşme Cad. (B), İsmail Sok. (D) |
| Kilise tarihleri | 1694 (Gabriel) · 1830 (Zaharias II, Rus bağışı) · 1 Nisan 1993 (Iokeim III) |
| Kilise footprint | **320.6 m²** · 22 × 24 m · merkez 40.99072, 29.02505 |
| Camlı + Clocher | 166 m² · 19 × 14.7 m |
| Çeşme | 7.6 m² (parsel 39/2) |
| Beyaz Fırın · aile | Kosma Stoyanof (Balat 1836) → Dimitri Stoyanof (Kadıköy 1920) → 5. nesil |
| Beyaz Fırın · adres + Pervititch | Yasa Cd. **23**, Osmanağa Mh. ≡ batı duvarındaki 3 küçük magazinden **en güneyde / en büyüğü** (~10 m², `near-39-open-32-magazine.kml`) — proje sahibinin yer bilgisi |
| Beyaz Fırın · koord. | 40.9908° K, 29.0248° D (Kültür Envanteri) |
| Akveren Makarna · kuruluş | **1925** — Mehmet Coşkunsu; *"yüzyıla yakın bir süredir Kadıköy Tarihi Çarşıdaki konumunda"* (kendi sitesi); 4. nesil |
| Akveren Makarna · adres + Pervititch | Söğütlüçeşme Cd. **12/1** (bazı kayıtlarda 16), Osmanağa Mh. — Pervititch parsel **(40)/(42)** kuzey cephesi |
| Mehmet Efendi · ana marka | **1871** — Mehmet Efendi (Eminönü Mısır Çarşısı); soyadı "Kurukahveci" 1934 |
| Mehmet Efendi · Kadıköy şubesi | açılış tarihi kamuya belgelenmemiş — büyük olasılıkla post-1934, Cumhuriyet sonrası genişleme |
| Mehmet Efendi · adres + koord. | Söğütlüçeşme Cd. **12/1**, Osmanağa Mh. — Akveren'in bitişiği, koord. **40.990911, 29.025160** (Yandex Haritalar) |
| Sokak adı göçü | Pervititch "Söğütlü Çeşme Cad." (B) → Yasa Cd. · Pervititch "T…L Sok." (K) → Söğütlüçeşme Cd. |
| Pervititch `FİRİN` kompleksi (tek tesis) | parsel (40) kuzey cephesi + (34)/(36) batı cephesi + batı duvarındaki 3 küçük magazin → bugün üç marka, iki cephe |
| 1855 yangını | 14 Ağustos 1855, Caferağa; ≈ 400 bina |
| Yangın sonrası plan | Hasan Tahsin Efendi, 1856; 6 m + 4.5 m sokaklar; ana aks Mühürdar Cd. |
| Sit kararı | 28.09.2022 · No. 9900 · Kentsel Sit + 3. Derece Arkeolojik Sit · 87 ha |
| Toplam parsel sayısı (model) | **34** (`buildings.json`) |
| KML toplam | **21** (`kml_metrics.json`) — 20 yapı + blok sınırı |

---

# Ek 4 — Kaynaklar (sunum sonu)

- Pervititch atlası — 1938 Kadıköy plate 08 (Salt Araştırma)
- İstanbul Ansiklopedisi — *Ayia Efimia Rum Ortodoks Kilisesi*
- Tarihi İstanbul — *Ayia Efimia Rum Ortodoks Kilisesi*
- Beyaz Fırın resmi sayfa — beyazfirin.com/hikaye
- Yüzyıllık Hikâyeler — *Beyaz Fırın*
- Akveren Makarna — kurumsal "Tarihçe" — akveren.com
- Kurukahveci Mehmet Efendi — resmi "Tarihçe" — mehmetefendi.com/hakkimizda/tarihce/marka-donemi
- Kurukahveci Mehmet Efendi — Kadıköy şubesi iletişim — mehmetefendi.com/iletisim/sube-kadikoy
- Kurukahveci Mehmet Efendi — Wikipedia (Türkçe)
- Yüzyıllık Markalar Derneği — *Beyaz Fırın*
- Kültür Envanteri — *Beyaz Fırın* (Osmanağa Mh. koordinatı)
- Pınar Erkan, *"1855 Kadıköy Yangını ve İlk Izgara Plan Uygulaması"*, Gazete Kadıköy
- İBB Şehir Planlama — *Kadıköy Merkez Sit Alanı* (28.09.2022, K.9900)
- Emre Muşazlıoğlu, *"Kadıköy'ün en asude en kibar caddesi: Mühürdar"*, Gazete Kadıköy
- HUMS proje — **hums.ilkeryoru.com**
