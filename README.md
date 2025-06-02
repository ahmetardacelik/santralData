# EPIAS Elektrik Verisi Çekici

Modern web arayüzü ile EPIAS (Elektrik Piyasası İşletmecisi) elektrik üretim verilerini çekme uygulaması.

## 🚀 Özellikler

- **Modern Web Arayüzü**: Responsive ve kullanıcı dostu interface
- **EPIAS Authentication**: Güvenli EPIAS hesap girişi
- **Veri Çekme**: Esnek tarih aralığı ve santral seçimi
- **Progress Tracking**: Gerçek zamanlı ilerleme takibi
- **Excel Export**: Detaylı Excel raporları
- **REST API**: Programatik erişim için RESTful API
- **Docker Support**: Kolay deployment ve ölçeklendirme

## 📋 Gereksinimler

### Sistem Gereksinimleri
- Python 3.11+
- Docker & Docker Compose (isteğe bağlı)
- Modern web tarayıcısı

### EPIAS Hesabı
- Geçerli EPIAS kullanıcı hesabı
- Elektrik verilerine erişim yetkisi

## 🛠️ Kurulum

### 1. Projeyi İndirin
```bash
git clone <repository-url>
cd epias-elektrik-veri-cekici
```

### 2. Python ile Kurulum

#### Sanal Ortam Oluşturun
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# veya
venv\Scripts\activate     # Windows
```

#### Bağımlılıkları Yükleyin
```bash
pip install -r requirements.txt
```

#### Environment Ayarları
```bash
cp env.example .env
# .env dosyasını düzenleyin
```

#### Sunucuyu Başlatın
```bash
cd backend
python app.py
```

### 3. Docker ile Kurulum

#### Geliştirme Ortamı
```bash
docker-compose up --build
```

#### Production Ortamı
```bash
docker build -t epias-app .
docker run -p 5000:5000 epias-app
```

## 🌐 Kullanım

### Web Arayüzü
1. Tarayıcınızda `http://localhost:5000` adresine gidin
2. EPIAS kullanıcı bilgilerinizle giriş yapın
3. Tarih aralığını seçin
4. Santral seçimi yapın (isteğe bağlı)
5. "Veri Çekmeyi Başlat" butonuna tıklayın
6. İşlem tamamlandığında Excel dosyasını indirin

### API Kullanımı

#### Authentication
```bash
curl -X POST http://localhost:5000/api/auth \
  -H "Content-Type: application/json" \
  -d '{"username": "your-email", "password": "your-password"}'
```

#### Veri Çekme
```bash
curl -X POST http://localhost:5000/api/extract \
  -H "Content-Type: application/json" \
  -d '{
    "start_date": "2024-01-01",
    "end_date": "2024-01-07",
    "chunk_days": 15
  }'
```

#### İşlem Durumu
```bash
curl http://localhost:5000/api/extract/status/{task_id}
```

## 📊 API Endpoints

| Method | Endpoint | Açıklama |
|--------|----------|----------|
| `GET` | `/` | API ana sayfa |
| `GET` | `/api/health` | Sistem durumu |
| `POST` | `/api/auth` | Kullanıcı girişi |
| `GET` | `/api/plants` | Santral listesi |
| `POST` | `/api/extract` | Veri çekme başlat |
| `GET` | `/api/extract/status/{id}` | İşlem durumu |
| `GET` | `/api/download/{file}` | Dosya indirme |
| `POST` | `/api/logout` | Çıkış |

## 🔧 Konfigürasyon

### Environment Variables

```env
# Server Configuration
FLASK_ENV=development
SECRET_KEY=your-secret-key
PORT=5000

# Session Configuration
SESSION_TIMEOUT=7200

# CORS Configuration
CORS_ORIGINS=*
```

### Chunk Boyutu
Büyük tarih aralıkları için veri alma performansını optimize etmek için chunk boyutunu ayarlayabilirsiniz:
- **Küçük aralıklar (1-7 gün)**: 7 gün
- **Orta aralıklar (1-4 hafta)**: 15 gün
- **Büyük aralıklar (1+ ay)**: 30 gün

## 📁 Proje Yapısı

```
epias-elektrik-veri-cekici/
├── backend/
│   ├── app.py              # Flask web server
│   ├── epias_extractor.py  # EPIAS API client
│   ├── logs/               # Log dosyaları
│   └── downloads/          # İndirilen dosyalar
├── frontend/
│   ├── index.html          # Ana sayfa
│   ├── styles.css          # CSS stilleri
│   └── script.js           # JavaScript logic
├── requirements.txt        # Python bağımlılıkları
├── Dockerfile             # Docker image
├── docker-compose.yml     # Docker compose
└── README.md             # Bu dosya
```

## 🚢 Deployment

### Heroku Deployment
```bash
# Heroku CLI ile
heroku create your-app-name
heroku config:set SECRET_KEY=your-production-secret
git push heroku main
```

### Railway Deployment
1. Railway.app'e proje bağlayın
2. Environment variables ekleyin
3. Otomatik deployment

### VPS Deployment
```bash
# Sunucuda
git clone <repository>
cd epias-elektrik-veri-cekici

# Docker ile
docker-compose -f docker-compose.prod.yml up -d

# Veya systemd service olarak
sudo systemctl enable epias-app
sudo systemctl start epias-app
```

## 📈 Monitoring

### Sistem Durumu
```bash
curl http://localhost:5000/api/health
```

### Loglar
```bash
# Application logs
tail -f backend/logs/epias_api.log

# Container logs
docker-compose logs -f epias-app
```

## 🔒 Güvenlik

- **Environment Variables**: Hassas bilgileri env dosyalarında saklayın
- **HTTPS**: Production'da SSL sertifikası kullanın
- **Session Management**: Güvenli session konfigürasyonu
- **Input Validation**: API girdi doğrulaması
- **Rate Limiting**: API abuse koruması

## 🐛 Sorun Giderme

### Yaygın Sorunlar

#### Authentication Hatası
```
✅ EPIAS kullanıcı bilgilerini kontrol edin
✅ İnternet bağlantısını kontrol edin
✅ EPIAS sisteminin çalıştığını doğrulayın
```

#### Veri Çekme Hatası
```
✅ Tarih formatını kontrol edin (YYYY-MM-DD)
✅ Tarih aralığının makul olduğunu kontrol edin
✅ Chunk boyutunu azaltmayı deneyin
```

#### Dosya İndirme Sorunu
```
✅ İşlemin tamamlandığını kontrol edin
✅ Tarayıcı indirme izinlerini kontrol edin
✅ Disk alanını kontrol edin
```

### Debug Modu
```bash
export FLASK_ENV=development
export LOG_LEVEL=DEBUG
python backend/app.py
```

## 🤝 Katkıda Bulunma

1. Fork edin
2. Feature branch oluşturun (`git checkout -b feature/amazing-feature`)
3. Commit edin (`git commit -m 'Add amazing feature'`)
4. Push edin (`git push origin feature/amazing-feature`)
5. Pull Request oluşturun

## 📝 Lisans

Bu proje MIT lisansı altında lisanslanmıştır. Detaylar için `LICENSE` dosyasına bakınız.

## 🆘 Destek

- **Issues**: GitHub Issues kullanın
- **Email**: support@example.com
- **Docs**: Kapsamlı API dokümantasyonu için `/api` endpoint'ini ziyaret edin

## 🔄 Güncellemeler

### v1.0.0 (Current)
- ✅ Modern web arayüzü
- ✅ EPIAS API entegrasyonu
- ✅ Excel export
- ✅ Docker support
- ✅ Real-time progress tracking

### Gelecek Sürümler
- 📊 Data visualization charts
- 🔔 Email notifications
- 📱 Mobile app
- 🤖 Scheduled data extraction

---

**Not**: Bu uygulama EPIAS'ın resmi bir uygulaması değildir. Üçüncü taraf bir araçtır. 