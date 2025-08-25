#!/usr/bin/env python3
import time
import requests

def test_endpoint(url, name):
    try:
        start = time.time()
        response = requests.get(url, timeout=10)
        duration = (time.time() - start) * 1000
        
        if response.status_code == 200:
            data = response.json()
            print(f'✅ {name}: {duration:.2f}ms - Success')
            
            if 'vault_path' in data:
                print(f'   📁 Vault Path: {data.get("vault_path", "Unknown")}')
            if 'ai_status' in data:
                status = "Online" if data.get('ai_status') else "Offline"
                print(f'   🤖 AI Status: {status}')
            if 'stats' in data and data['stats']:
                stats = data['stats']
                print(f'   📊 Files: {stats.get("total_files", 0)} total, {stats.get("tagged_files", 0)} tagged')
            
            return duration
        else:
            print(f'❌ {name}: {duration:.2f}ms - HTTP {response.status_code}')
            return None
    except Exception as e:
        print(f'❌ {name}: Error - {e}')
        return None

print('🧪 Testing Optimized API Endpoints')
print('=' * 50)

# Test endpoints
endpoints = [
    ('http://127.0.0.1:5000/api/status/quick', 'Quick Status'),
    ('http://127.0.0.1:5000/api/status', 'Status (no stats)'),
    ('http://127.0.0.1:5000/api/status?stats=true', 'Status (with stats)'),
    ('http://127.0.0.1:5000/api/files/recent?limit=5', 'Recent Files'),
]

results = []
for url, name in endpoints:
    print(f'\n📡 Testing {name}...')
    duration = test_endpoint(url, name)
    if duration is not None:
        results.append((name, duration))

print('\n🎯 Performance Summary')
print('=' * 50)
for name, duration in results:
    if duration < 200:
        status = '🟢 Excellent'
    elif duration < 500:
        status = '🟡 Good'
    elif duration < 1000:
        status = '🟠 Fair'
    else:
        status = '🔴 Slow'
    
    print(f'{status} {name}: {duration:.2f}ms')

if results:
    avg_time = sum(duration for _, duration in results) / len(results)
    print(f'\n📊 Average Response Time: {avg_time:.2f}ms')
    
    if avg_time < 200:
        print('🎉 Excellent performance! All optimizations working well.')
    elif avg_time < 500:
        print('👍 Good performance! Significant improvement achieved.')
    else:
        print('⚠️ Still some room for improvement.')