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

# Add backend to path
sys.path.append('backend')

from backend.epias_extractor import EpiasExtractor

# Page config
st.set_page_config(
    page_title="EPIAS Elektrik Verisi Çekici",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

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

# Custom CSS - Connection-aware styling
st.markdown("""
<style>
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

# Main header
st.markdown("""
<div class="main-header">
    <h1>⚡ EPIAS Elektrik Verisi Çekici</h1>
    <p>Türkiye Elektrik Piyasası Şeffaflık Platformu Veri Çekici</p>
    <p><strong>WebSocket Güvenli Versiyon</strong></p>
</div>
""", unsafe_allow_html=True)

# Helper Functions - Connection-safe
@st.cache_data(ttl=300)  # 5 dakika cache
def get_cached_power_plants():
    """Cache'lenmiş santral listesi - connection-safe"""
    if not st.session_state.authenticated or not st.session_state.extractor:
        return []
    
    try:
        result = st.session_state.extractor.get_power_plant_list()
        if result['success']:
            return result['data']
    except Exception as e:
        st.error(f"Santral listesi alınamadı: {e}")
    return []

def safe_extraction_with_resume(extractor, start_date, end_date, power_plant_id=None, chunk_days=7):
    """WebSocket kopma durumunda devam edebilen güvenli veri çekme"""
    
    extraction_key = f"{start_date}_{end_date}_{power_plant_id or 'all'}"
    if extraction_key not in st.session_state.extraction_progress:
        st.session_state.extraction_progress[extraction_key] = {
            'completed_chunks': [],
            'all_data': [],
            'start_date': start_date,
            'end_date': end_date,
            'power_plant_id': power_plant_id,
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
        return progress_info['all_data']
    else:
        status_text.text(f"⏸️ İşlem durdu: {len(progress_info['completed_chunks'])}/{progress_info['total_chunks']} chunk tamamlandı")
        st.warning("İşlem yarıda kaldı. 'Devam Et' butonuna basarak kaldığı yerden devam edebilirsiniz.")
        return None

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
                        extractor = EpiasExtractor(username, password)
                        auth_result = extractor.authenticate()
                        
                        if auth_result['success']:
                            st.session_state.authenticated = True
                            st.session_state.extractor = extractor
                            st.session_state.connection_status = "connected"
                            st.success("✅ Giriş başarılı!")
                            st.rerun()
                        else:
                            st.error(f"❌ Giriş başarısız: {auth_result['message']}")
                    except Exception as e:
                        st.error(f"❌ Bağlantı hatası: {e}")
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
            with st.expander(f"📈 {progress['start_date']} - {progress['end_date']} {'(Tamamlandı)' if progress['completed'] else '(Devam Ediyor)'}"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Toplam Chunk", progress['total_chunks'])
                
                with col2:
                    st.metric("Tamamlanan", len(progress['completed_chunks']))
                
                with col3:
                    completion_rate = len(progress['completed_chunks']) / progress['total_chunks'] if progress['total_chunks'] > 0 else 0
                    st.metric("Tamamlanma", f"%{completion_rate*100:.1f}")
                
                if not progress['completed'] and len(progress['all_data']) > 0:
                    if st.button(f"▶️ Devam Et - {key}", key=f"resume_{key}"):
                        with st.spinner("Kaldığı yerden devam ediliyor..."):
                            final_data = safe_extraction_with_resume(
                                st.session_state.extractor,
                                progress['start_date'],
                                progress['end_date'],
                                progress['power_plant_id'],
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
        
        # Santral seçimi - cached
        st.subheader("🏭 Santral Seçimi (İsteğe Bağlı)")
        
        if st.checkbox("Belirli santrallar için veri çek"):
            with st.spinner("Santral listesi yükleniyor..."):
                power_plants = get_cached_power_plants()
                
                if power_plants:
                    # Santral arama
                    search_term = st.text_input("🔍 Santral Ara", placeholder="Santral adı yazın...")
                    
                    if search_term:
                        filtered_plants = [p for p in power_plants if search_term.lower() in p.get('name', '').lower()]
                    else:
                        filtered_plants = power_plants[:50]  # İlk 50 santral
                    
                    if filtered_plants:
                        selected_plant = st.selectbox(
                            "Santral Seç",
                            options=[None] + filtered_plants,
                            format_func=lambda x: "Tüm Santraller" if x is None else f"{x.get('name', 'Unknown')} (ID: {x.get('id', 'N/A')})"
                        )
                        power_plant_id = selected_plant.get('id') if selected_plant else None
                    else:
                        st.warning("Arama kriterinize uygun santral bulunamadı.")
                        power_plant_id = None
                else:
                    st.error("Santral listesi yüklenemedi.")
                    power_plant_id = None
        else:
            power_plant_id = None
        
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
                    
                    # Connection-safe extraction başlat
                    with st.spinner("Veri çekiliyor... (Bu işlem uzun sürebilir)"):
                        final_data = safe_extraction_with_resume(
                            st.session_state.extractor,
                            start_str,
                            end_str,
                            power_plant_id,
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

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 1rem;'>
    <p>⚡ EPIAS Elektrik Verisi Çekici - WebSocket Güvenli Versiyon</p>
    <p>Bağlantı problemlerinde otomatik olarak kaldığı yerden devam eder</p>
</div>
""", unsafe_allow_html=True) 