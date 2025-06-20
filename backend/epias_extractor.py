#!/usr/bin/env python3
"""
EPIAS Elektrik Verisi Çekici - Backend API için refactor edilmiş
"""

import requests
import pandas as pd
from datetime import datetime, timedelta
import json
import time
import os
import logging
from typing import List, Dict, Optional, Tuple

class EpiasExtractor:
    """EPIAS Elektrik Verisi Çekici - API Class"""
    
    def __init__(self, username: str, password: str):
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
        
        # Setup logging
        self.setup_logging()
        
    def setup_logging(self):
        """Logging setup - cloud deployment friendly"""
        handlers = []
        
        # Always add console handler
        handlers.append(logging.StreamHandler())
        
        # Try to add file handler if possible (for local development)
        try:
            # Create logs directory if it doesn't exist
            log_dir = 'backend/logs'
            os.makedirs(log_dir, exist_ok=True)
            
            # Add file handler
            file_handler = logging.FileHandler('backend/logs/epias_api.log', encoding='utf-8')
            handlers.append(file_handler)
        except (OSError, PermissionError):
            # If file logging fails (e.g., in cloud environment), just use console
            pass
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=handlers,
            force=True  # Override any existing logging config
        )
        self.logger = logging.getLogger(__name__)
    
    def authenticate(self) -> Dict[str, any]:
        """EPIAS'a authenticate ol ve TGT token al"""
        try:
            self.logger.info("🔐 EPIAS authentication başlatılıyor...")
            
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
                self.logger.info("✅ Authentication başarılı!")
                
                # Session headers'ına TGT ekle
                self.session.headers.update({
                    'TGT': self.tgt_token
                })
                
                return {
                    'success': True,
                    'message': 'Authentication başarılı',
                    'token_preview': self.tgt_token[:20] + '...' if len(self.tgt_token) > 20 else self.tgt_token
                }
            else:
                self.logger.error(f"❌ Authentication başarısız: {response.status_code}")
                return {
                    'success': False,
                    'message': f'Authentication başarısız: {response.status_code}',
                    'error': response.text
                }
                
        except Exception as e:
            self.logger.error(f"❌ Authentication hatası: {e}")
            return {
                'success': False,
                'message': f'Authentication hatası: {str(e)}'
            }
    
    def get_power_plant_list(self) -> Dict[str, any]:
        """Santral listesini getir"""
        if not self.tgt_token:
            return {
                'success': False,
                'message': 'Authentication gerekli',
                'data': []
            }
        
        try:
            self.logger.info("📋 Santral listesi alınıyor...")
            
            url = f"{self.base_url}/data/injection-quantity-powerplant-list"
            
            response = self.session.get(url, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                # Response structure'ı kontrol et
                if isinstance(data, dict) and 'items' in data:
                    plants = data['items']
                elif isinstance(data, list):
                    plants = data
                else:
                    plants = []
                
                self.logger.info(f"✅ {len(plants)} santral bulundu")
                
                return {
                    'success': True,
                    'message': f'{len(plants)} santral bulundu',
                    'data': plants,
                    'count': len(plants)
                }
            else:
                self.logger.error(f"❌ Santral listesi alınamadı: {response.status_code}")
                return {
                    'success': False,
                    'message': f'Santral listesi alınamadı: {response.status_code}',
                    'data': []
                }
                
        except Exception as e:
            self.logger.error(f"❌ Santral listesi hatası: {e}")
            return {
                'success': False,
                'message': f'Santral listesi hatası: {str(e)}',
                'data': []
            }
    
    def get_uevcb_list(self, organization_id: str) -> List[Dict]:
        """Belirli bir santral için UEVCB listesini getir"""
        if not self.tgt_token:
            return []
        
        try:
            self.logger.info(f"🔍 UEVCB listesi alınıyor - Organization ID: {organization_id}")
            
            url = f"{self.base_url}/data/uevcb-list"
            
            # Request body
            payload = {
                "organizationId": int(organization_id)
            }
            
            self.logger.info(f"🌐 UEVCB API isteği: {url}")
            self.logger.info(f"📦 UEVCB Payload: {payload}")
            
            response = self.session.post(url, json=payload, timeout=30)
            
            self.logger.info(f"📨 UEVCB Response Status: {response.status_code}")
            self.logger.info(f"📨 UEVCB Response Headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                data = response.json()
                self.logger.info(f"📊 UEVCB Raw Response: {data}")
                
                # Response yapısını kontrol et
                if isinstance(data, dict) and 'body' in data and 'content' in data['body']:
                    uevcbs = data['body']['content']
                elif isinstance(data, dict) and 'items' in data:
                    uevcbs = data['items']
                elif isinstance(data, list):
                    uevcbs = data
                else:
                    uevcbs = []
                
                self.logger.info(f"✅ {len(uevcbs)} UEVCB bulundu")
                if uevcbs:
                    self.logger.info(f"🔍 İlk UEVCB örneği: {uevcbs[0]}")
                return uevcbs
            else:
                self.logger.error(f"❌ UEVCB listesi alınamadı: {response.status_code}")
                self.logger.error(f"❌ UEVCB Response Text: {response.text}")
                return []
                
        except Exception as e:
            self.logger.error(f"❌ UEVCB listesi hatası: {e}")
            return []

    def get_injection_quantity_data_export(self, start_date: str, end_date: str, power_plant_id: Optional[str] = None) -> List[Dict]:
        """Try the export endpoint which might give individual plant data"""
        if not self.tgt_token:
            return []
        
        try:
            self.logger.info(f"🔄 Trying EXPORT endpoint for individual plant data...")
            
            url = f"{self.base_url}/export/injection-quantity"
            
            payload = {
                "startDate": start_date,
                "endDate": end_date,
                "format": "JSON"  # Try JSON format instead of XLSX
            }
            
            if power_plant_id:
                payload["powerplantId"] = int(power_plant_id)
                self.logger.info(f"🎯 Export endpoint - powerplantId = {power_plant_id}")
            
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json, text/plain, */*',
                'Origin': 'https://seffaflik.epias.com.tr',
                'Referer': 'https://seffaflik.epias.com.tr/electricity/electricity-generation/ex-post-generation/injection-quantity',
                'TGT': self.tgt_token
            }
            
            self.logger.info(f"🌐 Export API isteği: {url}")
            self.logger.info(f"📦 Export Payload: {payload}")
            
            response = self.session.post(url, json=payload, headers=headers, timeout=60)
            
            self.logger.info(f"📨 Export Response Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                self.logger.info(f"📊 Export Raw Response: {str(data)[:500]}...")
                
                if isinstance(data, dict) and 'content' in data:
                    items = data['content']
                elif isinstance(data, list):
                    items = data
                else:
                    items = []
                
                self.logger.info(f"✅ Export endpoint: {len(items)} kayıt alındı")
                if items:
                    self.logger.info(f"🔍 Export record örneği: {items[0]}")
                    
                return items
            else:
                self.logger.error(f"❌ Export endpoint failed: {response.status_code}")
                self.logger.error(f"❌ Export Response: {response.text}")
                return []
                
        except Exception as e:
            self.logger.error(f"❌ Export endpoint hatası: {e}")
            return []

    def get_injection_quantity_data(self, start_date: str, end_date: str, power_plant_id: Optional[str] = None) -> List[Dict]:
        """Enjeksiyon miktarı verilerini getir - EPIAS website ile aynı format"""
        if not self.tgt_token:
            return []
        
        try:
            self.logger.info(f"📊 Enjeksiyon verileri alınıyor: {start_date} - {end_date}")
            
            # If we have a specific power plant, try export endpoint first
            if power_plant_id:
                self.logger.info(f"🔄 Specific plant requested - trying export endpoint first...")
                export_data = self.get_injection_quantity_data_export(start_date, end_date, power_plant_id)
                if export_data:
                    self.logger.info(f"✅ Export endpoint successful, returning {len(export_data)} records")
                    return export_data
                else:
                    self.logger.warning(f"⚠️ Export endpoint failed, falling back to data endpoint...")
            
            url = f"{self.base_url}/data/injection-quantity"
            
            # Request body - EPIAS website formatı
            payload = {
                "startDate": start_date,
                "endDate": end_date,
                "page": {
                    "number": 1,
                    "size": 24,
                    "sort": {
                        "direction": "ASC",
                        "field": "date"
                    }
                }
            }
            
            # Eğer power_plant_id varsa, powerplantId olarak ekle (lowercase 'p')
            if power_plant_id:
                payload["powerplantId"] = int(power_plant_id)
                self.logger.info(f"🎯 Santral filtreleme: powerplantId = {power_plant_id}")
            else:
                self.logger.info(f"📊 Tüm santraller verisi çekiliyor")
            
            self.logger.info(f"🌐 Injection API isteği: {url}")
            self.logger.info(f"📦 Injection Payload: {payload}")
            
            # Headers - EPIAS website benzeri
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json, text/plain, */*',
                'Origin': 'https://seffaflik.epias.com.tr',
                'Referer': 'https://seffaflik.epias.com.tr/electricity/electricity-generation/ex-post-generation/injection-quantity',
                'TGT': self.tgt_token
            }
            
            response = self.session.post(url, json=payload, headers=headers, timeout=60)
            
            self.logger.info(f"📨 Injection Response Status: {response.status_code}")
            self.logger.info(f"📨 Injection Response Headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                data = response.json()
                self.logger.info(f"📊 Injection Raw Response: {str(data)[:500]}...")
                
                # Response yapısını kontrol et - EPIAS website ile aynı format
                if isinstance(data, dict) and 'items' in data:
                    items = data['items']
                    
                    # Handle pagination like real EPIAS website
                    page_info = data.get('page', {})
                    total_records = page_info.get('total', len(items))
                    current_page = page_info.get('number', 1)
                    page_size = page_info.get('size', len(items))
                    
                    self.logger.info(f"📄 PAGINATION: Page {current_page}, Total records: {total_records}, Page size: {page_size}")
                    
                    # Show totals summary if available (like your real data)
                    if 'totals' in data:
                        totals = data['totals']
                        total_total = totals.get('totalTotal', 0)
                        self.logger.info(f"📊 PERIOD TOTALS: Total energy = {total_total} MWh")
                        
                        # Show active energy types from totals
                        energy_total_fields = ['naturalGasTotal', 'damTotal', 'ligniteTotal', 'riverTotal', 'importedCoalTotal', 
                                             'sunTotal', 'windTotal', 'biomassTotal', 'geothermalTotal', 'fueloilTotal', 
                                             'asphaltiteTotal', 'stoneCoalTotal', 'naphtaTotal', 'lngTotal']
                        active_totals = {k.replace('Total', ''): v for k, v in totals.items() if k in energy_total_fields and v > 0}
                        if active_totals:
                            self.logger.info(f"⚡ ACTIVE ENERGY TYPES (Period totals): {active_totals}")
                    
                    # If there are more pages, collect all data
                    all_items = items.copy()
                    if total_records > len(items):
                        total_pages = (total_records + page_size - 1) // page_size  # Ceiling division
                        self.logger.info(f"📚 MULTI-PAGE DETECTED: {total_records} total records across {total_pages} pages")
                        
                        for page_num in range(2, total_pages + 1):
                            page_payload = payload.copy()
                            page_payload["page"]["number"] = page_num
                            
                            self.logger.info(f"📄 Fetching page {page_num}/{total_pages}...")
                            page_response = self.session.post(url, json=page_payload, headers=headers, timeout=60)
                            
                            if page_response.status_code == 200:
                                page_data = page_response.json()
                                if isinstance(page_data, dict) and 'items' in page_data:
                                    page_items = page_data['items']
                                    all_items.extend(page_items)
                                    self.logger.info(f"📄 Page {page_num}: Added {len(page_items)} records (Total: {len(all_items)})")
                                else:
                                    self.logger.warning(f"⚠️ Page {page_num} unexpected format")
                                    break
                            else:
                                self.logger.error(f"❌ Page {page_num} failed: {page_response.status_code}")
                                break
                        
                        self.logger.info(f"✅ PAGINATION COMPLETE: Collected {len(all_items)} total records")
                    else:
                        self.logger.info(f"📄 SINGLE PAGE: All {len(items)} records fit on one page")
                    
                    items = all_items
                elif isinstance(data, dict) and 'content' in data:
                    # Fallback for old format
                    items = data['content']
                    self.logger.warning(f"⚠️ Using fallback 'content' format")
                elif isinstance(data, list):
                    items = data
                    self.logger.warning(f"⚠️ Direct list format")
                else:
                    items = []
                    self.logger.warning(f"⚠️ Unknown response format: {type(data)}")
                
                self.logger.info(f"✅ {len(items)} kayıt alındı")
                if items:
                    self.logger.info(f"🔍 İlk injection record örneği: {items[0]}")
                    
                    # Detailed analysis of data structure
                    first_record = items[0]
                    self.logger.info(f"🔍 Record keys: {list(first_record.keys())}")
                    
                    # Analyze data structure to understand if this is individual or aggregate data
                    if 'total' in first_record:
                        total_value = first_record.get('total')
                        self.logger.info(f"📊 DATA ANALYSIS: 'total' field found = {total_value}")
                        
                        # Check if this is individual plant data (only one energy type has values) vs aggregate (multiple types)
                        energy_fields = ['naturalGas', 'dam', 'lignite', 'river', 'importedCoal', 'sun', 'wind', 'biomass', 'geothermal', 'fueloil', 'asphaltite', 'stoneCoal', 'naphtha', 'lng']
                        non_zero_fields = [field for field in energy_fields if field in first_record and first_record.get(field, 0) > 0]
                        
                        if len(non_zero_fields) == 0:
                            self.logger.info(f"💤 ZERO PRODUCTION: Plant has no energy production in this time period")
                        elif len(non_zero_fields) == 1:
                            energy_type = non_zero_fields[0]
                            self.logger.info(f"✅ INDIVIDUAL PLANT DATA: Single energy type '{energy_type}' = {first_record.get(energy_type)}")
                            self.logger.info(f"✅ This appears to be individual power plant data (single energy source)")
                        else:
                            self.logger.warning(f"⚠️ MULTIPLE ENERGY TYPES: {non_zero_fields}")
                            if power_plant_id:
                                self.logger.warning(f"⚠️ Requested specific plant {power_plant_id} but got multiple energy types")
                                self.logger.warning(f"⚠️ This might be aggregate data or a multi-source plant")
                            else:
                                self.logger.info(f"📊 Expected: Multiple energy types for aggregate Turkey data")
                        
                        # Show energy breakdown for clarity
                        energy_breakdown = {field: first_record.get(field, 0) for field in energy_fields if field in first_record}
                        non_zero_breakdown = {k: v for k, v in energy_breakdown.items() if v > 0}
                        self.logger.info(f"⚡ ENERGY BREAKDOWN: {non_zero_breakdown}")
                        
                        if power_plant_id:
                            self.logger.info(f"🎯 PLANT {power_plant_id} ANALYSIS: Total={total_value}, Active sources={len(non_zero_fields)}")
                        else:
                            self.logger.info(f"🌍 AGGREGATE DATA ANALYSIS: Total={total_value}, Active sources={len(non_zero_fields)}")
                    
                    if 'powerPlantId' in first_record:
                        plant_id_in_data = first_record.get('powerPlantId')
                        self.logger.info(f"✅ Individual plant data: powerPlantId = {plant_id_in_data}")
                        if power_plant_id and str(plant_id_in_data) != str(power_plant_id):
                            self.logger.warning(f"⚠️ Plant ID mismatch! Requested: {power_plant_id}, Got: {plant_id_in_data}")
                    elif 'organizationId' in first_record:
                        org_id_in_data = first_record.get('organizationId')
                        self.logger.info(f"✅ Individual plant data: organizationId = {org_id_in_data}")
                        if power_plant_id and str(org_id_in_data) != str(power_plant_id):
                            self.logger.warning(f"⚠️ Organization ID mismatch! Requested: {power_plant_id}, Got: {org_id_in_data}")
                    else:
                        self.logger.warning(f"⚠️ No plant identifier found in record - this might be aggregate data")
                        
                    # Show more sample records to understand the pattern
                    if len(items) > 1:
                        self.logger.info(f"🔍 İkinci record örneği: {items[1]}")
                    if len(items) > 2:
                        self.logger.info(f"🔍 Üçüncü record örneği: {items[2]}")
                        
                return items
            else:
                self.logger.error(f"❌ Veri alınamadı: {response.status_code}")
                self.logger.error(f"❌ Response Text: {response.text}")
                return []
                
        except Exception as e:
            self.logger.error(f"❌ Veri alma hatası: {e}")
            return []
    
    def format_date_for_api(self, date_str: str) -> str:
        """Tarihi API formatına çevir (ISO 8601 + timezone)"""
        try:
            # YYYY-MM-DD formatından datetime'a çevir
            dt = datetime.strptime(date_str, '%Y-%m-%d')
            # ISO 8601 formatına çevir (Türkiye timezone +03:00)
            return dt.strftime('%Y-%m-%dT%H:%M:%S+03:00')
        except:
            # Eğer zaten doğru formattaysa, olduğu gibi döndür
            return date_str
    
    def get_data_for_period(self, start_date: str, end_date: str, chunk_days: int = 30, 
                           power_plant_id: Optional[str] = None, progress_callback=None) -> Dict[str, any]:
        """Uzun dönemler için veriyi parçalara bölerek getir"""
        all_data = []
        
        try:
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
                
                # Progress callback
                progress = (processed_days / total_days) * 100 if total_days > 0 else 0
                if progress_callback:
                    progress_callback(progress, current_start.strftime('%Y-%m-%d'), current_end.strftime('%Y-%m-%d'))
                
                self.logger.info(f"📈 İlerleme: %{progress:.1f} - {current_start.strftime('%Y-%m-%d')} - {current_end.strftime('%Y-%m-%d')}")
                
                # Veri çek
                chunk_data = self.get_injection_quantity_data(chunk_start, chunk_end, power_plant_id)
                all_data.extend(chunk_data)
                
                # Sonraki chunk'a geç
                current_start = current_end + timedelta(days=1)
                processed_days = (current_start - datetime.strptime(start_date, "%Y-%m-%d")).days
                
                # API'ye yük bindirmemek için bekle
                time.sleep(1)
            
            self.logger.info(f"🎉 Toplam {len(all_data)} kayıt alındı")
            
            return {
                'success': True,
                'message': f'Toplam {len(all_data)} kayıt alındı',
                'data': all_data,
                'count': len(all_data),
                'period': {
                    'start_date': start_date,
                    'end_date': end_date,
                    'total_days': total_days
                }
            }
            
        except Exception as e:
            self.logger.error(f"❌ Veri çekme hatası: {e}")
            return {
                'success': False,
                'message': f'Veri çekme hatası: {str(e)}',
                'data': [],
                'count': 0
            }
    
    def save_to_excel(self, data: List[Dict], filename: Optional[str] = None, 
                     include_power_plants: bool = True) -> Dict[str, any]:
        """Verileri Excel'e kaydet"""
        if not data:
            return {
                'success': False,
                'message': 'Kaydedilecek veri yok',
                'filepath': None
            }
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"epias_injection_data_{timestamp}.xlsx"
        
        # Output klasörü oluştur
        output_dir = "backend/downloads"
        os.makedirs(output_dir, exist_ok=True)
        filepath = os.path.join(output_dir, filename)
        
        try:
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                # Ana veri
                df = pd.DataFrame(data)
                
                # Tarih sütunlarını düzelt
                date_columns = [col for col in df.columns if 'date' in col.lower() or 'time' in col.lower()]
                for col in date_columns:
                    try:
                        df[col] = pd.to_datetime(df[col])
                        if df[col].dt.tz is not None:
                            df[col] = df[col].dt.tz_localize(None)
                    except Exception as e:
                        self.logger.warning(f"⚠️ {col} sütunu datetime'a çevrilemedi: {e}")
                        pass
                
                df.to_excel(writer, sheet_name='Injection_Data', index=False)
                
                # Santral listesi
                if include_power_plants:
                    try:
                        plants_response = self.get_power_plant_list()
                        if plants_response['success'] and plants_response['data']:
                            df_plants = pd.DataFrame(plants_response['data'])
                            df_plants.to_excel(writer, sheet_name='Power_Plants', index=False)
                    except Exception as e:
                        self.logger.warning(f"⚠️ Santral listesi kaydedilemedi: {e}")
                
                # Özet
                summary_data = self._create_summary(df)
                df_summary = pd.DataFrame(summary_data)
                df_summary.to_excel(writer, sheet_name='Özet', index=False)
                
                # Günlük özet
                if 'date' in df.columns and 'total' in df.columns:
                    try:
                        daily_summary = df.groupby('date')['total'].agg(['sum', 'mean', 'count']).reset_index()
                        daily_summary.columns = ['Tarih', 'Günlük_Toplam_MWh', 'Ortalama_Saatlik_MWh', 'Saat_Sayısı']
                        daily_summary.to_excel(writer, sheet_name='Günlük_Özet', index=False)
                    except Exception as e:
                        self.logger.warning(f"⚠️ Günlük özet oluşturulamadı: {e}")
            
            file_size = os.path.getsize(filepath) / 1024 / 1024  # MB
            self.logger.info(f"🎉 Excel dosyası kaydedildi: {filepath} ({file_size:.2f} MB)")
            
            return {
                'success': True,
                'message': f'Excel dosyası oluşturuldu ({file_size:.2f} MB)',
                'filepath': filepath,
                'filename': filename,
                'file_size_mb': round(file_size, 2),
                'record_count': len(data)
            }
            
        except Exception as e:
            self.logger.error(f"❌ Excel kaydetme hatası: {e}")
            return {
                'success': False,
                'message': f'Excel kaydetme hatası: {str(e)}',
                'filepath': None
            }
    
    def _create_summary(self, df: pd.DataFrame) -> List[Dict]:
        """Özet istatistik oluştur"""
        summary_data = [
            {"Metrik": "Toplam Kayıt", "Değer": len(df)},
            {"Metrik": "Tarih Aralığı", "Değer": f"İlk: {df['date'].min()} - Son: {df['date'].max()}" if 'date' in df.columns else "Bilinmiyor"},
            {"Metrik": "Dosya Oluşturma", "Değer": datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
            {"Metrik": "Kullanıcı", "Değer": self.username}
        ]
        
        # Numerik sütunlar için istatistik
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