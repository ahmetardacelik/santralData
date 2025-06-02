#!/usr/bin/env python3
"""
EPIAS Elektrik Verisi Çekici - Streamlit App
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date
import os
import sys
import io
import time

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

# Custom CSS
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
    .info-box {
        background-color: #e2e3f1;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #667eea;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'extractor' not in st.session_state:
    st.session_state.extractor = None
if 'username' not in st.session_state:
    st.session_state.username = ""

def authenticate_user(username: str, password: str):
    """Authenticate user with EPIAS"""
    try:
        with st.spinner('EPIAS\'a giriş yapılıyor...'):
            extractor = EpiasExtractor(username, password)
            result = extractor.authenticate()
            
            if result['success']:
                st.session_state.authenticated = True
                st.session_state.extractor = extractor
                st.session_state.username = username
                st.success("✅ Giriş başarılı!")
                st.rerun()
            else:
                st.error(f"❌ Giriş hatası: {result['message']}")
                
    except Exception as e:
        st.error(f"❌ Bağlantı hatası: {str(e)}")

def logout():
    """Logout user"""
    st.session_state.authenticated = False
    st.session_state.extractor = None
    st.session_state.username = ""
    st.success("Çıkış yapıldı!")
    st.rerun()

def load_power_plants():
    """Load power plant list"""
    if not st.session_state.extractor:
        return []
    
    try:
        with st.spinner('Santral listesi yükleniyor...'):
            result = st.session_state.extractor.get_power_plant_list()
            
            if result['success']:
                return result['data']
            else:
                st.error(f"Santral listesi yüklenemedi: {result['message']}")
                return []
                
    except Exception as e:
        st.error(f"Santral listesi hatası: {str(e)}")
        return []

def extract_data(start_date: date, end_date: date, power_plant_id: str = None, chunk_days: int = 15):
    """Extract electricity data"""
    if not st.session_state.extractor:
        st.error("Authentication gerekli")
        return None
    
    try:
        # Convert dates to string
        start_str = start_date.strftime('%Y-%m-%d')
        end_str = end_date.strftime('%Y-%m-%d')
        
        # Validate dates
        if start_date >= end_date:
            st.error("Başlangıç tarihi bitiş tarihinden önce olmalı")
            return None
        
        # Calculate total days
        total_days = (end_date - start_date).days
        if total_days > 365:
            st.warning("Çok büyük tarih aralığı. İşlem uzun sürebilir.")
        
        # Progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        def progress_callback(progress, current_start, current_end):
            progress_bar.progress(progress / 100)
            status_text.text(f"İşleniyor: {current_start} - {current_end} ({progress:.1f}%)")
        
        status_text.text("Veri çekme başlatılıyor...")
        
        # Extract data
        result = st.session_state.extractor.get_data_for_period(
            start_str, 
            end_str, 
            chunk_days=chunk_days,
            power_plant_id=power_plant_id if power_plant_id else None,
            progress_callback=progress_callback
        )
        
        progress_bar.progress(100)
        
        if result['success']:
            status_text.text(f"✅ Tamamlandı! {result['count']} kayıt işlendi")
            return result['data']
        else:
            st.error(f"Veri çekme hatası: {result['message']}")
            return None
            
    except Exception as e:
        st.error(f"İşlem hatası: {str(e)}")
        return None

def create_excel_download(data: list, filename: str = None):
    """Create Excel file for download"""
    if not data:
        return None
    
    try:
        # Convert to DataFrame
        df = pd.DataFrame(data)
        
        # Create Excel file in memory
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Main data sheet
            df.to_excel(writer, sheet_name='Elektrik Verileri', index=False)
            
            # Summary sheet
            if not df.empty:
                summary_data = {
                    'Toplam Kayıt': [len(df)],
                    'Tarih Aralığı': [f"{df['date'].min()} - {df['date'].max()}"] if 'date' in df.columns else ['N/A'],
                    'Oluşturma Tarihi': [datetime.now().strftime('%Y-%m-%d %H:%M:%S')]
                }
                summary_df = pd.DataFrame(summary_data)
                summary_df.to_excel(writer, sheet_name='Özet', index=False)
        
        output.seek(0)
        return output
        
    except Exception as e:
        st.error(f"Excel oluşturma hatası: {str(e)}")
        return None

def main():
    """Main application"""
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>⚡ EPIAS Elektrik Verisi Çekici</h1>
        <p>Türkiye elektrik piyasası şeffaflık platformu veri çekici</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Authentication Section
    if not st.session_state.authenticated:
        st.markdown("### 🔐 EPIAS Giriş")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            with st.form("auth_form"):
                username = st.text_input("E-posta", value="celikahmetarda30@gmail.com")
                password = st.text_input("Şifre", type="password")
                
                if st.form_submit_button("🔑 Giriş Yap", type="primary"):
                    if username and password:
                        authenticate_user(username, password)
                    else:
                        st.error("E-posta ve şifre gerekli")
        
        with col2:
            st.markdown("""
            <div class="info-box">
                <h4>ℹ️ Bilgi</h4>
                <p>EPIAS şeffaflık platformu hesabınızla giriş yapın.</p>
                <p>Bu uygulama elektrik üretim verilerini çeker ve Excel formatında sunar.</p>
            </div>
            """, unsafe_allow_html=True)
    
    else:
        # Main Dashboard
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown(f"### 👋 Hoş Geldiniz, {st.session_state.username}")
        
        with col2:
            if st.button("🚪 Çıkış", type="secondary"):
                logout()
        
        st.markdown("---")
        
        # Data Extraction Form
        st.markdown("### 📊 Veri Çekme")
        
        with st.form("extract_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                start_date = st.date_input(
                    "Başlangıç Tarihi",
                    value=datetime.now() - timedelta(days=7),
                    max_value=datetime.now().date()
                )
            
            with col2:
                end_date = st.date_input(
                    "Bitiş Tarihi",
                    value=datetime.now().date(),
                    max_value=datetime.now().date()
                )
            
            # Quick date buttons
            st.markdown("**Hızlı Tarih Seçimi:**")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if st.form_submit_button("Son 3 Gün"):
                    end_date = datetime.now().date()
                    start_date = end_date - timedelta(days=3)
            
            with col2:
                if st.form_submit_button("Son 7 Gün"):
                    end_date = datetime.now().date()
                    start_date = end_date - timedelta(days=7)
            
            with col3:
                if st.form_submit_button("Son 15 Gün"):
                    end_date = datetime.now().date()
                    start_date = end_date - timedelta(days=15)
            
            with col4:
                if st.form_submit_button("Son 30 Gün"):
                    end_date = datetime.now().date()
                    start_date = end_date - timedelta(days=30)
            
            # Power plant selection
            st.markdown("**Santral Seçimi (İsteğe Bağlı):**")
            
            col1, col2 = st.columns([3, 1])
            
            with col1:
                power_plant_id = st.selectbox(
                    "Santral",
                    options=[""] + [f"{plant.get('id', plant.get('powerPlantId', 'N/A'))} - {plant.get('name', plant.get('shortName', 'N/A'))}" 
                            for plant in st.session_state.get('power_plants', [])],
                    format_func=lambda x: "Tüm Santraller" if x == "" else x
                )
            
            with col2:
                if st.form_submit_button("🔄 Santral Listesini Yükle"):
                    plants = load_power_plants()
                    if plants:
                        st.session_state.power_plants = plants
                        st.success(f"✅ {len(plants)} santral yüklendi")
                        st.rerun()
            
            # Advanced options
            chunk_days = st.slider("Chunk Boyutu (Gün)", min_value=1, max_value=90, value=15,
                                 help="Büyük tarih aralıkları için veri kaç günlük parçalara bölünsün")
            
            # Extract button
            extract_submitted = st.form_submit_button("🚀 Veri Çekmeyi Başlat", type="primary")
        
        # Process extraction
        if extract_submitted:
            # Extract power plant ID if selected
            selected_plant_id = None
            if power_plant_id and power_plant_id != "":
                selected_plant_id = power_plant_id.split(" - ")[0]
            
            # Extract data
            data = extract_data(start_date, end_date, selected_plant_id, chunk_days)
            
            if data:
                st.session_state.extracted_data = data
                st.session_state.extraction_date = datetime.now()
        
        # Results Section
        if 'extracted_data' in st.session_state and st.session_state.extracted_data:
            st.markdown("---")
            st.markdown("### ✅ Sonuçlar")
            
            data = st.session_state.extracted_data
            
            # Summary metrics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Toplam Kayıt", f"{len(data):,}")
            
            with col2:
                file_size_mb = len(str(data)) / (1024 * 1024)
                st.metric("Tahmini Boyut", f"{file_size_mb:.2f} MB")
            
            with col3:
                if 'extraction_date' in st.session_state:
                    extraction_time = st.session_state.extraction_date
                    st.metric("İşlem Tarihi", extraction_time.strftime("%H:%M:%S"))
            
            # Data preview
            if st.checkbox("📋 Veri Önizlemesi"):
                df = pd.DataFrame(data)
                st.dataframe(df.head(100), use_container_width=True)
            
            # Download section
            st.markdown("### 📥 İndirme")
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"epias_data_{timestamp}.xlsx"
                
                excel_file = create_excel_download(data, filename)
                
                if excel_file:
                    st.download_button(
                        label="📊 Excel Dosyasını İndir",
                        data=excel_file,
                        file_name=filename,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        type="primary"
                    )
            
            with col2:
                st.info(f"💾 **Dosya:** {filename}")

# Sidebar info
with st.sidebar:
    st.markdown("## ℹ️ Uygulama Bilgisi")
    st.markdown("""
    **EPIAS Elektrik Verisi Çekici**
    
    Bu uygulama Türkiye Elektrik Piyasası (EPIAS) şeffaflık platformundan elektrik üretim verilerini çeker.
    
    **Özellikler:**
    - ⚡ Anlık veri çekme
    - 📊 Excel export
    - 🏭 Santral bazlı filtreleme
    - 📈 İlerleme takibi
    - 🔒 Güvenli giriş
    
    **Kullanım:**
    1. EPIAS hesabınızla giriş yapın
    2. Tarih aralığını seçin
    3. Veri çekmeyi başlatın
    4. Excel dosyasını indirin
    """)
    
    st.markdown("---")
    st.markdown("**Geliştirici:** Ahmet Arda Çelik")
    st.markdown("**Versiyon:** 2.0")

if __name__ == "__main__":
    main() 