# Block 147 — Sunum Görsel Paketi

Bu klasör, [`Block147_Sunum_Konusmasi.md`](../../Block147_Sunum_Konusmasi.md) içindeki 9 slayt için hazırlanmış görseller içerir. Gamma / Keynote / PowerPoint / Canva'ya direkt sürükle-bırak ile koyabilirsin.

Tüm dosyalar **slayt başına önerilen kullanım** sırasında listelenmiştir.

---

## Asset → Slayt eşlemesi

| Dosya | Boyut | Slayt | Nasıl kullanılır |
|---|---:|---:|---|
| `qr_hums_ilkeryoru.png` | <1 KB | **1**, **9** | büyük QR kod (hedef = `https://hums.ilkeryoru.com`); açılışta sağda, kapanışta ortada |
| `pervititch_1938_full.jpg` | 1.35 MB | **2** | 1938 Kadıköy 1:500 plaka 08'in tamamı (2000 px) |
| `pervititch_1938_full_annotated.jpg` | 1.35 MB | **2** veya **3** | aynı plaka, Pafta 147 etrafı kırmızı/sarı çerçeveyle vurgulu + etiket |
| `pervititch_1938_block147_zoom.jpg` | 1.02 MB | **3** | 1938 plakasından Pafta 147 + komşu bloklar (1400×1400) — "147" rozetli, "(143-148)" komşuları görünür, bonus olarak **`MUSTAFA ve MURAT Odun ve Kömür Deposu`** (Blok 152) etiketini gösterir |
| `flow_diagram.png` | 33 KB | **4** | "Pervititch raster → KML footprint → buildings.json → block147.glb → IFC" yatay akış |
| `map_church_zoom.jpg` | 330 KB | **5** | 1923 sheet (`map.png`) içinden kilise + kubbe yakın planı |
| `aya_efimia_church.jpg` | 814 KB | **5** | bugünkü Aya Efimia Kilisesi — sokaktan giriş, çan kulesi (Clocher) net görünür · *© Wikimedia Commons, CC-BY-SA* |
| `aya_efimia_church_yellow.jpg` | 875 KB | **5** (alternatif) | aynı kilise, başka açı — sarı avlu duvarı, beyaz kapı · *© Wikimedia Commons, CC-BY-SA (Yellow Church — panoramio)* |
| `map_nw_corner_zoom.jpg` | 201 KB | **6** | 1923 sheet'inde NW köşesi: parsel (40) "FİRİN" + (42) ve (34)(36) "Fırın" işaretleri |
| `map_se_corner_zoom.jpg` | 262 KB | **6** veya **bonus** | SE köşesi: parsel (16) **"Şekerci · T. Molla?"** etiketi |
| `map_wooden_highlight.jpg` | 701 KB | **7** | `map.png`'in **ahşap (sarı) parselleri parlatan** versiyonu — geri kalan doku desature edilmiş; (40) cephesi, (42), (4)+(4a), (39), INT-E2 vurgulu |

---

## Slayt 6 (Beyaz Fırın) için fotoğraf

Beyaz Fırın'ın bugünkü vitrin fotoğrafı **Wikimedia'da yok** ve resmi sitesi telif altında. Üç seçenek:

1. **Kendi fotoğrafını çek** (en temizi, telif sorunu yok): Yasa Cd. No: 23, Osmanağa Mh., Kadıköy. Vitrin + tabela tek karede.
2. **Resmi siteden** (beyazfirin.com) ekran görüntüsü al → slayt altına "Görsel: beyazfirin.com" atfı düş.
3. **Tripadvisor / Google Maps** kullanıcı fotoğraflarından birine link ver — atıfla.

Olmadığı zaman, **`map_nw_corner_zoom.jpg`** (Pervititch'in çizdiği fırın) + bir "Yasa Cd. 23" künye bloğu zaten slaytı dolduruyor; bugünkü fotoğraf "bonus" niteliğinde.

---

## QR kod

QR kod hedefi: **`https://hums.ilkeryoru.com`**

Yeniden üretmek istersen:
```
https://api.qrserver.com/v1/create-qr-code/?size=800x800&margin=10&data=https%3A%2F%2Fhums.ilkeryoru.com
```

---

## Atıflar (sunum kaynaklar slaytı için)

- **1938 Pervititch raster** (`500_1938_APLPEKADI08.tif`) — Salt Araştırma arşivi · Jacques Pervititch atlası, Kadıköy 1:500, plaka 08.
- **Aya Efimia kilise fotoğrafları** — Wikimedia Commons:
  - *Saint_Euphemia_Greek_Orthodox_Church_in_Kadıköy,_Istanbul.jpg* (CC-BY-SA)
  - *Yellow_Church_-_panoramio.jpg* (CC-BY-SA, Panoramio user)
- **1923 map.png** — Pervititch atlası 1923 baskısı, Pafta 147 (proje deposu).

---

## Boyut özeti

Toplam görsel paketi ≈ **7 MB** — sunum aracına rahatlıkla yüklenir, hiçbir görseli ayrı host etmeye gerek yok.

```
qr_hums_ilkeryoru.png                       <1 KB
flow_diagram.png                            33 KB
map_nw_corner_zoom.jpg                     201 KB
map_se_corner_zoom.jpg                     262 KB
map_church_zoom.jpg                        330 KB
map_wooden_highlight.jpg                   701 KB
aya_efimia_church.jpg                      814 KB
aya_efimia_church_yellow.jpg               875 KB
pervititch_1938_block147_zoom.jpg        1 016 KB
pervititch_1938_full.jpg                 1 351 KB
pervititch_1938_full_annotated.jpg       1 351 KB
─────────────────────────────────────────────────
Toplam                                  ≈ 7 MB
```
