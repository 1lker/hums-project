# Block 147 — Cowork (Gamma / Beautiful.ai / Copilot / Tome) Prompt Paketi

> **HUMS — Pervititch 1923/1938 · Pafta 147 · LOD3 BIM**
> Tema: **Kadıköy 1930'lar → 2026, bir adanın kayıt + dönüşüm hikâyesi**
> Süre: **10 dakika · 9 slayt · Türkçe · vurucu, gerçek bilgi merkezli**
> Canlı viewer: **hums.ilkeryoru.com**

Bu belge **doğrudan kopyala-yapıştır** içindir. Önce **§1 Master Prompt**'u sohbetin/aracın başına yapıştır; bütün slayt yapısını üretir. Sonra gerektiğinde **§2 Slayt-bazlı promptlar** ile tek tek slaytları rafine et. **§3 Fact Bundle** her zaman tutarlı kullanılması için araca verilen kesin veri paketidir — hiçbir tarih, isim, koordinat tahmin değil.

---

## §1 — MASTER PROMPT (sohbetin başına yapıştır)

```text
Senden Türkçe, 10 dakikalık, 9 slaytlık, "müze-poster" estetiğinde (sepia + krem + terrakota vurgular; serif başlık + ince sans gövde) bir akademik-popüler sunum hazırlamanı istiyorum.

KONU: HUMS projesi — 1923/1938 tarihli Pervititch yangın-sigorta haritalarındaki Kadıköy Pafta 147'nin (Ayia Efimia Rum Ortodoks Kilisesi'nin bulunduğu blok) LOD3 düzeyinde 3 boyutlu BIM yeniden inşası. Sunumun omurgası ise "**Kadıköy 1930'lardan bugüne dönüşüm**" anlatısı — bir tek 1372 m²'lik adada bu büyük dönüşümün hem yaşamış hem hayatta kalmış kahramanlarını anlatarak.

KESİN KURALLAR:
1. Tüm rakam, tarih, isim, adres ve koordinatlar AŞAĞIDAKİ FACT BUNDLE'a sadık kalacak. Bilmediğin bir veriyi UYDURMA — yazmamış olarak bırak.
1b. HER SAYISAL ya da TARİHSEL İDDİA için §6 Referanslar listesinden bir kaynak kodu (örn. `[R-F1]`, `[R-C2]`) slayt notunda parantez içinde belirtilecek. Kaynak kodu olmayan iddiayı yazma; ya §6'daki bir referansa bağla ya da satırı çıkar.
2. Slayt başına ortalama 65 saniye konuşma süresi (≈ 140 sözcük) varsay. Slayt metinleri kısa: başlık + maksimum 5 madde / küçük tablo.
3. Türkçe; özel isimler ve sokak adları orijinal yazımıyla (ş, ç, ğ, ü, ö). Pervititch'in Fransızca etiketleri italik korunsun ('FİRİN', 'V.F.', 'V.T.', 'MB', 'TR.4', 'Tt.', '1=2', 'Mg.', 'Camlı (Vitre)', 'Clocher', 'Enclos').
4. Politik dönüşüm anlatısı (1942 Varlık Vergisi, 6-7 Eylül 1955, 1964 sürgün) **belge düzeyinde, edebî ya da duygusal abartıdan uzak** olmalı — sayılar Wikipedia / İHD / Gazete Kadıköy gibi atıflanabilir kaynaklara dayanıyor. Aya Efimia'nın 1955'te zarar görmüş olabileceğine dair iddia GENEL bir cümlenin parçası ("İstanbul'daki 73 Rum Ortodoks kilisesinin tamamı ateşe verildi"); kiliseye spesifik saldırı kanıtı GET edilirse o ifade kalsın, edilmezse "İstanbul genelinde 73 Rum kilisesi" şeklinde genel bırak.
5. Görsel önerileri ASCII olarak slayt notlarına eklensin (her slayt için "Layout / Visual brief").
6. Açılış ve kapanış slaytlarına **büyük QR kod** ve URL: hums.ilkeryoru.com.

SLAYT YAPISI (9 slayt, toplam 10 dk):

Slayt 1 — Açılış · QR + live viewer (45 sn)
Slayt 2 — Pervititch: zamanın kâğıt fotoğrafı (45 sn)
Slayt 3 — Pafta 147 · 1923-1938 (75 sn)
Slayt 4 — Transformasyon arkı 1930'lar → 2026 (135 sn) ★ HERO
Slayt 5 — Pafta 147'de neler hayatta kaldı, neler kayboldu (75 sn)
Slayt 6 — Hayatta kalan #1 · Ayia Efimia Kilisesi (75 sn)
Slayt 7 — Hayatta kalan #2 · NW köşesi · üç tarihi marka (90 sn)
Slayt 8 — HUMS BIM · kâğıttan dijital şehre (45 sn)
Slayt 9 — Kapanış · QR + teşekkür (15 sn)

ŞİMDİ FACT BUNDLE — bütün veriyi içeriden çek; uydurma:

[ FACT BUNDLE — bkz. §3 ]

Şu çıktıyı üret:
- Her slayt için: BAŞLIK + ALT BAŞLIK + 4-6 madde / küçük tablo + KONUŞMA NOTLARI (~140 sözcük) + LAYOUT BRIEF (görselin nerede ne olacağı)
- En sona: bir KAYNAKLAR slaytı (atıflar listesi)
- Tonu: bilgili, kuru olmayan, vurucu ama klişesiz; resmî bir BIM/akademi konferansı sahnesine uygun.
- Estetik: müze afişi · krem zemin (#f4efe6) · terrakota vurgular (#c25c2a) · ince serif başlık · sans madde.
```

---

## §2 — Slayt-bazlı promptlar (master sonrası tek tek rafine için)

Her birini, master prompt'tan sonra ayrı bir mesaj olarak yapıştırabilirsin. Tool karakterli (Gamma "Refine slide") ya da düz sohbet (ChatGPT/Copilot) hepsinde çalışır.

### Slayt 1 — Açılış · QR + live viewer (45 sn)
```text
Slayt 1'i şöyle kur:
- Tam genişlikte koyu krem zemin; sol yarı: tek satırlık büyük serif başlık "HUMS — Pervititch 1923/1938 · Pafta 147"; altında ince ikinci satır "Kâğıttan dijital şehre, bir blok ve dönüşümü"
- Sağ yarı: BÜYÜK QR KOD (hedef = https://hums.ilkeryoru.com), QR'ın altında URL düz metin
- Alt sol köşede yazar künyesi: "İlker Yörü · CTO Mindra · ilkeryoru.com"
- Konuşma notları 3 cümle: telefonunuzla QR'ı okutun (canlı 3D model), sunum boyunca açık tutun, bugün size bir kağıt haritayı dijital şehre dönüştürmenin hikâyesini ve aynı adada 100 yıllık dönüşümün izini anlatacağım.
```

### Slayt 2 — Pervititch: zamanın kâğıt fotoğrafı (45 sn)
```text
Slayt 2 için içerik:
Başlık: "Pervititch · zamanın kâğıt fotoğrafı"
Alt başlık: "1922-1945 · Yangın-sigorta haritaları · Jacques Pervititch"
4 madde:
1. Bina başına: duvar malzemesi (taş/tuğla/ahşap), kat sayısı, tonoz türü (Voûte Française, Voûte Turque), açıklıklar, hatta bahçedeki ağaçlar
2. İstanbul'un erken-Cumhuriyet en ayrıntılı kayıtlı görüntüsü
3. Kaynağımız: 1938 Kadıköy 1:500 plaka 08 (SALT Araştırma)
4. Bizim için bir "BIM seed" — her parsel veri taşıyor

Layout: solda 1938 Pervititch plakasının geniş görüntüsü, sağda Pafta 147 üzerine zoom (kilise kubbesi merkezde); sepia palette.
Konuşma notları (~110 sözcük): Pervititch Hırvat asıllı yangın-sigorta haritacısı, 1922-1945 arası İstanbul'u blok blok kaydetti — fakat amaç sanat değil, sigorta riski; her parsel için duvar malzemesi, kat sayısı, tonoz türü, açıklıklar yazılı; bu ayrıntı bizim için BIM tohumu oluyor.
```

### Slayt 3 — Pafta 147 · 1923-1938 (75 sn)
```text
Slayt 3:
Başlık: "Pafta 147 · Kadıköy Çarşı'sının göbeği"
Sağ-sol layout: solda map.png (1923 Pervititch sheet), sağda 1938 sheet'inin aynı blok yakın planı; arada "147" rozetı.

Madde (kısa):
- Mahalle: Osmanağa  ·  Bugün: Yasa Cd. × Mühürdar Cd.
- Pervititch sokakları: "Söğütlü Çeşme Cad." (B), "İsmail Sok." (D)
- 46 × 52 m  ·  1 372 m²  ·  34 parsel modellendi
- Anchor: Ayia Efimia Rum Ortodoks Kilisesi (1694/1830)
- Tarihsel arka plan: 14 Ağustos 1855 Kadıköy yangını → 400 bina yandı → Hasan Tahsin Efendi'nin çizdiği OSMANLI'NIN İLK MODERN IZGARA PLANI 1856'da uygulandı — bu adanın grid'i tam o plan

Konuşma notları (~150 sözcük): Pafta 147 bugünkü Kadıköy Çarşı'sının göbeğinde, Osmanağa Mahallesi, Yasa ve Mühürdar caddelerinin köşesinde. Pervititch'in dilinde batı sokağı "Söğütlü Çeşme Cad.", doğu sokağı "İsmail Sok."; 46 × 52 metre, 1372 m². Adanın çekirdeği Aya Efimia Rum Ortodoks Kilisesi — yapı 1694, bugünkü biçim 1830. Daha vurucu bir başka katman: bu adanın grid planı 1855 Kadıköy yangınından sonra çiziliyor — 14 Ağustos 1855'te Caferağa'da çıkan yangın 400 binayı yaktı; mühendis Hasan Tahsin Efendi 1856'da Osmanlı şehirciliğinin ilk modern ızgara planını burada uyguladı, ana aks Mühürdar Caddesi. Yani gördüğümüz blok 1856 sonrası bir doku — Pervititch onu 70-80 yıl sonra kayda alıyor.
```

### Slayt 4 — Transformasyon arkı 1930'lar → 2026 (135 sn · HERO) ★
```text
Slayt 4 — sunumun OMURGASI. Bu slaytta tarih şeridi tasarımı kullan: yatay zaman çizgisi, üstte yıllar, altında olaylar, vurucu sayılarla.

Başlık: "Transformasyon · 1925'ten 2026'ya bir adanın çevresinde 100 yıl"

Tarih şeridi (1925 → 2026):
1925   İstanbul'da Rum Ortodoks nüfus ≈ 100.000  (Lozan-sonrası, mübadeleden muaf)
1942   Varlık Vergisi · İstanbul gayrimüslim ticareti yıkıma uğrar
1955   6-7 EYLÜL OLAYLARI · İstanbul Ekspres "Atatürk'ün evi bombalandı" manşeti yalan haberle ateşlenir; Beyoğlu-Şişli-Nişantaşı-KADIKÖY-Kuzguncuk-Ortaköy-Bakırköy-Adalar'da yağma; 4 214 ev, 1 000 işyeri, 73 RUM ORTODOKS KİLİSESİ, 26 okul tahrip edilir
1964   12 000 Yunan vatandaşı sürgün edilir; aile ağı kopar; geriye kalan Rum nüfus hızla erir
1965   Kat Mülkiyeti Kanunu · konak/ahşap arazileri bölünür → çok katlı apartmanlaşma başlar
1940-60lar  Kadıköy'de ahşap konak ve dükkân-evleri betonarme villalarla değiştirilir
1972-73    Bostancı-Erenköy planı + Boğaz Köprüsü → inşaat patlaması
2006   İstanbul Rum nüfus ≈ 2 500 — 1925'in %2,5'i
2022 · 28 Eylül   KORUMA KURULU KARAR 9900: Kadıköy Merkez Geleneksel Çarşı'da 87 hektarlık alan KENTSEL SİT + 3. DERECE ARKEOLOJİK SİT ilan edilir; Pafta 147 bu kapsamda
2026   HUMS · Pafta 147'nin LOD3 BIM'i tamamlanır; canlı viewer hums.ilkeryoru.com

Konuşma notları (~280 sözcük): "Bugün gördüğümüz Kadıköy Çarşı, Pervititch'in çizdiği Kadıköy değil. Bir asırda blokun çevresi tepeden tırnağa dönüştü — hem demografik, hem fiziksel. 1925'te Lozan'dan sonra Anadolu Rumları mübadele edilirken İstanbul Rumları kararname dışı tutuldu; şehirde yaklaşık 100 bin Rum yaşıyordu, Kadıköy onların yoğun yerleştiği ilçelerden biriydi — Aya Efimia kilisesinin etrafındaki bu blok da öyle. Sonra zincir başlıyor: 1942 Varlık Vergisi gayrimüslimlerin ticaretine ağır darbe vurdu. 1955'in 6 ve 7 Eylül gecelerinde — 'Atatürk'ün evi bombalandı' yalan haberi tetikleyici oldu — Beyoğlu, Şişli, Nişantaşı, KADIKÖY, Kuzguncuk, Ortaköy ve Adalar'da yağma ve yangınlar başladı; resmi rakamlara göre 4 bin 214 ev, bin işyeri, ve İstanbul'daki 73 Rum Ortodoks kilisesinin tamamı tahrip edildi. 1964'te 12 bin Yunan vatandaşı bir gecede sürgün edildi. 2006'ya gelindiğinde şehirdeki Rum nüfus 2 bin 500'e — yani 1925'in yüzde iki buçuğuna — düşmüştü. Fiziksel dönüşüm bununla eşzamanlı: 1965 Kat Mülkiyeti Kanunu, parsellerin bölünüp çok katlı apartmana çevrilmesinin kapısını açtı; 1940'lardan 1970'lere kadar Kadıköy'ün ahşap konakları yerini önce iki-üç katlı betonarme villalara, sonra dört-beş katlı apartmanlara bıraktı. Pafta 147'de Pervititch'in sarıyla gösterdiği ahşap dükkân-evleri, kiliseyi çevreleyen küçük masonik yapılar, çoğunlukla bu dalgada eridi. Ve 2022'de — Koruma Kurulu'nun 9900 sayılı kararıyla — Kadıköy Çarşı'nın 87 hektarı Kentsel Sit ve 3. Derece Arkeolojik Sit ilan edildi; geç ama hâlâ ayakta kalan bir doku için. Bugün biz Pafta 147'yi LOD3 BIM'e taşırken aslında bu dönüşümün YALNIZCA HARİTASINI değil, KAYBINI da kayıt altına alıyoruz."

Layout brief: yatay zaman çizgisi (timeline) üstte; alta her dönüm noktası için küçük ikon + tek satır açıklama + vurucu sayı; sağ alt köşede küçük bir "Pervititch 1938 sheet" ve "modern 2025 hava fotoğrafı" karşılaştırma kutusu.
```

### Slayt 5 — Pafta 147'de neler hayatta kaldı, neler kayboldu (75 sn)
```text
Slayt 5:
Başlık: "Pafta 147 · Bir adanın hafıza envanteri"

İki sütunlu liste:

HAYATTA KALAN (4)               KAYBOLAN / DEĞİŞEN
- Ayia Efimia Kilisesi          - Sarı (ahşap, C sınıfı) parsellerin çoğu
  (1694/1830)                     (40) ahşap cephe, (42), (4)+(4a), (39)
- Beyaz Fırın (1920)            - 19. yy küçük dükkân-evi tipolojisi
- Akveren Makarna (1925)        - Rum nüfus (1925: ~100K → 2006: ~2.5K)
- Kurukahveci Mehmet Efendi     - Yunanca dükkân tabelaları
  Kadıköy şubesi                - Sokak adı "Söğütlü Çeşme Cad." → bugün Yasa Cd.
- Çeşme (parsel 39/2)           - "T…L Sok." (kuzey) → bugün Söğütlüçeşme Cd.
                                - Çoğu masonik dükkân (4-5 katlı betona dönüştü)

Konuşma notları (~150 sözcük): "Bir adada ne hayatta kalır, ne kaybolur? Pafta 147'de hayatta kalanlar belli: kilise — 1694'ten beri, üç yangın, bir restorasyon görerek — hâlâ ayakta. Çeşme — söğüt-fontaynı, parsel 39/2 — yerinde. Kuzeybatı köşesinde 1920'de açılan Beyaz Fırın, 1925'te kurulan Akveren Makarna, ana markası 1871'e dayanan Kurukahveci Mehmet Efendi'nin Kadıköy şubesi — üçü de hâlâ aynı 30 metrelik köşede çalışıyor. Kaybolanlar: Pervititch'in sarıyla boyadığı yüzlerce metre karelik ahşap dükkân-evi dokusu; eski Rum nüfusunun varlığı; Yunanca tabelalar; iki sokağın eski isimleri — 'Söğütlü Çeşme Cad.' bugün Yasa Cd. oldu, eskiden 'T…L Sok.' olan kuzey sokağı şimdi Söğütlüçeşme Cad. — yani çeşmenin adı kendisi taşırken bile, taşıdığı sokak değişti."

Layout brief: iki sütunlu temiz tablo; sol sütun yeşil tikler, sağ sütun gri ışıltısız; üstte ortada Pafta 147'nin ahşap parsellerin vurgulu (yellow) küçük diyagramı.
```

### Slayt 6 — Hayatta kalan #1 · Ayia Efimia Kilisesi (75 sn)
```text
Slayt 6:
Başlık: "Hayatta kalan #1 · Ayia Efimia Rum Ortodoks Kilisesi"
Alt başlık: "Kalkedon'un kendi şehidi · 451 Konsili'nin azizi"

Triptik görsel: solda 1923 Pervititch sheet'inden kilise yakın planı (kubbe sembolü, "Rum-Ortodoks Kilises 'Ayia-Eftimia'", testere kenarlı "Enclos"); ortada LOD3 BIM render'ı (HUMS'tan kubbe + clocher); sağda bugünkü kilise fotoğrafı (Wikimedia, çan kulesi net).

4 madde:
- 1694  Met. Gabriel · yeniden inşa
- 1830  Met. II. Zaharias · Rus bağışıyla büyütme
- 1955  6-7 Eylül olayları · İstanbul'daki 73 Rum kilisesinin tamamı hasar gördü
- 1993 · 1 Nisan  Met. III. Iokeim · restorasyon, ibadete açılış
- Pervititch kodları doğruluyor: `Tt.` kiremit çatı · `1=2` yüksek nef · `2p` iki kısmi kat · `1er V.T.` Türk tonozu · merkezde kubbe · `Enclos` (testere kenarlı avlu duvarı)
- Modelde: tuğla beden, 4 fil ayağı pilastr üzerinde yüksek tamburlu kubbe, drumda üç küçük kemerli camlı açıklık (haritada üç işaret var; sadakatle korundu)

Konuşma notları (~150 sözcük): "Bu kilisenin adı Eufemia tesadüfen seçilmedi — Khalkedon'un, yani Kadıköy'ün, kendi şehidi. 451'de bu şehirde toplanan Kalkedon Konsili Hristiyan teolojisinin en büyük kavşaklarından biri ve kilise o anının sembolik mührü. Yapı hikâyesi kısa: Bizans manastırı yıkıldıktan sonra 1694'te Metropolit Gabriel'in izniyle yeniden inşa edildi, 1830'da Metropolit II. Zaharias Rusya'dan topladığı bağışla büyüttü — bugün gördüğümüz yapı o aşamadan kalma: tuğla beden, kiremit çatı, dört 'fil ayağı' pilastrın taşıdığı yüksek tamburlu merkezi kubbe. 1955'te İstanbul'daki tüm 73 Rum kilisesi gibi hasar gördü, 20. yüzyıl boyunca harap düştü; 1 Nisan 1993'te Metropolit III. Iokeim'in çalışmalarıyla restore edilip yeniden ibadete açıldı. Pervititch'in 1923 ve 1938 sayfaları yapı kodlarıyla bu kiliseyi doğruluyor — biz de modelde sadece bu kodlara sadık bir şekilde kurduk."
```

### Slayt 7 — Hayatta kalan #2 · NW köşesi · üç tarihi marka (90 sn)
```text
Slayt 7 — bu da hero. Bir köşe, üç marka.

Başlık: "Hayatta kalan #2 · BİR KÖŞE · ÜÇ MARKA · 100+ YIL"
Alt başlık: "Pervititch'in tek bir `FİRİN` etiketi → bugün üç ayrı kurumsal kimlik"

Layout: solda map.png'in NW köşesi yakın planı — `FİRİN V.F. +MB 2½` parselin (40)'i, batı cephesindeki `Fırın TR.4 +3` (34/36), ve batı duvarına yapışmış üç küçük magazin (`near-39-open-32-*.kml`) vurgulu glow ile; sağda üç markanın storefront/logo'su dikey panel halinde, ortada bir tablo.

Tablo:
| Yıl  | Marka                                       | Pervititch karşılığı                                            | Bugün                              |
|------|---------------------------------------------|------------------------------------------------------------------|-------------------------------------|
| 1920 | Beyaz Fırın · Stoyanof ailesi (5. nesil)    | batı duvarındaki en güneydeki magazin (~10 m²)                  | Yasa Cd. 23 (eski "Söğütlü Çeşme") |
| 1925 | Akveren Makarna · Coşkunsu ailesi (4. nesil)| parsel (40)/(42) kuzey cephesi                                  | Söğütlüçeşme Cd. 12/1 (eski "T…L") |
| 1871 | Kurukahveci Mehmet Efendi · ana marka       | Akveren bitişiği, aynı kuzey cephesi (Kadıköy şubesi sonradan)  | Söğütlüçeşme Cd. 12/1               |

Sokak adı göçü (alt bant): "Söğütlü Çeşme Cad." → Yasa Cd.  ·  "T…L Sok." → Söğütlüçeşme Cd.

Konuşma notları (~190 sözcük): "Şimdi adanın kuzeybatı köşesine zoom yapıyoruz. Pervititch'te 'FİRİN' büyük harflerle yazılmış parsel (40); batı cephesinde küçük 'Fırın' notu olan (34) ve (36); ve batı duvarına yapışmış üç küçük magazin. Pervititch bunları tek bir bina tipi olarak topluyor — yangın haritasının gözünde hepsi 'fırın'. Bugün ise tam bu noktada üç ayrı tarihi marka çalışıyor: 1920'de Bulgar Ortodoks Stoyanof ailesinin açtığı Beyaz Fırın — bugün 5. nesil, Yasa Caddesi 23'te, batı duvarındaki en büyük magazinin yerinde. Sadece beş yıl sonra, 1925'te Mehmet Coşkunsu aynı köşede Akveren Makarna'yı kuruyor — kuzey cephesinde, hâlâ 4. nesil, hâlâ aynı bina. Üçüncü taraf: 1871'de Mısır Çarşısı'nda kurulan Kurukahveci Mehmet Efendi'nin Kadıköy şubesi, bugün Akveren'in tam bitişiğinde. Yani 1372 metre karelik bir adada Rum Ortodoks kilisesi, Bulgar Ortodoks fırını, Türk-Müslüman makarnacı ve 19. yüzyıl Türk kuru kahvecisinin şubesi — hepsi yan yana, en az yüz yıllık kesintisiz bir gıda-ve-mâbet omurgası. Bir dönüşüm hikâyesinin direnen tarafı."
```

### Slayt 8 — HUMS BIM · kâğıttan dijital şehre (45 sn)
```text
Slayt 8:
Başlık: "HUMS · kâğıttan LOD3 BIM'e"
Alt başlık: "Bir adanın dijital tanıklığı"

Yatay akış diyagramı:
[Pervititch raster · 1938] → [21 KML footprint · 1 372 m²] → [buildings.json · 34 parsel · LOD3] → [block147.glb · model-viewer] → [IFC · BIM downstream]

3 madde:
- LOD3 = her cephe, açıklık, tonoz, çatı eğimi ayrı bir mesh elemanı
- Pafta 147 küçük bir laboratuvar; yöntem bütün Pervititch atlasına ölçeklenebilir
- Canlı: hums.ilkeryoru.com (telefonunuzda)

Konuşma notları (~110 sözcük): "Veri hattı kısa: 1938 Pervititch rasterinden başlıyoruz, üzerine 21 KML poligonuyla binaların gerçek izdüşümlerini bindiriyoruz; sonra Pervititch'in malzeme ve kat kodlarını parsel başına ekleyerek 34 parselli bir LOD3 binalar veri kümesi çıkarıyoruz. Bunu doğrudan glTF ve IFC'ye export ediyoruz; tarayıcıda model-viewer ile döndürebilir hale geliyor. LOD3'ün anlamı: yalnızca footprint değil — her cephe, her açıklık, her tonoz ayrı bir mesh elemanı. Pafta 147 küçük bir laboratuvar ama yöntem bütün Pervititch atlasına, hatta diğer kentlere ölçeklenebilir."
```

### Slayt 9 — Kapanış · QR + teşekkür (15 sn)
```text
Slayt 9 — kapanış. Açılış slaytının sade kopyası.
- Büyük QR (hums.ilkeryoru.com), URL altta
- "Teşekkürler · hums.ilkeryoru.com · modeli kendiniz döndürün"
- Sol alt: İlker Yörü · ilkeryoru.com
- Konuşma notları: "Modeli telefonunuzda döndürmeye devam edin, veri tablosuna da oradan ulaşabilirsiniz. Sorular için açığım. Teşekkürler."
```

### Slayt 10 — Kaynaklar (sunum sonu, isteğe bağlı tek slayt)
```text
Slayt 10 — Kaynaklar listesi. Tek slayt, 3 sütun:

PRİMARYE (BIM kaynakları)
- Pervititch atlası — 1938 Kadıköy 1:500 plaka 08 (Salt Araştırma)
- HUMS proje deposu — github.com/1lker/hums-project + hums.ilkeryoru.com
- Pafta 147 LOD3 veri seti — buildings.json (34 parsel)

TARİHSEL (kilise + dönüşüm)
- İstanbul Ansiklopedisi — Ayia Efimia Rum Ortodoks Kilisesi
- Tarihi İstanbul — Ayia Efimia Rum Ortodoks Kilisesi
- Pınar Erkan — "1855 Kadıköy Yangını ve İlk Izgara Plan Uygulaması", Gazete Kadıköy
- İBB Şehir Planlama Müdürlüğü — Kadıköy Merkez Sit Alanı (28.09.2022 · K.9900)
- 6-7 Eylül Olayları — Vikipedi · İnsan Hakları Derneği (İHD)
- Arkitera / Kadıköy Kaymakamlığı — Geçmişin Modern Mimarisi Kadıköy

YAŞAYAN MARKALAR
- Beyaz Fırın — beyazfirin.com/beyazfirin-hikaye
- Akveren Makarna — akveren.com (kurumsal tarihçe)
- Kurukahveci Mehmet Efendi — mehmetefendi.com/hakkimizda/tarihce/marka-donemi + sube-kadikoy
- Yüzyıllık Hikâyeler — yuzyillikhikayeler.com (Beyaz Fırın)
- Yüzyıllık Markalar Derneği · Kültür Envanteri — koordinatlar
```

---

## §3 — FACT BUNDLE (master prompt'a göm; tahmin yok)

```text
== ANCHOR / KONUM ==
- Pafta 147: Kadıköy, Osmanağa Mahallesi
- Bugünkü köşe: Yasa Cd. × Mühürdar Cd.
- Pervititch sokakları (1923/1938): "Söğütlü Çeşme Cad." (BATI), "İsmail Sok." (DOĞU), "T…L Sok." (KUZEY), "A…D Sok." (GÜNEY)
- Bugünkü sokak göçü: Pervititch "Söğütlü Çeşme Cad." → Yasa Cd.  ·  Pervititch "T…L Sok." → Söğütlüçeşme Cd.
- Blok boyutu: 46 × 52 m · 1 372 m²
- Blok centroid: 40.9907° K, 29.0251° D
- Model: 34 parsel · 21 KML footprint · LOD3

== KİLİSE — AYIA EFİMİA RUM ORTODOKS KİLİSESİ ==
- İsimlendirme: Kalkedon (Khalkedon) = Kadıköy; aziz Eufemia; 451 Kalkedon Konsili
- Bizans dönemi: aynı yerde "Ayia Basis" / "Ayia Euphemia Metropolitlik Manastırı"
- 1694: Met. Gabriel · yeniden inşa
- 1830: Met. II. Zaharias · Rusya'dan toplanan bağışla büyütme
- 1955: 6-7 Eylül olayları kapsamında İstanbul'daki 73 Rum kilisesinin tamamı hasar gördü (kiliseye spesifik kanıt yoksa şehir geneli ifade kullan)
- 1 Nisan 1993: Met. III. Iokeim · restorasyon ve ibadete açılış
- Mimari: tuğla beden, kiremit çatı, dört fil ayağı pilastr üzerinde yüksek tamburlu merkezi kubbe, tamburda üç küçük kemerli camlı açıklık
- Pervititch kodları (sheet): `Tt.` kiremit çatı · `1=2` yüksek nef · `2p` iki kısmi kat · `1er V.T.` Türk tonozu · kubbe sembolü · testere kenarlı `Enclos` (avlu duvarı)
- KML: footprint 320.6 m² · bbox 22 × 24 m · merkez ≈ 40.99072, 29.02505

== HİKAYE BİNALARI · NW KÖŞESİ ÜÇ MARKA ==
1) BEYAZ FIRIN
   - Aile: Kosma (Kozma) Stoyanof / Stanyof · Bulgaro-Makedonyalı Ortodoks · 1836'da Balat'ta simit dükkânı açtı
   - Kadıköy şubesi: oğul Dimitri Stoyanof ("Üsküdarlı Dimitri Stanyof") · 1920'de Beyaz Fırın'ı açtı
   - Bugün: 5. nesil aile yönetiminde
   - Adres: Osmanağa Mh., Yasa Cd. No: 23, Kadıköy 34714
   - Pervititch karşılığı (proje sahibinin yer bilgisi): batı duvarındaki 3 küçük magazinden EN GÜNEYDE ve EN BÜYÜK olanı (~10.3 m², `near-39-open-32-magazine.kml`)
   - Koordinat: 40.9908° K, 29.0248° D (Kültür Envanteri)

2) AKVEREN MAKARNA
   - Kurucu: Mehmet Coşkunsu (merhum)
   - Yıl: 1925
   - Kendi sözüyle: "yüzyıla yakın bir süredir Kadıköy Tarihi Çarşıdaki konumunda gıda sektöründe hizmet vermektedir"
   - Bugün: 4. nesil
   - Adres: Osmanağa Mh., Söğütlüçeşme Cd. No: 12/1 (bazı kayıtlarda 16)
   - Pervititch karşılığı: parsel (40)/(42) kuzey cephesi (büyük FİRİN etiketinin bulunduğu kompleks)

3) KURUKAHVECİ MEHMET EFENDİ (Kadıköy şubesi)
   - Ana marka: Mehmet Efendi · 1871 · Eminönü Mısır Çarşısı
   - Aile soyadı: 1934'te Surname Law ile "Kurukahveci"
   - Kadıköy şubesinin açılış tarihi: kamuya açık bir kaynakta belgelenmemiş — post-1934, Cumhuriyet sonrası genişleme döneminden
   - Adres: Osmanağa Mh., Söğütlüçeşme Cd. No: 12/1, Kadıköy 34714
   - Koordinat: 40.990911 K, 29.025160 D (Yandex Haritalar)

== TARİHSEL DÖNÜŞÜM TARİHLERİ (kronoloji ile) ==
- 14 Ağustos 1855: Caferağa yangını · ≈ 400 bina · Surp Takavor kilisesi hasar
- 1856: Hasan Tahsin Efendi · Osmanlı'nın ilk modern ızgara planı · 6 m + 4.5 m sokaklar · çıkmaz yok · ana aks Mühürdar Cd.
- 1923: Pervititch atlası 1. baskı (Pafta 147 ham hâli)
- 1925: İstanbul Rum Ortodoks nüfus ≈ 100 000 (Lozan mübadelesinden muaf)
- 1934: Soyadı Kanunu (Kurukahveci, Coşkunsu vb. aile soyadları)
- 1938: Pervititch Kadıköy 1:500 plaka 08 güncel baskısı (`data/raw/raster/`)
- 1942: Varlık Vergisi · İstanbul gayrimüslim ticaretinin sermaye taşıyıcılığı çökerildi
- 6-7 Eylül 1955: İstanbul Pogromu — İstanbul Ekspres "Atatürk'ün evi bombalandı" yalan haberi tetiklemesiyle Beyoğlu, Şişli, Nişantaşı, Kadıköy, Kuzguncuk, Ortaköy, Bakırköy, Adalar'da yağma · 4 214 ev, 1 000 işyeri, 73 Rum Ortodoks kilisesi, 26 okul tahrip
- 1964: ≈ 12 000 Yunan vatandaşı sürgün
- 1965: Kat Mülkiyeti Kanunu · konak/villa parsellerinin bölünmesi ve apartmanlaşma başlangıcı
- 1940-60'lar: Kadıköy banliyösünde ahşap konaklar betonarme villalara dönüştürüldü
- 1972: Bostancı-Erenköy bölge planı
- 1973: 1. Boğaz Köprüsü açılışı → inşaat patlaması
- 1993 · 1 Nisan: Ayia Efimia restorasyonu ve yeniden ibadete açılış
- 2006: İstanbul Rum nüfusu ≈ 2 500 — 1925'in %2,5'i
- 2022 · 28 Eylül: Kültür Varlıklarını Koruma Bölge Kurulu KARAR 9900 — Kadıköy Merkez Geleneksel Çarşı'da 87 hektarlık alan KENTSEL SİT + 3. DERECE ARKEOLOJİK SİT (Pafta 147 dâhil)
- 2026 · Mayıs: HUMS Pafta 147 LOD3 BIM canlı (hums.ilkeryoru.com)

== HARİTA ÜZERİNDE GÖRÜNEN İSİMLİ KULLANIMLAR ==
- Parsel (40): `FİRİN` (büyük harf) · `MB+V.F.+2½`
- Parsel (34)+(36) batı cephesi: `Fırın` · `TR.4 +3+ MB+V.F.+2½`
- Parsel (16) SE köşesi: `+1 MO. Şekerci Mg. T. Mol[la]` (proprietor adı belirsiz — "T. Molla" / "T. Mollas" muhtemel)
- Parsel (39/1): `Camlı (Vitre)` · `Clocher` · `1 bs. F.` · `1er V.T.`
- Parsel (39/2): `Çeşme`
- Kilise parseli: `Rum-Ortodoks Kilises "Ayia-Eftimia"` · `Tt.` · `1=2` · `2p` · `1er V.T.` · merkez kubbe · `Enclos` testere kenarı
- Diğer parseller (4, 6, 8, 10, 12, 14, 41, 43, 45, 44, 46, 48, 50, 52, 54): `Mg.` (magasin/dükkân) + tonoz kodları (`V.F.`, `V.T.`)

== AHŞAP (CLASS C) PARSELLER ==
- (40) Beyaz Fırın'ın ahşap cephesi (gövde MB tuğla)
- (42) Vitrinli ahşap dükkân
- (4) bodrumlu ahşap (`T. bs. Vx. MG.`)
- (4a) iç avluya bakan ahşap ek (`1 bs. F.`)
- (39) güneybatı köşesi bodrumlu ahşap (`T. 1 bs. M.`)
- INT-E2 avlu içi ahşap (~10 m²)

== KANIT KAYNAKLARI (URL'ler) ==
- Pervititch 1938: archives.saltresearch.org (Kadıköy 1:500 plaka 08)
- İstanbul Ansiklopedisi · Ayia Efimia: istanbulansiklopedisi.org/handle/rek/5128
- Tarihi İstanbul · Ayia Efimia: tarihi.ist/ayia-efimia-rum-ortodoks-kilisesi/
- Wikimedia Commons (kilise fotoğrafları, CC-BY-SA): commons.wikimedia.org/wiki/Category:Saint_Euphemia_Greek_Orthodox_Church_in_Kadıköy
- Beyaz Fırın · hikâye: beyazfirin.com/beyazfirin-hikaye  ·  yuzyillikhikayeler.com/en/historic-brands/beyaz-firin/  ·  kulturenvanteri.com/en/yer/beyaz-firin/
- Akveren Makarna · tarihçe: akveren.com
- Kurukahveci Mehmet Efendi · tarihçe: mehmetefendi.com/hakkimizda/tarihce/marka-donemi  ·  şube: mehmetefendi.com/iletisim/sube-kadikoy  ·  Wikipedia: tr.wikipedia.org/wiki/Kurukahveci_Mehmet_Efendi
- 1855 yangını / ızgara plan: Pınar Erkan, Gazete Kadıköy
- 6-7 Eylül 1955: tr.wikipedia.org/wiki/6-7_Eylül_Olayları  ·  ihd.org.tr · Gazete Kadıköy
- 2022 sit kararı: sehirplanlama.ibb.istanbul/kadikoy-merkez-sit-alani/
- Kadıköy dönüşüm (1960-80): kadikoy.gov.tr/gecmisin-modern-mimarisi-kadikoy-ilcemiz · arkitera.com/haber/gecmisin-modern-mimarisi-1-kadikoy/
- HUMS canlı viewer: hums.ilkeryoru.com
```

---

## §4 — Stil rehberi (her arka arkaya istek için ekle)

```text
STİL & TON:
- Estetik: müze afişi · krem zemin (#f4efe6) · ink siyah/grafit yazı · terrakota vurgular (#c25c2a) · ince serif başlıklar (Playfair / Cormorant / EB Garamond uygun) · sans madde gövde
- Görsel hiyerarşi: başlık 36-44pt, madde 16-20pt, konuşma notları slayt altında 11pt
- Yan boşluk: cömert (12-15%); slaytlar nefes alsın
- İkonlar: minimum, ince çizgi, tek renk (terrakota veya grafit)
- Renkten kaçın: aşırı parlak, gradient ya da emoji yok. Vurgu için sadece terrakota.
- Yazı tonu: bilgili ama klişesiz. "Hikaye" anlatımı değil, "kayıt" tutumu — kurmaca abartı yok.
- Cümleler kısa, somut. "Belki, sanıyorum" gibi belirsizlik yerine ya kesin sayı ya açık "kaynak X" referansı.
- Türkçe karakter setini koru. Pervititch'in Fransızca kodlarını italik ve aynen yaz.
- Sayıları boşluklu gruplandır: "100 000", "1 372 m²", "4 214 ev".
```

---

## §5 — Hızlı sevkiyat checklist

Cowork'e ne taşıyacaksın:

1. **§1 Master Prompt**'u kopyala-yapıştır ilk mesaj olarak — FACT BUNDLE'ı içine göm (yukarıdaki [ FACT BUNDLE ] placeholder'ını §3 ile doldur).
2. Tool sana 9 slayt taslağı üretecek. Her slayt için ihtiyaç duyarsan **§2 Slayt-bazlı promptlardan** ilgili olanı tekrar yapıştırarak rafine et.
3. **§3 Fact Bundle**'a sapma olduğunda "FACT BUNDLE'a bağlı kal — yukarıda yazılmamış bir tarih/isim üretme" diyerek kırp.
4. **§4 Stil rehberi**'ni tool şikayet ederse tekrar ekle.
5. Görselleri `output/presentation/` klasöründen sürükle-bırak:
   - `qr_hums_ilkeryoru.png` → Slayt 1 + Slayt 9
   - `pervititch_1938_full_annotated.jpg` → Slayt 2
   - `pervititch_1938_block147_zoom.jpg` → Slayt 3
   - *(Slayt 4 için kullanıcının kendi seçeceği transformasyon görselleri — tarih şeridi tool tarafından üretilecek)*
   - `map_wooden_highlight.jpg` → Slayt 5
   - `map_church_zoom.jpg` + `aya_efimia_church.jpg` (veya `_yellow.jpg`) → Slayt 6
   - `map_nw_corner_zoom.jpg` + (Beyaz Fırın/Akveren/Mehmet Efendi storefront fotoğrafları, kullanıcı kendisi çekebilir veya kurumsal sitelerden atıflı alabilir) → Slayt 7
   - `flow_diagram.png` → Slayt 8

---

---

## §6 — TAM REFERANSLAR (her iddia bu listeden bir koda bağlanır)

Aşağıdaki tüm referanslar **gerçek, açık erişimli, doğrulanmış URL'lerdir**. Master prompt'un kuralı (1b) gereği AI tool her sayısal/tarihsel iddiada bu koddan birini parantez içinde slayt notuna yazmak zorundadır. Hiçbir referans uydurulmamış — sunum sonu Kaynaklar slaytında aynısı görünecek.

### A — Pervititch atlası & temel kaynak
- **[R-A1]** Salt Araştırma (SALT Research). *Jacques Pervititch Sigorta Haritaları* dijital koleksiyonu. Kadıköy 1:500 plaka 08 (1938 baskısı). `archives.saltresearch.org`
- **[R-A2]** HUMS proje deposu — `data/raw/raster/500_1938_APLPEKADI08.tif` (georeferenced, EPSG:32635, 0.1 m/px). github.com/1lker/hums-project

### B — Aya Efimia Rum Ortodoks Kilisesi
- **[R-B1]** İstanbul Ansiklopedisi. "AYİA EFİMİA RUM ORTODOKS KİLİSESİ." `istanbulansiklopedisi.org/handle/rek/5128`
- **[R-B2]** *Tarihi İstanbul.* "Ayia Efimia Rum Ortodoks Kilisesi." `tarihi.ist/ayia-efimia-rum-ortodoks-kilisesi/`
- **[R-B3]** Wikimedia Commons. *Category: Saint Euphemia Greek Orthodox Church in Kadıköy* (kilisenin CC-BY-SA fotoğrafları). `commons.wikimedia.org/wiki/Category:Saint_Euphemia_Greek_Orthodox_Church_in_Kadıköy`
- **[R-B4]** Lonely Planet. "Aya Efimia Rum Ortodoks Kilisesi." `lonelyplanet.com/turkey/istanbul/kadikoy/attractions/aya-efimia-rum-ortodoks-kilisesi/`
- **[R-B5]** Kadıköy Life. "Kadıköy'de tarihin tanığı 'Ayia Euphemia Kilisesi'." `kadikoylife.com`
- **[R-B6]** Wikidata. *Q25404984 · Agia Efimia church (Turkey)* — koordinat, kuruluş ve dış kimlik referansları.

### C — Yaşayan markalar
- **[R-C1]** Beyaz Fırın. "Hikâye." `beyazfirin.com/beyazfirin-hikaye`
- **[R-C2]** Yüzyıllık Hikâyeler / Hundred Year Stories. "Beyaz Fırın." `yuzyillikhikayeler.com/en/historic-brands/beyaz-firin/`
- **[R-C3]** Yüzyıllık Markalar Derneği. "Beyaz Fırın." `yuzyillikmarkalar.org/uye-markalarimiz/beyaz-firin/`
- **[R-C4]** Kültür Envanteri / Cultural Inventory. "Beyaz Fırın" (Osmanağa Mh. koordinat: 40.9908066, 29.0248280). `kulturenvanteri.com/en/yer/beyaz-firin/`
- **[R-C5]** Akveren Makarna. *Tarihçe* — kurumsal sayfa. `akveren.com`
- **[R-C6]** Kurukahveci Mehmet Efendi. *Tarihçe — Marka Dönemi.* `mehmetefendi.com/hakkimizda/tarihce/marka-donemi`
- **[R-C7]** Kurukahveci Mehmet Efendi. *Şube (Kadıköy) iletişim sayfası* — Osmanağa Mh., Söğütlüçeşme Cd. No: 12/1. `mehmetefendi.com/iletisim/sube-kadikoy`
- **[R-C8]** Vikipedi (TR). "Kurukahveci Mehmet Efendi." `tr.wikipedia.org/wiki/Kurukahveci_Mehmet_Efendi`
- **[R-C9]** Yandex Haritalar. *Kurukahveci Mehmet Efendi Mahdumları* — koordinat 40.990911, 29.025160. `yandex.com.tr/maps/org/kurukahveci_mehmet_efendi_mahdumlari/172237500940/`

### D — Kadıköy şehir tarihi & 1855 yangını
- **[R-D1]** Erkan, Pınar. "1855 Kadıköy Yangını ve İlk Izgara Plan Uygulaması." *Gazete Kadıköy.* `gazetekadikoy.com.tr/yazarlar/pinar-erkan/1855-kadikoy-yangini-ve-ilk-izgara-plan-uygulamasi`
- **[R-D2]** Muşazlıoğlu, Emre. "Kadıköy'ün en asude en kibar caddesi: Mühürdar." *Gazete Kadıköy.*
- **[R-D3]** Kadıköy Belediyesi. "Kadıköy'ün Tarihçesi." `kadikoy.bel.tr/en/kadikoyun-tarihcesi`
- **[R-D4]** T.C. Kadıköy Kaymakamlığı. "Geçmişin Modern Mimarisi · Kadıköy." `kadikoy.gov.tr/gecmisin-modern-mimarisi-kadikoy-ilcemiz`
- **[R-D5]** Arkitera. "Geçmişin Modern Mimarisi - 1: Kadıköy." `arkitera.com/haber/gecmisin-modern-mimarisi-1-kadikoy/`

### E — 1942 Varlık Vergisi
- **[R-E1]** Vikipedi (TR). "Varlık Vergisi." `tr.wikipedia.org/wiki/Varl%C4%B1k_Vergisi`
- **[R-E2]** Aktar, Ayhan. *Varlık Vergisi ve Türkleştirme Politikaları.* İletişim Yayınları, 2000. *(akademik temel referans)*

### F — 6-7 Eylül 1955 Olayları
- **[R-F1]** Vikipedi (TR). "6-7 Eylül Olayları." `tr.wikipedia.org/wiki/6-7_Eyl%C3%BCl_Olaylar%C4%B1`  *(temel istatistikler: 4 214 ev / 1 000 işyeri / 73 kilise / 26 okul tahrip)*
- **[R-F2]** İnsan Hakları Derneği (İHD). "6-7 Eylül 1955: Yalnızca Bir Devlet Operasyonu mu?" `ihd.org.tr/6-7-eylul-1955-yalnizca-bir-devlet-operasyonu-mu/`
- **[R-F3]** Gazete Kadıköy. "6-7 Eylül olaylarının 69'uncu yılında." `gazetekadikoy.com.tr/gundem/6-7-eylul-olaylarinin-69uncu-yilinda`
- **[R-F4]** Euronews Türkiye. "6-7 Eylül olaylarının yıl dönümü." `tr.euronews.com/2021/09/06/6-7-eylul-olaylar-65-y-l-donumu-neler-yasand-nas-l-hat-rlan-yor-`
- **[R-F5]** Vryonis Jr., Speros. *The Mechanism of Catastrophe: The Turkish Pogrom of September 6-7, 1955, and the Destruction of the Greek Community of Istanbul.* greekworks.com, 2005. *(akademik referans)*

### G — 1964 sürgün ve Rum nüfus erimesi
- **[R-G1]** Vikipedi (TR). "1964 Yunan Sürgünü" / "İstanbul Rumları." `tr.wikipedia.org/wiki/İstanbul_Rumları`
- **[R-G2]** Güven, Dilek. *Cumhuriyet Dönemi Azınlık Politikaları ve Stratejileri Bağlamında 6-7 Eylül Olayları.* İletişim Yayınları, 2005. *(akademik referans — Rum nüfus erimesi tablolarıyla)*
- **[R-G3]** Vikipedi'nin 6-7 Eylül maddesi (R-F1) içinde: "İstanbul Rum nüfus 1925 ≈ 100 000 → 2006 ≈ 2 500" verisi.

### H — 1965 Kat Mülkiyeti Kanunu & Kadıköy apartmanlaşması
- **[R-H1]** Vikipedi (TR). "Kat Mülkiyeti Kanunu." `tr.wikipedia.org/wiki/Kat_M%C3%BClkiyeti_Kanunu`
- **[R-H2]** Arkitera (R-D5) — Kadıköy'ün 1960-1980 dönüşümü; ahşap konak yıkımı + betonarme villa + çok katlı apartman dalgaları.
- **[R-H3]** Kadıköy Kaymakamlığı (R-D4) — "Geçmişin Modern Mimarisi · Kadıköy."
- **[R-H4]** Academia.edu (Tuba İnal Çekiç, Z. Pelin Korur, Görgün Erkalmış). "Yeni orta sınıf ve kültürel sermaye ekseninde mekânın dönüşümü: Kadıköy Tarihi Çarşı ve Moda örnekleri." `academia.edu/48833575`

### I — 2022 Sit Alanı kararı
- **[R-I1]** İBB Şehir Planlama Müdürlüğü. "Kadıköy Geleneksel Çarşı ve Moda Kentsel ve 3. Derece Arkeolojik Sit Alanı İlan Edildi." *Karar No. 9900 / 28.09.2022 / 87 hektar.* `sehirplanlama.ibb.istanbul/kadikoy-merkez-sit-alani/`

### J — HUMS projesi
- **[R-J1]** HUMS canlı viewer. `hums.ilkeryoru.com`
- **[R-J2]** Proje deposu. `github.com/1lker/hums-project`
- **[R-J3]** Pafta 147 LOD3 BIM veri seti — `data/parsed/buildings.json` (34 parsel) + `data/parsed/kml_metrics.json` (21 KML)
- **[R-J4]** Jacques Pervititch hakkında ek arka plan — *Toplumsal Tarih Akademi*, "1922 Öncesinde Jacques Pervititch." `dergipark.org.tr/en/pub/ttakademi`

### K — Annuaire Oriental (ek veri arkeolojisi)
- **[R-K1]** Internet Archive. *Annuaire Oriental 1889-1890* (tam OCR metin). `archive.org/details/annuaire-oriental-1890`
- **[R-K2]** Salt Araştırma. *Annuaire Oriental* dijital koleksiyonu (1891-1922 baskıları). `archives.saltresearch.org/handle/123456789/2301`
- **[R-K3]** Büktel, Esranur. "Cervati Directories / Cervati Yıllıkları (Indicateur Ottoman, Indicateur Oriental, Annuaire Oriental, Şark Ticaret Yıllığı) 1880-1938." Academia.edu. `academia.edu/112889311`

---

## §7 — Slayt başına referans haritası (cowork'e "şunu nereye bağla" diye söylenir)

Master prompt çalıştığında AI tool her madde / sayı için aşağıdaki eşlemeyi kullanmalıdır:

| Slayt | Referans verilecek iddialar | Bağlanan kod(lar) |
|---|---|---|
| 1 | (yok — sadece QR) | — |
| 2 | Pervititch 1922-1945, 1938 plaka 08, SALT | [R-A1] [R-A2] [R-J4] |
| 3 | Pafta 147 koordinat & boyut · 1855 yangın · ızgara plan · Aya Efimia | [R-D1] [R-D3] [R-B1] [R-A2] |
| 4 (HERO) | Rum nüfus 1925 ≈ 100 000 / 2006 ≈ 2 500 · Varlık Vergisi · 6-7 Eylül istatistikleri · 1964 sürgün · 1965 Kat Mülkiyeti · Kadıköy apartmanlaşma · 2022 sit kararı | [R-E1] [R-E2] [R-F1] [R-F2] [R-G1] [R-G2] [R-G3] [R-H1] [R-H2] [R-D4] [R-D5] [R-I1] |
| 5 | Hayatta kalan kurumlar · sokak adı göçü · ahşap kaybı | [R-B1] [R-C1..C9] [R-D2] [R-H2] |
| 6 | Aya Efimia 1694/1830/1955/1993, mimarisi | [R-B1] [R-B2] [R-F1] (1955 için) |
| 7 | Beyaz Fırın 1836/1920/5. nesil · Akveren 1925/4. nesil · Mehmet Efendi 1871/Kadıköy şubesi | [R-C1..C4] [R-C5] [R-C6..C9] |
| 8 | HUMS pipeline + 34 parsel + 21 KML | [R-J1] [R-J2] [R-J3] [R-A2] |
| 9 | (sadece QR) | — |
| 10 (Kaynaklar) | Tüm §6 listesi | tümü |

---

*Hazırlık tarihi: 2026-05-12 · Live: hums.ilkeryoru.com · İlker Yörü · CTO Mindra*
