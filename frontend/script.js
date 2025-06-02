// Configuration
const CONFIG = {
    API_BASE_URL: window.location.hostname === 'localhost' 
        ? 'http://localhost:8000' 
        : '', // Same origin for production
    POLLING_INTERVAL: 2000, // 2 seconds
    TOAST_DURATION: 5000 // 5 seconds
};

// Global state
let currentTaskId = null;
let progressPollingInterval = null;
let isAuthenticated = false;
let sessionData = null;

// Initialize app
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    setupEventListeners();
    checkAuthenticationStatus();
    setDefaultDates();
}

function setupEventListeners() {
    // Authentication
    document.getElementById('authForm').addEventListener('submit', handleAuthentication);
    document.getElementById('logoutBtn').addEventListener('click', handleLogout);
    
    // Data extraction
    document.getElementById('extractForm').addEventListener('submit', handleDataExtraction);
    document.getElementById('loadPlantsBtn').addEventListener('click', loadPowerPlants);
    
    // Results
    document.getElementById('downloadBtn').addEventListener('click', handleDownload);
    
    // Cancel extraction
    document.getElementById('cancelBtn').addEventListener('click', cancelExtraction);
}

function setDefaultDates() {
    const today = new Date();
    const threeDaysAgo = new Date(today.getTime() - (3 * 24 * 60 * 60 * 1000));
    
    document.getElementById('startDate').value = threeDaysAgo.toISOString().split('T')[0];
    document.getElementById('endDate').value = today.toISOString().split('T')[0];
}

// Authentication Functions
async function checkAuthenticationStatus() {
    try {
        const response = await fetch(`${CONFIG.API_BASE_URL}/api/sessions`, {
            credentials: 'include'
        });
        
        const data = await response.json();
        
        if (data.authenticated) {
            isAuthenticated = true;
            sessionData = data;
            showDashboard();
            updateUserInfo(data);
        } else {
            showAuthSection();
        }
    } catch (error) {
        console.error('Auth check failed:', error);
        showAuthSection();
    }
}

async function handleAuthentication(event) {
    event.preventDefault();
    
    const submitBtn = document.getElementById('authBtn');
    const originalText = submitBtn.innerHTML;
    
    try {
        // Update button state
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Giriş yapılıyor...';
        
        const formData = new FormData(event.target);
        const credentials = {
            username: formData.get('username'),
            password: formData.get('password')
        };
        
        const response = await fetch(`${CONFIG.API_BASE_URL}/api/auth`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include',
            body: JSON.stringify(credentials)
        });
        
        const data = await response.json();
        
        if (data.success) {
            isAuthenticated = true;
            sessionData = data;
            showToast('success', 'Giriş Başarılı', data.message);
            showDashboard();
            updateUserInfo(data);
        } else {
            showToast('error', 'Giriş Hatası', data.message);
        }
        
    } catch (error) {
        console.error('Authentication error:', error);
        showToast('error', 'Bağlantı Hatası', 'Sunucuya bağlanılamadı');
    } finally {
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalText;
    }
}

async function handleLogout() {
    try {
        await fetch(`${CONFIG.API_BASE_URL}/api/logout`, {
            method: 'POST',
            credentials: 'include'
        });
        
        isAuthenticated = false;
        sessionData = null;
        
        // Stop any ongoing polling
        if (progressPollingInterval) {
            clearInterval(progressPollingInterval);
        }
        
        showToast('success', 'Çıkış Yapıldı', 'Başarıyla çıkış yaptınız');
        showAuthSection();
        
    } catch (error) {
        console.error('Logout error:', error);
        showToast('error', 'Çıkış Hatası', 'Çıkış yaparken hata oluştu');
    }
}

// Power Plants Functions
async function loadPowerPlants() {
    const btn = document.getElementById('loadPlantsBtn');
    const select = document.getElementById('powerPlantSelect');
    const originalText = btn.innerHTML;
    
    try {
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Yükleniyor...';
        
        const response = await fetch(`${CONFIG.API_BASE_URL}/api/plants`, {
            credentials: 'include'
        });
        
        const data = await response.json();
        
        if (data.success && data.data) {
            // Clear existing options except first one
            select.innerHTML = '<option value="">Tüm Santraller</option>';
            
            // Add power plants
            data.data.forEach(plant => {
                const option = document.createElement('option');
                option.value = plant.id || plant.powerPlantId;
                option.textContent = `${plant.name || plant.shortName} (${plant.id || plant.powerPlantId})`;
                select.appendChild(option);
            });
            
            showToast('success', 'Santral Listesi', `${data.count} santral yüklendi`);
        } else {
            showToast('error', 'Santral Hatası', data.message || 'Santral listesi yüklenemedi');
        }
        
    } catch (error) {
        console.error('Load plants error:', error);
        showToast('error', 'Bağlantı Hatası', 'Santral listesi yüklenirken hata oluştu');
    } finally {
        btn.disabled = false;
        btn.innerHTML = originalText;
    }
}

// Data Extraction Functions
async function handleDataExtraction(event) {
    event.preventDefault();
    
    const submitBtn = document.getElementById('extractBtn');
    const originalText = submitBtn.innerHTML;
    
    try {
        // Validate form
        const formData = new FormData(event.target);
        const extractData = {
            start_date: formData.get('startDate'),
            end_date: formData.get('endDate'),
            power_plant_id: formData.get('powerPlantId') || null,
            chunk_days: parseInt(formData.get('chunkDays')) || 15
        };
        
        // Validate dates
        const startDate = new Date(extractData.start_date);
        const endDate = new Date(extractData.end_date);
        
        if (startDate >= endDate) {
            showToast('error', 'Tarih Hatası', 'Başlangıç tarihi bitiş tarihinden önce olmalı');
            return;
        }
        
        const daysDiff = Math.ceil((endDate - startDate) / (1000 * 60 * 60 * 24));
        if (daysDiff > 365) {
            showToast('warning', 'Tarih Uyarısı', 'Çok büyük tarih aralığı. İşlem uzun sürebilir.');
        }
        
        // Update button state
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Başlatılıyor...';
        
        const response = await fetch(`${CONFIG.API_BASE_URL}/api/extract`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include',
            body: JSON.stringify(extractData)
        });
        
        const data = await response.json();
        
        if (data.success) {
            currentTaskId = data.task_id;
            showToast('success', 'İşlem Başlatıldı', data.message);
            showProgressSection();
            startProgressPolling();
        } else {
            showToast('error', 'İşlem Hatası', data.message);
        }
        
    } catch (error) {
        console.error('Extraction error:', error);
        showToast('error', 'Bağlantı Hatası', 'Veri çekme işlemi başlatılamadı');
    } finally {
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalText;
    }
}

function startProgressPolling() {
    if (progressPollingInterval) {
        clearInterval(progressPollingInterval);
    }
    
    progressPollingInterval = setInterval(async () => {
        if (!currentTaskId) return;
        
        try {
            const response = await fetch(`${CONFIG.API_BASE_URL}/api/extract/status/${currentTaskId}`, {
                credentials: 'include'
            });
            
            const data = await response.json();
            
            if (data.success && data.task_info) {
                updateProgressDisplay(data.task_info);
                
                // Stop polling if completed or error
                if (data.task_info.status === 'completed' || data.task_info.status === 'error') {
                    clearInterval(progressPollingInterval);
                    progressPollingInterval = null;
                    
                    if (data.task_info.status === 'completed') {
                        showResultsSection(data.task_info);
                        showToast('success', 'İşlem Tamamlandı', data.task_info.message);
                    } else {
                        showToast('error', 'İşlem Hatası', data.task_info.message);
                    }
                }
            }
            
        } catch (error) {
            console.error('Progress polling error:', error);
        }
    }, CONFIG.POLLING_INTERVAL);
}

function updateProgressDisplay(taskInfo) {
    // Update progress bar
    const progressFill = document.getElementById('progressFill');
    const progressText = document.getElementById('progressText');
    const progress = Math.round(taskInfo.progress || 0);
    
    progressFill.style.width = `${progress}%`;
    progressText.textContent = `${progress}%`;
    
    // Update status
    document.getElementById('progressStatus').textContent = getStatusText(taskInfo.status);
    document.getElementById('progressMessage').textContent = taskInfo.message || '-';
    
    // Update current period
    if (taskInfo.current_period) {
        const period = `${taskInfo.current_period.start} - ${taskInfo.current_period.end}`;
        document.getElementById('progressPeriod').textContent = period;
    }
    
    // Update start time
    if (taskInfo.started_at) {
        const startTime = new Date(taskInfo.started_at).toLocaleString('tr-TR');
        document.getElementById('progressStartTime').textContent = startTime;
    }
}

function getStatusText(status) {
    const statusMap = {
        'running': 'Çalışıyor',
        'completed': 'Tamamlandı',
        'error': 'Hata',
        'cancelled': 'İptal Edildi'
    };
    
    return statusMap[status] || status;
}

function cancelExtraction() {
    if (progressPollingInterval) {
        clearInterval(progressPollingInterval);
        progressPollingInterval = null;
    }
    
    currentTaskId = null;
    hideProgressSection();
    showToast('warning', 'İşlem İptal Edildi', 'Veri çekme işlemi iptal edildi');
}

// Results Functions
function showResultsSection(taskInfo) {
    const section = document.getElementById('resultsSection');
    section.style.display = 'block';
    section.classList.add('fade-in');
    
    if (taskInfo.data) {
        // Update summary
        document.getElementById('recordCount').textContent = 
            taskInfo.data.record_count?.toLocaleString('tr-TR') || '-';
        
        document.getElementById('fileSize').textContent = 
            taskInfo.data.file_info?.file_size_mb ? `${taskInfo.data.file_info.file_size_mb} MB` : '-';
        
        // Calculate processing time
        if (taskInfo.started_at && taskInfo.completed_at) {
            const start = new Date(taskInfo.started_at);
            const end = new Date(taskInfo.completed_at);
            const duration = Math.round((end - start) / 1000);
            
            let timeText = '';
            if (duration < 60) {
                timeText = `${duration} saniye`;
            } else if (duration < 3600) {
                timeText = `${Math.round(duration / 60)} dakika`;
            } else {
                timeText = `${Math.round(duration / 3600)} saat`;
            }
            
            document.getElementById('processingTime').textContent = timeText;
        }
        
        // Setup download button
        const downloadBtn = document.getElementById('downloadBtn');
        if (taskInfo.data.file_info?.filename) {
            downloadBtn.dataset.filename = taskInfo.data.file_info.filename;
            downloadBtn.disabled = false;
        }
    }
}

async function handleDownload() {
    const btn = document.getElementById('downloadBtn');
    const filename = btn.dataset.filename;
    
    if (!filename) {
        showToast('error', 'İndirme Hatası', 'İndirilecek dosya bulunamadı');
        return;
    }
    
    try {
        const originalText = btn.innerHTML;
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> İndiriliyor...';
        
        const response = await fetch(`${CONFIG.API_BASE_URL}/api/download/${filename}`, {
            credentials: 'include'
        });
        
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            
            showToast('success', 'İndirme Başarılı', 'Dosya başarıyla indirildi');
        } else {
            const errorData = await response.json();
            showToast('error', 'İndirme Hatası', errorData.message || 'Dosya indirilemedi');
        }
        
    } catch (error) {
        console.error('Download error:', error);
        showToast('error', 'İndirme Hatası', 'Dosya indirirken hata oluştu');
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-file-excel"></i> Excel Dosyasını İndir';
    }
}

// UI Functions
function showAuthSection() {
    document.getElementById('authSection').style.display = 'block';
    document.getElementById('dashboardSection').style.display = 'none';
    document.getElementById('logoutBtn').style.display = 'none';
}

function showDashboard() {
    document.getElementById('authSection').style.display = 'none';
    document.getElementById('dashboardSection').style.display = 'block';
    document.getElementById('logoutBtn').style.display = 'flex';
    
    // Reset sections
    hideProgressSection();
    hideResultsSection();
}

function showProgressSection() {
    const section = document.getElementById('progressSection');
    section.style.display = 'block';
    section.classList.add('fade-in');
    
    // Reset progress
    document.getElementById('progressFill').style.width = '0%';
    document.getElementById('progressText').textContent = '0%';
    document.getElementById('progressStatus').textContent = 'Başlatılıyor...';
    document.getElementById('progressMessage').textContent = '-';
    document.getElementById('progressPeriod').textContent = '-';
    document.getElementById('progressStartTime').textContent = '-';
    
    // Hide results
    hideResultsSection();
}

function hideProgressSection() {
    document.getElementById('progressSection').style.display = 'none';
}

function hideResultsSection() {
    document.getElementById('resultsSection').style.display = 'none';
}

function updateUserInfo(data) {
    document.getElementById('welcomeText').textContent = `Hoş Geldiniz!`;
    document.getElementById('userEmail').textContent = data.username || sessionData?.username || '-';
}

// Utility Functions
function setQuickDate(days) {
    const today = new Date();
    const startDate = new Date(today.getTime() - (days * 24 * 60 * 60 * 1000));
    
    document.getElementById('startDate').value = startDate.toISOString().split('T')[0];
    document.getElementById('endDate').value = today.toISOString().split('T')[0];
}

function togglePassword() {
    const input = document.getElementById('password');
    const icon = document.querySelector('.password-toggle i');
    
    if (input.type === 'password') {
        input.type = 'text';
        icon.className = 'fas fa-eye-slash';
    } else {
        input.type = 'password';
        icon.className = 'fas fa-eye';
    }
}

// Toast Notification System
function showToast(type, title, message) {
    const container = document.getElementById('toastContainer');
    
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    const iconMap = {
        success: 'fas fa-check-circle',
        error: 'fas fa-exclamation-circle',
        warning: 'fas fa-exclamation-triangle',
        info: 'fas fa-info-circle'
    };
    
    toast.innerHTML = `
        <div class="toast-icon">
            <i class="${iconMap[type] || iconMap.info}"></i>
        </div>
        <div class="toast-content">
            <div class="toast-title">${title}</div>
            <div class="toast-message">${message}</div>
        </div>
        <button class="toast-close" onclick="closeToast(this)">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    container.appendChild(toast);
    
    // Auto remove after duration
    setTimeout(() => {
        if (toast.parentNode) {
            closeToast(toast.querySelector('.toast-close'));
        }
    }, CONFIG.TOAST_DURATION);
}

function closeToast(button) {
    const toast = button.closest('.toast');
    if (toast) {
        toast.classList.add('fade-out');
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 300);
    }
}

// Error Handling
window.addEventListener('error', function(event) {
    console.error('Global error:', event.error);
    showToast('error', 'Uygulama Hatası', 'Beklenmeyen bir hata oluştu');
});

window.addEventListener('unhandledrejection', function(event) {
    console.error('Unhandled promise rejection:', event.reason);
    showToast('error', 'İşlem Hatası', 'Bir işlem tamamlanamadı');
});

// Cleanup on page unload
window.addEventListener('beforeunload', function() {
    if (progressPollingInterval) {
        clearInterval(progressPollingInterval);
    }
}); 