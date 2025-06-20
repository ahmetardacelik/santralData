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

# Store import status for later display
backend_import_success = False
backend_import_error = None

try:
    from backend.epias_extractor import EpiasExtractor
    backend_import_success = True
except ImportError as e:
    backend_import_error = e

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

# Custom CSS - Clean and professional styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
        padding: 2rem 3rem;
        border-radius: 12px;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    
    .main-title {
        font-size: 2.5rem !important;
        font-weight: 700 !important;
        margin-bottom: 0.5rem !important;
        text-align: center;
    }
    
    .main-subtitle {
        font-size: 1.1rem !important;
        opacity: 0.9;
        text-align: center;
        margin-bottom: 1rem !important;
    }
    
    .version-info {
        background: rgba(255,255,255,0.1);
        padding: 8px 16px;
        border-radius: 20px;
        font-size: 0.9rem;
        text-align: center;
        border: 1px solid rgba(255,255,255,0.2);
    }
    .status-success {
        background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%);
        border: 1px solid #10b981;
        color: #064e3b;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        font-weight: 500;
    }
    .status-error {
        background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%);
        border: 1px solid #ef4444;
        color: #7f1d1d;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        font-weight: 500;
    }
    .status-warning {
        background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
        border: 1px solid #f59e0b;
        color: #78350f;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        font-weight: 500;
    }
    .connection-indicator {
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 8px 16px;
        border-radius: 20px;
        font-size: 13px;
        z-index: 999;
        font-weight: 600;
        box-shadow: 0 2px 8px rgba(0,0,0,0.15);
    }
    .connected {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: white;
    }
    .disconnected {
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
        color: white;
    }
    .progress-container {
        margin: 1.5rem 0;
        padding: 1.5rem;
        background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .stProgress > div > div > div > div {
        background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
    }
    
    /* Form styling */
    .stForm {
        background: white;
        padding: 2rem;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# Connection status indicator
connection_class = "connected" if st.session_state.connection_status == "connected" else "disconnected"
st.markdown(f"""
<div class="connection-indicator {connection_class}">
    {"● Bağlı" if st.session_state.connection_status == "connected" else "● Bağlantı Kesildi"}
</div>
""", unsafe_allow_html=True)

# Clean Professional Header
st.markdown("""
<div class="main-header">
    <h1 class="main-title">EPIAS Elektrik Verisi Çekici</h1>
    <p class="main-subtitle">Türkiye Elektrik Piyasası Şeffaflık Platformu - Enjeksiyon Miktarı Verileri</p>
    <div class="version-info">
        Version 2.1 - Updated: 2025-06-19 23:15 UTC
    </div>
</div>
""", unsafe_allow_html=True)

# Display backend import status
if backend_import_success:
    st.success("Backend modülü başarıyla yüklendi")
else:
    st.error(f"Backend modülü yüklenemedi: {backend_import_error}")
    st.error("Backend klasörünü ve epias_extractor.py dosyasını kontrol edin")
    st.stop()

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
        
        # Data is already filtered by UEVCB in backend, just validate and display info
        final_data = progress_info['all_data']
        
        # Display debug info about the received data
        display_data_info(final_data, power_plant_id, power_plant_name)
        
        # Even if filtered data is empty, allow the process to complete
        # This matches EPIAS website behavior where you can still see results
        if len(final_data) == 0 and power_plant_id:
            st.info("📋 Boş sonuç seti tamamlandı - Excel dosyası oluşturulabilir")
        
        return final_data
    else:
        status_text.text(f"⏸️ İşlem durdu: {len(progress_info['completed_chunks'])}/{progress_info['total_chunks']} chunk tamamlandı")
        st.warning("İşlem yarıda kaldı. 'Devam Et' butonuna basarak kaldığı yerden devam edebilirsiniz.")
        return None

def display_data_info(data, power_plant_id, power_plant_name):
    """
    Display information about the received data
    Data is already filtered by UEVCB in backend, so this just shows what we got
    """
    if not data:
        if power_plant_id:
            st.warning(f"⚠️ Seçili santral için veri bulunamadı!")
            st.info("💡 Bu durum şu sebeplerden olabilir:")
            st.info("   • Santral bu dönemde hiç elektrik üretmemiş")
            st.info("   • Santral için UEVCB bulunamadı")
            st.info("   • API servisi geçici olarak erişilemez durumda")
            st.info("📋 Yine de Excel dosyası oluşturabilirsiniz (açıklama ile)")
        return
    
    # Debug: Show data structure for the first few records
    if data and len(data) > 0:
        st.info(f"🔍 Debug: Toplam {len(data)} kayıt geldi API'den")
        st.info(f"🔍 Debug: İlk kayıt yapısı - {list(data[0].keys())}")
        
        # Show a few sample records to understand the structure
        for i, record in enumerate(data[:3]):
            st.info(f"🔍 Debug Record {i+1}: {str(record)[:300]}...")
    
    if power_plant_id:
        st.success(f"✅ Santral filtreleme başarılı: {len(data)} kayıt")
        st.info(f"🏭 Santral: {power_plant_name} (ID: {power_plant_id})")
        st.info("💡 EPIAS website ile aynı API formatı kullanıldı - powerplantId parametresi")
    else:
        st.info(f"📊 Tüm santraller verisi: {len(data)} kayıt")

# Authentication Section
if not st.session_state.authenticated:
    st.header("EPIAS Giriş")
    
    with st.form("login_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            username = st.text_input("Kullanıcı Adı", placeholder="EPIAS kullanıcı adınız")
        
        with col2:
            password = st.text_input("Şifre", type="password", placeholder="EPIAS şifreniz")
        
        login_button = st.form_submit_button("Giriş Yap", use_container_width=True)
        
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
    st.subheader("Veri Çekme")
    
    # Santral seçimi - OUTSIDE the form so it appears immediately
    st.subheader("Santral Seçimi (İsteğe Bağlı)")
    
    use_specific_plants = st.checkbox("Belirli santrallar için veri çek")
    power_plant_id = None
    
    if use_specific_plants:
        # Santral arama input'unu hemen göster
        st.markdown("**İpucu:** 2496 santral arasından seçim yapmak için santral adını arayın!")
        
        # Hızlı arama için popüler santral tipleri
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Termik Santraller", help="Termik santralları filtrele"):
                search_term = "termik"
            else:
                search_term = st.text_input(
                    "Santral Ara", 
                    placeholder="Örnek: Akenerji, Soma, Çatalağzı, vb...",
                    help="Santral adının bir bölümünü yazın. Büyük/küçük harf duyarlı değil."
                )
        with col2:
            if st.button("Rüzgar Santralleri", help="Rüzgar santralları filtrele"):
                search_term = "rüzgar"
            elif st.button("Güneş Santralleri", help="Güneş santralları filtrele"):
                search_term = "güneş"
            elif st.button("Hidroelektrik", help="Hidroelektrik santralları filtrele"):
                search_term = "hidro"
        
        # Power plants'i yükle - UI blocking olmadan
        power_plants = get_cached_power_plants()
        
        if power_plants is not None and len(power_plants) > 0:
            # Filtreleme - Tüm santralleri göster
            if search_term:
                filtered_plants = [p for p in power_plants if search_term.lower() in p.get('name', '').lower()]
                st.info(f"Arama sonucu: {len(filtered_plants)} santral bulundu")
            else:
                filtered_plants = power_plants  # Tüm santralleri göster
                st.info(f"Toplam {len(filtered_plants)} santral mevcut (Arama yaparak filtreleyebilirsiniz)")
            
            if filtered_plants:
                # Eğer çok fazla santral varsa kullanıcıyı uyar
                if len(filtered_plants) > 100 and not search_term:
                    st.warning("Çok fazla santral var! Daha hızlı seçim için santral adı arayarak filtreleyebilirsiniz.")
                
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
            st.warning("Santral listesi yükleniyor... Bağlantı problemi varsa bir süre bekleyin.")
            if st.button("Santral Listesini Yenile", key="reload_plants"):
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
                "Başlangıç Tarihi",
                value=date.today() - timedelta(days=30),
                max_value=date.today()
            )
        
        with col2:
            end_date = st.date_input(
                "Bitiş Tarihi",
                value=date.today() - timedelta(days=1),
                max_value=date.today()
            )
        
        extract_button = st.form_submit_button("Veri Çekmeyi Başlat", use_container_width=True)
        
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
                        
                        if final_data is not None:
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