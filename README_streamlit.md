# ⚡ EPIAS Elektrik Verisi Çekici - Streamlit Version

Bu uygulama Türkiye Elektrik Piyasası (EPIAS) şeffaflık platformundan elektrik üretim verilerini çeker ve Excel formatında sunar.

## 🌐 Live Demo

**Uygulama Linki:** [Streamlit Cloud'da çalışacak]

## 📋 Özellikler

- ⚡ **Anlık Veri Çekme**: EPIAS API'sinden gerçek zamanlı elektrik verisi
- 📊 **Excel Export**: Verileri Excel formatında indirme
- 🏭 **Santral Filtreleme**: Belirli santraller için veri çekme
- 📈 **İlerleme Takibi**: Gerçek zamanlı işlem durumu
- 🔒 **Güvenli Giriş**: EPIAS hesabı ile kimlik doğrulama
- 📱 **Responsive Tasarım**: Mobil ve masaüstü uyumlu

## 🚀 Kullanım

1. **Giriş Yapın**: EPIAS şeffaflık platformu hesabınızla giriş yapın
2. **Tarih Seçin**: Veri çekmek istediğiniz tarih aralığını belirleyin
3. **Santral Seçin** (İsteğe bağlı): Belirli bir santral için filtreleme yapın
4. **Veri Çekin**: "Veri Çekmeyi Başlat" butonuna tıklayın
5. **İndirin**: Excel dosyasını bilgisayarınıza indirin

## 🛠️ Teknik Detaylar

### Kullanılan Teknolojiler
- **Streamlit**: Web arayüzü
- **Pandas**: Veri işleme
- **Requests**: HTTP istekleri
- **OpenPyXL**: Excel dosya oluşturma

### API Endpoints
- EPIAS Authentication API
- EPIAS Injection Quantity API
- Power Plant List API

## 📊 Veri Türleri

Uygulama aşağıdaki elektrik verilerini çeker:
- **Enjeksiyon Miktarı**: Santrallerin elektrik üretim miktarları
- **Santral Bilgileri**: Santral listesi ve detayları
- **Zaman Serileri**: Saatlik/günlük üretim verileri

## 🔧 Geliştirme

### Yerel Kurulum
```bash
# Repository'yi klonlayın
git clone https://github.com/ahmetardacelik/santralData.git
cd santralData

# Bağımlılıkları yükleyin
pip install -r requirements_streamlit.txt

# Uygulamayı çalıştırın
streamlit run streamlit_app.py
```

### Deployment
Bu uygulama [Streamlit Cloud](https://streamlit.io/cloud) üzerinde ücretsiz olarak deploy edilmiştir.

## 📝 Lisans

Bu proje açık kaynak kodludur.

## 👨‍💻 Geliştirici

**Ahmet Arda Çelik**
- GitHub: [@ahmetardacelik](https://github.com/ahmetardacelik)

## 📞 Destek

Herhangi bir sorun veya öneri için GitHub Issues bölümünü kullanabilirsiniz.

---

⚡ **EPIAS Elektrik Verisi Çekici** - Türkiye elektrik piyasası verilerine kolay erişim! 