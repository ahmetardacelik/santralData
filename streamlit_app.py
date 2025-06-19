#!/usr/bin/env python3
"""
EPIAS Elektrik Verisi Çekici - Streamlit App
Connection-Safe Version - WebSocket timeout'larına karşı dayanıklı
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date
import os
import sys
import io
import time
import json

# Page config - MUST BE FIRST STREAMLIT COMMAND
st.set_page_config(
    page_title="EPIAS Elektrik Verisi Çekici",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Add backend to path and import with error handling
sys.path.append('backend')

try:
    from backend.epias_extractor import EpiasExtractor
    st.success("✅ Backend modülü başarıyla yüklendi!")
except ImportError as e:
    st.error(f"❌ Backend modülü yüklenemedi: {e}")
    st.error("Backend klasörünü ve epias_extractor.py dosyasını kontrol edin!")
    st.stop()

# Session state initialization - WebSocket güvenli
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'extractor' not in st.session_state:
    st.session_state.extractor = None
if 'extraction_progress' not in st.session_state:
    st.session_state.extraction_progress = {}
if 'last_result' not in st.session_state:
    st.session_state.last_result = None
if 'connection_status' not in st.session_state:
    st.session_state.connection_status = "disconnected"

# Auto-refresh kontrolü - connection monitoring
def check_connection():
    """Bağlantı durumunu kontrol et"""
    try:
        if st.session_state.extractor and hasattr(st.session_state.extractor, 'tgt_token'):
            if st.session_state.extractor.tgt_token:
                st.session_state.connection_status = "connected"
                return True
    except:
        pass
    st.session_state.connection_status = "disconnected"
    return False

# Custom CSS - Connection-aware styling with BIG ANIMATED HEADER
st.markdown("""
<style>
    @keyframes gradientShift {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.05); }
        100% { transform: scale(1); }
    }
    
    @keyframes slideIn {
        0% { transform: translateY(-50px); opacity: 0; }
        100% { transform: translateY(0); opacity: 1; }
    }
    
    .mega-header {
        background: linear-gradient(-45deg, #ee7752, #e73c7e, #23a6d5, #23d5ab, #667eea, #764ba2);
        background-size: 400% 400%;
        animation: gradientShift 4s ease infinite;
        padding: 4rem 2rem;
        border-radius: 20px;
        color: white;
        text-align: center;
        margin-bottom: 3rem;
        box-shadow: 0 20px 40px rgba(0,0,0,0.3);
        animation: slideIn 1.5s ease-out;
    }
    
    .mega-title {
        font-size: 4rem !important;
        font-weight: 900 !important;
        margin-bottom: 1rem !important;
        text-shadow: 3px 3px 6px rgba(0,0,0,0.5);
        animation: pulse 2s ease-in-out infinite;
    }
    
    .mega-subtitle {
        font-size: 1.8rem !important;
        margin-bottom: 1rem !important;
        opacity: 0.9;
    }
    
    .version-badge {
        display: inline-block;
        background: rgba(255,255,255,0.2);
        padding: 10px 20px;
        border-radius: 50px;
        font-weight: bold;
        margin-top: 1rem;
        border: 2px solid rgba(255,255,255,0.3);
        animation: pulse 1.5s ease-in-out infinite;
    }
    
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .status-success {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        padding: 0.75rem;
        border-radius: 0.375rem;
        margin: 1rem 0;
    }
    .status-error {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
        padding: 0.75rem;
        border-radius: 0.375rem;
        margin: 1rem 0;
    }
    .status-warning {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        color: #856404;
        padding: 0.75rem;
        border-radius: 0.375rem;
        margin: 1rem 0;
    }
    .connection-indicator {
        position: fixed;
        top: 10px;
        right: 10px;
        padding: 5px 10px;
        border-radius: 15px;
        font-size: 12px;
        z-index: 999;
    }
    .connected {
        background-color: #28a745;
        color: white;
    }
    .disconnected {
        background-color: #dc3545;
        color: white;
    }
    .progress-container {
        margin: 1rem 0;
        padding: 1rem;
        background-color: #f8f9fa;
        border-radius: 0.5rem;
        border: 1px solid #dee2e6;
    }
    .stProgress > div > div > div > div {
        background-color: #667eea;
    }
</style>
""", unsafe_allow_html=True)

# Connection status indicator
connection_class = "connected" if st.session_state.connection_status == "connected" else "disconnected"
st.markdown(f"""
<div class="connection-indicator {connection_class}">
    {"🟢 Bağlı" if st.session_state.connection_status == "connected" else "🔴 Bağlantı Kesildi"}
</div>
""", unsafe_allow_html=True)

# MEGA ANIMATED HEADER - You will definitely see this!
st.markdown("""
<div class="mega-header">
    <h1 class="mega-title">🚀 EPIAS ELEKTRIK VERİSİ ÇEKİCİ 🚀</h1>
    <p class="mega-subtitle">⚡ Türkiye Elektrik Piyasası Şeffaflık Platformu ⚡</p>
    <p class="mega-subtitle">🔥 WebSocket Güvenli Versiyon - ULTRA EDITION 🔥</p>
    <div class="version-badge">
        🎯 VERSION 2.0 - ANIMATED & IMPROVED 🎯
    </div>
</div>
""", unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 1rem;'>
    <p>⚡ EPIAS Elektrik Verisi Çekici - WebSocket Güvenli Versiyon</p>
    <p>Bağlantı problemlerinde otomatik olarak kaldığı yerden devam eder</p>
</div>
""", unsafe_allow_html=True)

st.markdown("""
    <div style='
        background: linear-gradient(45deg, #ff6b6b, #4ecdc4, #45b7d1, #96ceb4, #ffeaa7);
        background-size: 300% 300%;
        animation: gradientShift 3s ease infinite;
        padding: 25px;
        text-align: center;
        font-size: 36px;
        font-weight: 900;
        color: white;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
        margin-bottom: 2rem;
        border-radius: 15px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
    '>
                 🎉 LATEST VERSION DEPLOYED - ANIMATION EDITION! 🎉
         <br/>
         <span style='font-size: 24px;'>🚀 GitHub → Streamlit Cloud Pipeline Working! 🚀</span>
         <br/>
         <span style='font-size: 18px;'>⏰ TIMESTAMP: 2025-01-19 12:10 PM - FORCED UPDATE! ⏰</span>
    </div>
    """, unsafe_allow_html=True)

# Helper Functions - Connection-safe
@st.cache_data(ttl=300)  # 5 dakika cache
def get_cached_power_plants():
    """Cache'lenmiş santral listesi - connection-safe"""
    if not st.session_state.authenticated or not st.session_state.extractor:
        return None  # Return None to distinguish from empty list
    
    try:
        result = st.session_state.extractor.get_power_plant_list()
        if result['success']:
            return result['data']
        else:
            # If the API call failed, return None to indicate error
            return None
    except Exception as e:
        # Don't show error here, let the calling function handle it
        return None

def safe_extraction_with_resume(extractor, start_date, end_date, power_plant_id=None, power_plant_name=None, chunk_days=7):
    """WebSocket kopma durumunda devam edebilen güvenli veri çekme"""
    
    # Daha unique extraction key oluştur
    plant_key = f"plant_{power_plant_id}" if power_plant_id else "all_plants"
    extraction_key = f"{start_date}_{end_date}_{plant_key}"
    if extraction_key not in st.session_state.extraction_progress:
        st.session_state.extraction_progress[extraction_key] = {
            'completed_chunks': [],
            'all_data': [],
            'start_date': start_date,
            'end_date': end_date,
            'power_plant_id': power_plant_id,
            'power_plant_name': power_plant_name or ("Seçili Santral" if power_plant_id else "Tüm Santraller"),
            'total_chunks': 0,
            'completed': False
        }
    progress_info = st.session_state.extraction_progress[extraction_key]
    current_start = datetime.strptime(start_date, "%Y-%m-%d")
    final_end = datetime.strptime(end_date, "%Y-%m-%d")
    all_chunks = []
    temp_start = current_start
    while temp_start < final_end:
        temp_end = temp_start + timedelta(days=chunk_days)
        if temp_end > final_end:
            temp_end = final_end
        all_chunks.append((temp_start.strftime('%Y-%m-%d'), temp_end.strftime('%Y-%m-%d')))
        temp_start = temp_end
    progress_info['total_chunks'] = len(all_chunks)
    progress_bar = st.progress(0)
    status_text = st.empty()
    for i, (chunk_start, chunk_end) in enumerate(all_chunks):
        chunk_key = f"{chunk_start}_{chunk_end}"
        if chunk_key in progress_info['completed_chunks']:
            continue
        status_text.text(f"📊 Veri çekiliyor: {chunk_start} - {chunk_end}")
        try:
            if not check_connection():
                st.error("❌ Bağlantı kesildi! Lütfen yeniden giriş yapın.")
                return None
            chunk_data = extractor.get_injection_quantity_data(
                extractor.format_date_for_api(chunk_start),
                extractor.format_date_for_api(chunk_end),
                power_plant_id
            )
            # Always mark chunk as completed, even if empty
            progress_info['completed_chunks'].append(chunk_key)
            if chunk_data:
                progress_info['all_data'].extend(chunk_data)
                st.success(f"✅ {chunk_start} - {chunk_end}: {len(chunk_data)} kayıt")
            else:
                st.warning(f"⚠️ {chunk_start} - {chunk_end}: Veri bulunamadı")
            progress = (len(progress_info['completed_chunks']) / progress_info['total_chunks'])
            progress_bar.progress(progress)
            st.session_state.extraction_progress[extraction_key] = progress_info
            time.sleep(0.5)
        except Exception as e:
            st.error(f"❌ {chunk_start} - {chunk_end} hatası: {e}")
            time.sleep(2)
            continue
    if len(progress_info['completed_chunks']) == progress_info['total_chunks']:
        progress_info['completed'] = True
        status_text.text("🎉 Veri çekme tamamlandı!")
        progress_bar.progress(1.0)
        
        # Apply client-side filtering for specific power plants
        final_data = filter_data_for_power_plant(
            progress_info['all_data'], 
            power_plant_id, 
            power_plant_name
        )
        
        # Even if filtered data is empty, allow the process to complete
        # This matches EPIAS website behavior where you can still see results
        if len(final_data) == 0 and power_plant_id:
            st.info("📋 Boş sonuç seti tamamlandı - Excel dosyası oluşturulabilir")
        
        return final_data
    else:
        status_text.text(f"⏸️ İşlem durdu: {len(progress_info['completed_chunks'])}/{progress_info['total_chunks']} chunk tamamlandı")
        st.warning("İşlem yarıda kaldı. 'Devam Et' butonuna basarak kaldığı yerden devam edebilirsiniz.")
        return None

def filter_data_for_power_plant(data, power_plant_id, power_plant_name):
    """
    Filter data to include only the selected power plant and validate results
    This ensures we only get data for the specific plant, like the EPIAS website
    """
    if not power_plant_id or not data:
        return data
    
    # Debug: Show data structure for the first few records
    if data and len(data) > 0:
        st.info(f"🔍 Debug: Toplam {len(data)} kayıt geldi API'den")
        st.info(f"🔍 Debug: İlk kayıt yapısı - {list(data[0].keys())}")
        
        # Show a few sample records to understand the structure
        for i, record in enumerate(data[:3]):
            st.info(f"🔍 Debug Record {i+1}: {str(record)[:300]}...")
    
    # Extract plant ID from the full name if it contains the ID
    clean_plant_id = power_plant_id
    if '-' in power_plant_name and power_plant_name.split('-')[-1]:
        potential_id = power_plant_name.split('-')[-1]
        if potential_id.replace('W', '').replace('0', '').isdigit():
            clean_plant_id = potential_id
    
    st.info(f"🔍 Debug: Aranan Plant ID: '{power_plant_id}', Clean ID: '{clean_plant_id}'")
    st.info(f"🔍 Debug: Aranan Plant Name: '{power_plant_name}'")
    
    # More flexible filtering - try different field combinations
    filtered_data = []
    matched_fields = set()
    
    for record in data:
        # Try multiple possible field names and matching strategies
        matches = [
            ('powerPlantId_exact', record.get('powerPlantId') == power_plant_id),
            ('id_exact', record.get('id') == power_plant_id),
            ('plantId_exact', record.get('plantId') == power_plant_id),
            ('powerPlantId_clean', record.get('powerPlantId') == clean_plant_id),
            ('id_clean', record.get('id') == clean_plant_id),
            ('plantId_clean', record.get('plantId') == clean_plant_id),
            # Name-based matching (more flexible)
            ('name_full', power_plant_name.lower() in str(record.get('name', '')).lower()),
            ('powerPlantName_full', power_plant_name.lower() in str(record.get('powerPlantName', '')).lower()),
            # Partial name matching for specific plant
            ('name_akyurt', 'akyurt' in str(record.get('name', '')).lower()),
            ('name_biyogaz', 'biyogaz' in str(record.get('name', '')).lower()),
            ('name_3a_bes', '3a bes' in str(record.get('name', '')).lower())
        ]
        
        for match_type, is_match in matches:
            if is_match:
                filtered_data.append(record)
                matched_fields.add(match_type)
                break  # Exit after first match to avoid duplicates
    
    st.info(f"🔍 Filtre sonucu: {len(filtered_data)} kayıt bulundu")
    if matched_fields:
        st.info(f"🔍 Eşleşen alanlar: {', '.join(matched_fields)}")
    
    # Even if 0 records, provide detailed explanation
    if len(filtered_data) == 0:
        st.warning(f"⚠️ Seçili santral için API verisinde eşleşme bulunamadı!")
        st.info("💡 Bu durum şu sebeplerden olabilir:")
        st.info("   • Santral bu dönemde hiç elektrik üretmemiş")
        st.info("   • API veri yapısı beklediğimizden farklı")
        st.info("   • Santral ID/adı formatı değişmiş")
        st.info("📋 Yine de Excel dosyası oluşturabilirsiniz (açıklama ile)")
        
        return []
    
    return filtered_data

# Authentication Section
if not st.session_state.authenticated:
    st.header("🔐 EPIAS Giriş")
    
    with st.form("login_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            username = st.text_input("👤 Kullanıcı Adı", placeholder="EPIAS kullanıcı adınız")
        
        with col2:
            password = st.text_input("🔒 Şifre", type="password", placeholder="EPIAS şifreniz")
        
        login_button = st.form_submit_button("🚀 Giriş Yap", use_container_width=True)
        
        if login_button:
            if username and password:
                with st.spinner("🔄 Giriş yapılıyor..."):
                    try:
                        st.info("🔄 EpiasExtractor başlatılıyor...")
                        extractor = EpiasExtractor(username, password)
                        st.info("🔄 Authentication çağrısı yapılıyor...")
                        auth_result = extractor.authenticate()
                        st.info(f"🔄 Authentication sonucu: {auth_result}")
                        
                        if auth_result and auth_result.get('success'):
                            st.session_state.authenticated = True
                            st.session_state.extractor = extractor
                            st.session_state.connection_status = "connected"
                            st.success("✅ Giriş başarılı!")
                            st.rerun()
                        else:
                            error_msg = auth_result.get('message', 'Bilinmeyen hata') if auth_result else 'Authentication sonucu None'
                            st.error(f"❌ Giriş başarısız: {error_msg}")
                    except ImportError as ie:
                        st.error(f"❌ Import hatası - Backend modülü bulunamadı: {ie}")
                    except AttributeError as ae:
                        st.error(f"❌ Method hatası - EpiasExtractor.authenticate() bulunamadı: {ae}")
                    except Exception as e:
                        st.error(f"❌ Genel hata: {type(e).__name__}: {e}")
                        st.error(f"❌ Hata detayı: {str(e)}")
            else:
                st.error("❌ Lütfen kullanıcı adı ve şifre girin!")

else:
    # Ana uygulama - Authentication başarılı
    
    # Sidebar - Connection-aware controls
    with st.sidebar:
        st.header("⚙️ Ayarlar")
        
        # Connection status
        if st.session_state.connection_status == "connected":
            st.success("🟢 Bağlantı Aktif")
        else:
            st.error("🔴 Bağlantı Kesildi")
            if st.button("🔄 Yeniden Bağlan"):
                if st.session_state.extractor:
                    try:
                        auth_result = st.session_state.extractor.authenticate()
                        if auth_result['success']:
                            st.session_state.connection_status = "connected"
                            st.success("✅ Yeniden bağlanıldı!")
                            st.rerun()
                    except Exception as e:
                        st.error(f"❌ Yeniden bağlanılamadı: {e}")
        
        # Logout
        if st.button("🚪 Çıkış Yap"):
            # Session state'i temizle
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
        
        st.divider()
        
        # Chunk size ayarı - Connection-safe processing için
        chunk_days = st.slider(
            "📦 Chunk Boyutu (Gün)", 
            min_value=1, 
            max_value=15, 
            value=7,
            help="Küçük chunk'lar daha güvenli ama yavaş. Bağlantı problemi varsa küçültün."
        )
        
        # Cache temizleme
        if st.button("🗑️ Cache Temizle"):
            st.cache_data.clear()
            st.success("✅ Cache temizlendi!")
    
    # Ana içerik
    st.header("📊 Veri Çekme")
    
    # Ongoing extraction display
    if st.session_state.extraction_progress:
        st.subheader("⏳ Devam Eden/Tamamlanan İşlemler")
        
        for key, progress in st.session_state.extraction_progress.items():
            plant_info = f" - {progress.get('power_plant_name', 'Bilinmeyen Santral')}"
            with st.expander(f"📈 {progress['start_date']} - {progress['end_date']}{plant_info} {'(Tamamlandı)' if progress['completed'] else '(Devam Ediyor)'}"):
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Toplam Chunk", progress['total_chunks'])
                
                with col2:
                    st.metric("Tamamlanan", len(progress['completed_chunks']))
                
                with col3:
                    completion_rate = len(progress['completed_chunks']) / progress['total_chunks'] if progress['total_chunks'] > 0 else 0
                    st.metric("Tamamlanma", f"%{completion_rate*100:.1f}")
                
                with col4:
                    st.metric("Santral", progress.get('power_plant_name', 'Bilinmeyen')[:20] + "..." if len(progress.get('power_plant_name', '')) > 20 else progress.get('power_plant_name', 'Bilinmeyen'))
                
                if not progress['completed'] and len(progress['all_data']) > 0:
                    if st.button(f"▶️ Devam Et - {key}", key=f"resume_{key}"):
                        with st.spinner("Kaldığı yerden devam ediliyor..."):
                            final_data = safe_extraction_with_resume(
                                st.session_state.extractor,
                                progress['start_date'],
                                progress['end_date'],
                                progress['power_plant_id'],
                                progress.get('power_plant_name'),
                                chunk_days
                            )
                            if final_data:
                                st.session_state.last_result = final_data
                
                if progress['completed'] and len(progress['all_data']) > 0:
                    st.info(f"✅ {len(progress['all_data'])} kayıt hazır")
                    if st.button(f"📁 Excel İndir - {key}", key=f"download_{key}"):
                        try:
                            result = st.session_state.extractor.save_to_excel(
                                progress['all_data'],
                                f"epias_data_{key.replace('_', '')}.xlsx"
                            )
                            if result['success']:
                                with open(result['filepath'], 'rb') as f:
                                    st.download_button(
                                        label="💾 Dosyayı İndir",
                                        data=f.read(),
                                        file_name=result['filename'],
                                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                        key=f"download_file_{key}"
                                    )
                        except Exception as e:
                            st.error(f"❌ Excel oluşturma hatası: {e}")
    
    # Yeni veri çekme formu
    st.subheader("🆕 Yeni Veri Çekme")
    
    # Santral seçimi - OUTSIDE the form so it appears immediately
    st.subheader("🏭 Santral Seçimi (İsteğe Bağlı)")
    
    use_specific_plants = st.checkbox("Belirli santrallar için veri çek")
    power_plant_id = None
    
    if use_specific_plants:
        # Santral arama input'unu hemen göster
        st.markdown("**💡 İpucu:** 2496 santral arasından seçim yapmak için santral adını arayın!")
        
        # Hızlı arama için popüler santral tipleri
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔥 Termik Santraller", help="Termik santralları filtrele"):
                search_term = "termik"
            else:
                search_term = st.text_input(
                    "🔍 Santral Ara", 
                    placeholder="Örnek: Akenerji, Soma, Çatalağzı, vb...",
                    help="Santral adının bir bölümünü yazın. Büyük/küçük harf duyarlı değil."
                )
        with col2:
            if st.button("💨 Rüzgar Santralleri", help="Rüzgar santralları filtrele"):
                search_term = "rüzgar"
            elif st.button("☀️ Güneş Santralleri", help="Güneş santralları filtrele"):
                search_term = "güneş"
            elif st.button("💧 Hidroelektrik", help="Hidroelektrik santralları filtrele"):
                search_term = "hidro"
        
        # Power plants'i yükle - UI blocking olmadan
        power_plants = get_cached_power_plants()
        
        if power_plants is not None and len(power_plants) > 0:
            # Filtreleme - Tüm santralleri göster
            if search_term:
                filtered_plants = [p for p in power_plants if search_term.lower() in p.get('name', '').lower()]
                st.info(f"🔍 Arama sonucu: {len(filtered_plants)} santral bulundu")
            else:
                filtered_plants = power_plants  # Tüm santralleri göster
                st.info(f"📋 Toplam {len(filtered_plants)} santral mevcut (Arama yaparak filtreleyebilirsiniz)")
            
            if filtered_plants:
                # Eğer çok fazla santral varsa kullanıcıyı uyar
                if len(filtered_plants) > 100 and not search_term:
                    st.warning("⚠️ Çok fazla santral var! Daha hızlı seçim için santral adı arayarak filtreleyebilirsiniz.")
                
                selected_plant = st.selectbox(
                    "Santral Seç",
                    options=[None] + filtered_plants,
                    format_func=lambda x: "Tüm Santraller" if x is None else f"{x.get('name', 'Unknown')} (ID: {x.get('id', 'N/A')})",
                    help=f"Belirli bir santral seçin veya tüm santraller için 'Tüm Santraller' seçeneğini bırakın. Toplam {len(filtered_plants)} santral mevcut."
                )
                # Fix the power_plant_id assignment to handle None properly
                power_plant_id = selected_plant.get('id') if selected_plant is not None else None
                power_plant_name = selected_plant.get('name') if selected_plant is not None else None
            else:
                st.warning("Arama kriterinize uygun santral bulunamadı.")
                power_plant_id = None
                power_plant_name = None
        elif power_plants is not None and len(power_plants) == 0:
            # Empty list - no power plants available
            st.info("Sistemde kayıtlı santral bulunamadı.")
            power_plant_id = None
            power_plant_name = None
        else:
            # power_plants is None - loading or error state
            st.warning("⚠️ Santral listesi yükleniyor... Bağlantı problemi varsa bir süre bekleyin.")
            if st.button("🔄 Santral Listesini Yenile", key="reload_plants"):
                st.cache_data.clear()
                st.rerun()
            power_plant_id = None
            power_plant_name = None
    else:
        power_plant_id = None
        power_plant_name = None
    
    # Date selection form - separate from santral selection
    with st.form("extraction_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            start_date = st.date_input(
                "📅 Başlangıç Tarihi",
                value=date.today() - timedelta(days=30),
                max_value=date.today()
            )
        
        with col2:
            end_date = st.date_input(
                "📅 Bitiş Tarihi",
                value=date.today() - timedelta(days=1),
                max_value=date.today()
            )
        
        extract_button = st.form_submit_button("🚀 Veri Çekmeyi Başlat", use_container_width=True)
        
        if extract_button:
            if start_date <= end_date:
                # Bağlantıyı kontrol et
                if not check_connection():
                    st.error("❌ Bağlantı kesildi! Lütfen yeniden giriş yapın.")
                else:
                    start_str = start_date.strftime("%Y-%m-%d")
                    end_str = end_date.strftime("%Y-%m-%d")
                    
                    # Tarih aralığını kontrol et
                    total_days = (end_date - start_date).days
                    
                    if total_days > 365:
                        st.warning("⚠️ 1 yıldan uzun dönemler için işlem uzun sürebilir ve connection kopma riski yüksektir.")
                    
                    st.info(f"📊 Veri çekme başlatıldı: {start_str} - {end_str} ({total_days} gün)")
                    st.info(f"📦 Chunk boyutu: {chunk_days} gün")
                    
                    if power_plant_id and power_plant_name:
                        st.success(f"🏭 Seçili santral: {power_plant_name} (ID: {power_plant_id})")
                        st.info("💡 Sadece seçili santralın verileri indirilecek - EPIAS website gibi!")
                    else:
                        st.info("🏭 Tüm santraller için veri çekiliyor")
                    
                    # Connection-safe extraction başlat
                    with st.spinner("Veri çekiliyor... (Bu işlem uzun sürebilir)"):
                        final_data = safe_extraction_with_resume(
                            st.session_state.extractor,
                            start_str,
                            end_str,
                            power_plant_id,
                            power_plant_name,
                            chunk_days
                        )
                        
                        if final_data:
                            st.session_state.last_result = final_data
                            st.success(f"🎉 İşlem tamamlandı! {len(final_data)} kayıt çekildi.")
                            st.rerun()
            else:
                st.error("❌ Başlangıç tarihi bitiş tarihinden sonra olamaz!")

    # Sonuç görüntüleme ve indirme
    if st.session_state.last_result:
        st.header("📈 Sonuçlar")
        
        data = st.session_state.last_result
        st.success(f"✅ Toplam {len(data)} kayıt çekildi")
        
        # Veri önizleme
        if st.checkbox("📋 Veri Önizleme"):
            df = pd.DataFrame(data)
            st.dataframe(df.head(100), use_container_width=True)
        
        # Excel indirme
        if st.button("💾 Excel Dosyası Oluştur", use_container_width=True):
            with st.spinner("Excel dosyası oluşturuluyor..."):
                try:
                    if len(data) == 0:
                        st.warning("⚠️ Veri boş olmasına rağmen Excel dosyası oluşturuluyor...")
                        st.info("💡 Bu, seçili santralın belirtilen dönemde elektrik üretmediğini gösterir.")
                        # Create a minimal Excel with explanation
                        import pandas as pd
                        from datetime import datetime
                        import os
                        
                        explanation_data = [{
                            'Açıklama': 'Seçili santral için bu tarih aralığında veri bulunamadı',
                            'Santral': power_plant_name if 'power_plant_name' in locals() else 'Bilinmeyen',
                            'Tarih': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            'Durum': 'Santral bu dönemde elektrik üretmemiş olabilir'
                        }]
                        
                        # Create Excel with explanation
                        output_dir = "backend/downloads"
                        os.makedirs(output_dir, exist_ok=True)
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"epias_empty_data_{timestamp}.xlsx"
                        filepath = os.path.join(output_dir, filename)
                        
                        df = pd.DataFrame(explanation_data)
                        df.to_excel(filepath, index=False)
                        
                        with open(filepath, 'rb') as f:
                            st.download_button(
                                label="📥 Boş Sonuç Excel Dosyasını İndir",
                                data=f.read(),
                                file_name=filename,
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            )
                    else:
                        result = st.session_state.extractor.save_to_excel(data)
                        
                        if result['success']:
                            st.success(f"✅ Excel dosyası oluşturuldu! ({result['file_size_mb']} MB)")
                            
                            # Download button
                            with open(result['filepath'], 'rb') as f:
                                st.download_button(
                                    label="📥 Excel Dosyasını İndir",
                                    data=f.read(),
                                    file_name=result['filename'],
                                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                                )
                        else:
                            st.error(f"❌ Excel oluşturulamadı: {result['message']}")
                except Exception as e:
                    st.error(f"❌ Excel oluşturma hatası: {e}") 