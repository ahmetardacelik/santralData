#!/usr/bin/env python3
"""
EPIAS Elektrik Verisi Çekici - Gerçek API'lerle Çalışan Versiyon
"""

import requests
import pandas as pd
from datetime import datetime, timedelta
import json
import time
import os
import logging

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('epias_extractor.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

class EpiasExtractor:
    """EPIAS Elektrik Verisi Çekici"""
    
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.tgt_token = None
        self.session = requests.Session()
        
        # API URLs
        self.auth_url = "https://giris.epias.com.tr/cas/v1/tickets"
        self.base_url = "https://seffaflik.epias.com.tr/electricity-service/v1/generation"
        
        # Headers
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })
        
    def authenticate(self):
        """EPIAS'a authenticate ol ve TGT token al"""
        try:
            logging.info("🔐 EPIAS authentication başlatılıyor...")
            
            # Authentication için headers
            auth_headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'text/plain'
            }
            
            # Authentication data
            auth_data = {
                'username': self.username,
                'password': self.password
            }
            
            response = requests.post(
                self.auth_url, 
                data=auth_data, 
                headers=auth_headers,
                timeout=30
            )
            
            if response.status_code == 201:
                self.tgt_token = response.text.strip()
                logging.info("✅ Authentication başarılı!")
                logging.info(f"   TGT Token alındı (ilk 20 karakter): {self.tgt_token[:20]}...")
                
                # Session headers'ına TGT ekle
                self.session.headers.update({
                    'TGT': self.tgt_token
                })
                return True
            else:
                logging.error(f"❌ Authentication başarısız: {response.status_code}")
                logging.error(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            logging.error(f"❌ Authentication hatası: {e}")
            return False
    
    def get_power_plant_list(self):
        """Santral listesini getir"""
        if not self.tgt_token:
            logging.error("❌ TGT token yok. Önce authenticate() çalıştırın.")
            return []
        
        try:
            logging.info("📋 Santral listesi alınıyor...")
            
            url = f"{self.base_url}/data/injection-quantity-powerplant-list"
            
            response = self.session.get(url, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                # Debug: Response yapısını logla
                logging.info(f"   📊 Response keys: {list(data.keys()) if isinstance(data, dict) else 'List'}")
                
                # Response structure'ı kontrol et - Debug sonuçlarına göre 'items' key'i var
                if isinstance(data, dict) and 'items' in data:
                    plants = data['items']
                elif isinstance(data, list):
                    plants = data
                else:
                    plants = []
                
                logging.info(f"✅ {len(plants)} santral bulundu")
                return plants
            else:
                logging.error(f"❌ Santral listesi alınamadı: {response.status_code}")
                logging.error(f"   Response: {response.text[:200]}...")
                return []
                
        except Exception as e:
            logging.error(f"❌ Santral listesi hatası: {e}")
            return []
    
    def get_injection_quantity_data(self, start_date, end_date, power_plant_id=None):
        """Enjeksiyon miktarı verilerini getir"""
        if not self.tgt_token:
            logging.error("❌ TGT token yok. Önce authenticate() çalıştırın.")
            return []
        
        try:
            logging.info(f"📊 Enjeksiyon verileri alınıyor: {start_date} - {end_date}")
            
            url = f"{self.base_url}/data/injection-quantity"
            
            # Request body
            payload = {
                "startDate": start_date,
                "endDate": end_date
            }
            
            if power_plant_id:
                payload["powerPlantId"] = power_plant_id
            
            response = self.session.post(url, json=payload, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                
                # Debug: Response yapısını logla
                logging.info(f"   📊 Response keys: {list(data.keys()) if isinstance(data, dict) else 'List'}")
                
                # Debug sonuçlarına göre direkt 'items' key'i var
                if isinstance(data, dict) and 'items' in data:
                    items = data['items']
                    
                    # Totals bilgisi varsa logla
                    if 'totals' in data:
                        totals = data['totals']
                        logging.info(f"   📈 Totals bilgisi: {totals}")
                    
                    # Page bilgisi varsa logla
                    if 'page' in data:
                        page = data['page']
                        logging.info(f"   📄 Page bilgisi: {page}")
                        
                elif isinstance(data, list):
                    items = data
                else:
                    items = []
                
                logging.info(f"✅ {len(items)} kayıt alındı")
                
                # Eğer items boşsa, debug için response'u logla
                if len(items) == 0:
                    logging.warning(f"⚠️ Boş response. Tam response: {data}")
                else:
                    # İlk kaydın keys'lerini logla
                    if len(items) > 0:
                        logging.info(f"   📋 İlk kayıt keys: {list(items[0].keys())}")
                
                return items
            else:
                logging.error(f"❌ Veri alınamadı: {response.status_code}")
                logging.error(f"   Response: {response.text[:200]}...")
                return []
                
        except Exception as e:
            logging.error(f"❌ Veri alma hatası: {e}")
            return []
    
    def format_date_for_api(self, date_str):
        """Tarihi API formatına çevir (ISO 8601 + timezone)"""
        try:
            # YYYY-MM-DD formatından datetime'a çevir
            dt = datetime.strptime(date_str, '%Y-%m-%d')
            # ISO 8601 formatına çevir (Türkiye timezone +03:00)
            return dt.strftime('%Y-%m-%dT%H:%M:%S+03:00')
        except:
            # Eğer zaten doğru formattaysa, olduğu gibi döndür
            return date_str
    
    def get_data_for_period(self, start_date, end_date, chunk_days=30, power_plant_id=None):
        """Uzun dönemler için veriyi parçalara bölerek getir"""
        all_data = []
        
        # String tarihlerini datetime'a çevir
        current_start = datetime.strptime(start_date, "%Y-%m-%d")
        final_end = datetime.strptime(end_date, "%Y-%m-%d")
        
        total_days = (final_end - current_start).days
        processed_days = 0
        
        while current_start < final_end:
            # Chunk hesapla
            current_end = current_start + timedelta(days=chunk_days)
            if current_end > final_end:
                current_end = final_end
            
            # API formatına çevir
            chunk_start = self.format_date_for_api(current_start.strftime('%Y-%m-%d'))
            chunk_end = self.format_date_for_api(current_end.strftime('%Y-%m-%d'))
            
            # Progress göster
            progress = (processed_days / total_days) * 100 if total_days > 0 else 0
            logging.info(f"📈 İlerleme: %{progress:.1f} - {current_start.strftime('%Y-%m-%d')} - {current_end.strftime('%Y-%m-%d')}")
            
            # Veri çek
            chunk_data = self.get_injection_quantity_data(chunk_start, chunk_end, power_plant_id)
            all_data.extend(chunk_data)
            
            # Sonraki chunk'a geç
            current_start = current_end + timedelta(days=1)
            processed_days = (current_start - datetime.strptime(start_date, "%Y-%m-%d")).days
            
            # API'ye yük bindirmemek için bekle
            time.sleep(1)
        
        logging.info(f"🎉 Toplam {len(all_data)} kayıt alındı")
        return all_data
    
    def save_to_excel(self, data, filename=None, include_power_plants=True):
        """Verileri Excel'e kaydet"""
        if not data:
            logging.warning("⚠️ Kaydedilecek veri yok")
            return None
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"epias_injection_data_{timestamp}.xlsx"
        
        # Output klasörü oluştur
        output_dir = "output"
        os.makedirs(output_dir, exist_ok=True)
        filepath = os.path.join(output_dir, filename)
        
        try:
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                # Ana veri
                df = pd.DataFrame(data)
                
                # Tarih sütunlarını düzelt (timezone sorununu çöz)
                date_columns = [col for col in df.columns if 'date' in col.lower() or 'time' in col.lower()]
                for col in date_columns:
                    try:
                        # Pandas datetime'a çevir
                        df[col] = pd.to_datetime(df[col])
                        # Timezone varsa kaldır (Excel için)
                        if df[col].dt.tz is not None:
                            df[col] = df[col].dt.tz_localize(None)
                    except Exception as e:
                        logging.warning(f"⚠️ {col} sütunu datetime'a çevrilemedi: {e}")
                        pass
                
                df.to_excel(writer, sheet_name='Injection_Data', index=False)
                logging.info(f"✅ Ana veri kaydedildi: {len(df)} kayıt")
                
                # Santral listesi
                if include_power_plants:
                    try:
                        plants = self.get_power_plant_list()
                        if plants:
                            df_plants = pd.DataFrame(plants)
                            df_plants.to_excel(writer, sheet_name='Power_Plants', index=False)
                            logging.info(f"✅ Santral listesi kaydedildi: {len(df_plants)} santral")
                    except Exception as e:
                        logging.warning(f"⚠️ Santral listesi kaydedilemedi: {e}")
                
                # Özet
                summary_data = [
                    {"Metrik": "Toplam Kayıt", "Değer": len(df)},
                    {"Metrik": "Tarih Aralığı", "Değer": f"İlk: {df['date'].min()} - Son: {df['date'].max()}" if 'date' in df.columns else "Bilinmiyor"},
                    {"Metrik": "Dosya Oluşturma", "Değer": datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
                    {"Metrik": "Kullanıcı", "Değer": self.username}
                ]
                
                # Numerik sütunlar için istatistik
                numeric_cols = df.select_dtypes(include=['number']).columns
                if len(numeric_cols) > 0:
                    # Toplam üretim istatistikleri
                    if 'total' in df.columns:
                        summary_data.extend([
                            {"Metrik": "Toplam Üretim (MWh)", "Değer": f"{df['total'].sum():,.2f}"},
                            {"Metrik": "Ortalama Saatlik Üretim (MWh)", "Değer": f"{df['total'].mean():,.2f}"},
                            {"Metrik": "Maksimum Saatlik Üretim (MWh)", "Değer": f"{df['total'].max():,.2f}"},
                            {"Metrik": "Minimum Saatlik Üretim (MWh)", "Değer": f"{df['total'].min():,.2f}"}
                        ])
                    
                    # Enerji kaynakları toplamları
                    energy_sources = ['naturalGas', 'dam', 'lignite', 'river', 'importedCoal', 'sun', 'wind', 'geothermal']
                    for source in energy_sources:
                        if source in df.columns:
                            total_source = df[source].sum()
                            if total_source > 0:
                                summary_data.append({
                                    "Metrik": f"{source.title()} Toplam (MWh)", 
                                    "Değer": f"{total_source:,.2f}"
                                })
                
                df_summary = pd.DataFrame(summary_data)
                df_summary.to_excel(writer, sheet_name='Özet', index=False)
                
                # Günlük özet (eğer veri varsa)
                if 'date' in df.columns and 'total' in df.columns:
                    try:
                        daily_summary = df.groupby('date')['total'].agg(['sum', 'mean', 'count']).reset_index()
                        daily_summary.columns = ['Tarih', 'Günlük_Toplam_MWh', 'Ortalama_Saatlik_MWh', 'Saat_Sayısı']
                        daily_summary.to_excel(writer, sheet_name='Günlük_Özet', index=False)
                        logging.info(f"✅ Günlük özet kaydedildi: {len(daily_summary)} gün")
                    except Exception as e:
                        logging.warning(f"⚠️ Günlük özet oluşturulamadı: {e}")
            
            logging.info(f"🎉 Excel dosyası kaydedildi: {filepath}")
            
            # Dosya boyutu
            file_size = os.path.getsize(filepath) / 1024 / 1024  # MB
            logging.info(f"💾 Dosya boyutu: {file_size:.2f} MB")
            
            return filepath
            
        except Exception as e:
            logging.error(f"❌ Excel kaydetme hatası: {e}")
            return None

def main():
    """Ana program"""
    print("🚀 EPIAS Elektrik Verisi Çekici")
    print("=" * 50)
    
    # Kullanıcı bilgileri
    username = "celikahmetarda30@gmail.com"
    password = input("🔒 EPIAS Şifreniz: ").strip()
    
    if not password:
        print("❌ Şifre gerekli!")
        return
    
    # Extractor oluştur
    extractor = EpiasExtractor(username, password)
    
    # Authentication
    if not extractor.authenticate():
        print("❌ Authentication başarısız!")
        return
    
    # Menü
    print("\n📅 Tarih Aralığı Seçin:")
    print("1. Son 3 gün (test için)")
    print("2. Son 7 gün")
    print("3. Son 15 gün") 
    print("4. Mayıs 2025 (1-10 Mayıs - test)")
    print("5. Özel tarih aralığı")
    
    choice = input("Seçiminiz (1-5): ").strip()
    
    today = datetime.now()
    
    if choice == "1":
        start_date = (today - timedelta(days=3)).strftime('%Y-%m-%d')
        end_date = today.strftime('%Y-%m-%d')
        period_name = "son_3_gun"
    elif choice == "2":
        start_date = (today - timedelta(days=7)).strftime('%Y-%m-%d')
        end_date = today.strftime('%Y-%m-%d')
        period_name = "son_7_gun"
    elif choice == "3":
        start_date = (today - timedelta(days=15)).strftime('%Y-%m-%d')
        end_date = today.strftime('%Y-%m-%d')
        period_name = "son_15_gun"
    elif choice == "4":
        start_date = "2025-05-01"
        end_date = "2025-05-10"  # Daha kısa test için
        period_name = "mayis_test"
    else:
        start_date = input("📅 Başlangıç tarihi (YYYY-MM-DD): ").strip()
        end_date = input("📅 Bitiş tarihi (YYYY-MM-DD): ").strip()
        period_name = "ozel_tarih"
    
    print(f"\n📊 Seçilen tarih aralığı: {start_date} - {end_date}")
    
    # Santral seçimi
    print("\n🏭 Santral Seçimi:")
    print("1. Tüm santraller")
    print("2. Belirli bir santral")
    
    plant_choice = input("Seçiminiz (1-2): ").strip()
    power_plant_id = None
    
    if plant_choice == "2":
        # Santral listesini göster
        plants = extractor.get_power_plant_list()
        if plants:
            print("\n📋 İlk 10 santral:")
            for i, plant in enumerate(plants[:10]):
                plant_name = plant.get('name', plant.get('shortName', 'Bilinmiyor'))
                plant_id = plant.get('id', plant.get('powerPlantId', 'N/A'))
                print(f"   {i+1}. {plant_name} (ID: {plant_id})")
            
            plant_id_input = input("\n🔢 Santral ID girin: ").strip()
            if plant_id_input:
                power_plant_id = plant_id_input
    
    # Veri çekme
    print(f"\n🔄 Veri çekme başlatılıyor...")
    
    try:
        # Daha kısa chunk ile test
        chunk_days = 7 if choice in ["1", "2"] else 15
        
        data = extractor.get_data_for_period(
            start_date, 
            end_date, 
            chunk_days=chunk_days,
            power_plant_id=power_plant_id
        )
        
        if data:
            # Excel'e kaydet
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"epias_{period_name}_{timestamp}.xlsx"
            
            filepath = extractor.save_to_excel(data, filename, include_power_plants=True)
            
            if filepath:
                print(f"\n🎉 İşlem tamamlandı!")
                print(f"📁 Dosya: {filepath}")
                print(f"📊 Toplam kayıt: {len(data)}")
                
                # İlk birkaç kayıt göster
                if len(data) > 0:
                    print(f"\n🔍 İlk kayıt örneği:")
                    first_record = data[0]
                    for key, value in list(first_record.items())[:5]:
                        print(f"   {key}: {value}")
                    
                    # Dosya boyutu
                    file_size = os.path.getsize(filepath) / 1024 / 1024
                    print(f"💾 Dosya boyutu: {file_size:.2f} MB")
            else:
                print("❌ Excel kaydetme başarısız!")
        else:
            print("❌ Veri alınamadı!")
            print("\n🔧 Olası nedenler:")
            print("   - Seçilen tarih aralığında veri yok")
            print("   - API geçici olarak veri dönmüyor")
            print("   - Tarih formatı sorunu")
            
            # Debug için tek API çağrısı yapalım
            print("\n🔍 Debug: Tek tarih testi...")
            test_start = extractor.format_date_for_api(start_date)
            test_end = extractor.format_date_for_api(start_date)  # Aynı gün
            
            debug_data = extractor.get_injection_quantity_data(test_start, test_end)
            print(f"   Debug sonucu: {len(debug_data)} kayıt")
            
    except Exception as e:
        logging.error(f"❌ Genel hata: {e}")
        print(f"❌ Hata oluştu: {e}")

if __name__ == "__main__":
    main()