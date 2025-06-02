#!/usr/bin/env python3
"""
EPIAS API Debugger - Ne oluyor görelim
"""

import requests
import json
from datetime import datetime, timedelta

def debug_epias():
    """EPIAS API'sini debug et"""
    
    print("🔍 EPIAS API Debug Modu")
    print("=" * 40)
    
    username = "celikahmetarda30@gmail.com"
    password = input("🔒 Şifreniz: ").strip()
    
    # 1. Authentication test
    print("\n1️⃣ Authentication Testi...")
    
    auth_url = "https://giris.epias.com.tr/cas/v1/tickets"
    auth_headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'text/plain'
    }
    auth_data = {
        'username': username,
        'password': password
    }
    
    try:
        auth_response = requests.post(auth_url, data=auth_data, headers=auth_headers, timeout=30)
        print(f"   Status: {auth_response.status_code}")
        
        if auth_response.status_code == 201:
            tgt_token = auth_response.text.strip()
            print(f"   ✅ TGT alındı: {tgt_token[:30]}...")
        else:
            print(f"   ❌ Auth başarısız: {auth_response.text}")
            return
            
    except Exception as e:
        print(f"   ❌ Auth hatası: {e}")
        return
    
    # 2. Santral listesi test
    print("\n2️⃣ Santral Listesi Testi...")
    
    plants_url = "https://seffaflik.epias.com.tr/electricity-service/v1/generation/data/injection-quantity-powerplant-list"
    plants_headers = {
        'TGT': tgt_token,
        'Accept': 'application/json'
    }
    
    try:
        plants_response = requests.get(plants_url, headers=plants_headers, timeout=30)
        print(f"   Status: {plants_response.status_code}")
        print(f"   Response size: {len(plants_response.text)} karakter")
        
        if plants_response.status_code == 200:
            plants_data = plants_response.json()
            print(f"   ✅ Response type: {type(plants_data)}")
            
            # Response yapısını incele
            if isinstance(plants_data, dict):
                print(f"   📋 Dict keys: {list(plants_data.keys())}")
                if 'body' in plants_data:
                    body = plants_data['body']
                    print(f"   📋 Body type: {type(body)}")
                    if isinstance(body, dict):
                        print(f"   📋 Body keys: {list(body.keys())}")
                        if 'powerPlantList' in body:
                            plants = body['powerPlantList']
                            print(f"   ✅ {len(plants)} santral bulundu")
                            if len(plants) > 0:
                                print(f"   📝 İlk santral: {plants[0]}")
            elif isinstance(plants_data, list):
                print(f"   ✅ {len(plants_data)} santral bulundu")
                if len(plants_data) > 0:
                    print(f"   📝 İlk santral: {plants_data[0]}")
        else:
            print(f"   ❌ Santral listesi başarısız")
            print(f"   📄 Response: {plants_response.text[:300]}...")
            
    except Exception as e:
        print(f"   ❌ Santral listesi hatası: {e}")
    
    # 3. Injection quantity test (farklı tarih formatları)
    print("\n3️⃣ Injection Quantity Testi...")
    
    injection_url = "https://seffaflik.epias.com.tr/electricity-service/v1/generation/data/injection-quantity"
    injection_headers = {
        'TGT': tgt_token,
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    
    # Farklı tarih formatları test et
    date_formats = [
        {
            "name": "ISO Format +03:00",
            "startDate": "2025-05-01T00:00:00+03:00",
            "endDate": "2025-05-02T00:00:00+03:00"
        },
        {
            "name": "ISO Format UTC",
            "startDate": "2025-05-01T00:00:00Z",
            "endDate": "2025-05-02T00:00:00Z"
        },
        {
            "name": "Simple Date",
            "startDate": "2025-05-01",
            "endDate": "2025-05-02"
        },
        {
            "name": "Recent Date (3 gün önce)",
            "startDate": (datetime.now() - timedelta(days=3)).strftime('%Y-%m-%dT%H:%M:%S+03:00'),
            "endDate": datetime.now().strftime('%Y-%m-%dT%H:%M:%S+03:00')
        }
    ]
    
    for i, date_format in enumerate(date_formats, 1):
        print(f"\n   3.{i} {date_format['name']} Testi...")
        
        payload = {
            "startDate": date_format["startDate"],
            "endDate": date_format["endDate"]
        }
        
        print(f"       📅 Payload: {json.dumps(payload, indent=6)}")
        
        try:
            injection_response = requests.post(
                injection_url, 
                json=payload, 
                headers=injection_headers, 
                timeout=60
            )
            
            print(f"       Status: {injection_response.status_code}")
            print(f"       Response size: {len(injection_response.text)} karakter")
            
            if injection_response.status_code == 200:
                injection_data = injection_response.json()
                print(f"       ✅ Response type: {type(injection_data)}")
                
                # Response yapısını incele
                if isinstance(injection_data, dict):
                    print(f"       📋 Dict keys: {list(injection_data.keys())}")
                    if 'body' in injection_data:
                        body = injection_data['body']
                        print(f"       📋 Body type: {type(body)}")
                        if isinstance(body, dict):
                            print(f"       📋 Body keys: {list(body.keys())}")
                            if 'items' in body:
                                items = body['items']
                                print(f"       ✅ {len(items)} kayıt bulundu")
                                if len(items) > 0:
                                    print(f"       📝 İlk kayıt keys: {list(items[0].keys())}")
                                    print(f"       📝 İlk kayıt: {items[0]}")
                                    break  # Başarılı olunca dur
                            else:
                                print(f"       ⚠️ 'items' key bulunamadı")
                elif isinstance(injection_data, list):
                    print(f"       ✅ {len(injection_data)} kayıt bulundu")
                    if len(injection_data) > 0:
                        print(f"       📝 İlk kayıt: {injection_data[0]}")
                        break  # Başarılı olunca dur
            else:
                print(f"       ❌ Request başarısız")
                print(f"       📄 Response: {injection_response.text[:300]}...")
                
        except Exception as e:
            print(f"       ❌ Request hatası: {e}")
    
    # 4. Export test
    print("\n4️⃣ Export Servisi Testi...")
    
    export_url = "https://seffaflik.epias.com.tr/electricity-service/v1/generation/export/injection-quantity"
    
    export_payload = {
        "startDate": "2025-05-01T00:00:00+03:00",
        "endDate": "2025-05-02T00:00:00+03:00",
        "exportType": "XLSX"
    }
    
    try:
        export_response = requests.post(
            export_url, 
            json=export_payload, 
            headers=injection_headers, 
            timeout=60
        )
        
        print(f"   Status: {export_response.status_code}")
        print(f"   Content-Type: {export_response.headers.get('content-type', 'N/A')}")
        print(f"   Response size: {len(export_response.content)} bytes")
        
        if export_response.status_code == 200:
            if 'application/vnd.openxmlformats' in export_response.headers.get('content-type', ''):
                print("   ✅ Excel dosyası alındı!")
                with open('debug_export.xlsx', 'wb') as f:
                    f.write(export_response.content)
                print("   💾 debug_export.xlsx olarak kaydedildi")
            else:
                print(f"   📄 Response (ilk 300 karakter): {export_response.text[:300]}...")
        else:
            print(f"   ❌ Export başarısız: {export_response.text[:300]}...")
            
    except Exception as e:
        print(f"   ❌ Export hatası: {e}")
    
    print("\n🎯 Debug tamamlandı!")

if __name__ == "__main__":
    debug_epias()