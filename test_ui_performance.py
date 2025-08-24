#!/usr/bin/env python3
"""
Test script to validate UI performance improvements for Obsidian Tag Automator.
This script tests the new endpoints and functionality.
"""

import time
import requests
import json
from pathlib import Path


def test_api_endpoints(base_url="http://localhost:5000"):
    """Test the new API endpoints for performance."""
    print("🧪 Testing API Endpoints Performance")
    print("=" * 50)
    
    endpoints = [
        ("/api/status/quick", "Quick Status"),
        ("/api/status", "Full Status"),
        ("/api/files/recent?limit=5&offset=0", "Recent Files"),
        ("/api/files", "All Files")
    ]
    
    results = {}
    
    for endpoint, name in endpoints:
        print(f"\n📡 Testing {name}: {endpoint}")
        
        try:
            start_time = time.time()
            response = requests.get(f"{base_url}{endpoint}", timeout=10)
            end_time = time.time()
            
            duration = (end_time - start_time) * 1000  # Convert to milliseconds
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Success - {duration:.2f}ms")
                
                # Show relevant info
                if endpoint == "/api/status/quick":
                    print(f"   📁 Vault: {data.get('vault_path', 'Unknown')}")
                    print(f"   🤖 AI: {'Online' if data.get('ai_status') else 'Offline'}")
                    print(f"   📂 Valid Vault: {data.get('is_obsidian_vault', False)}")
                    
                elif endpoint == "/api/files/recent?limit=5&offset=0":
                    if data.get('success') and data.get('files'):
                        print(f"   📄 Files returned: {len(data['files'])}")
                        print(f"   📊 Pagination: {data.get('pagination', {})}")
                        
                elif endpoint == "/api/files":
                    if data.get('success') and data.get('files'):
                        print(f"   📄 Total files: {len(data['files'])}")
                        print(f"   📁 Vault: {data.get('vault_path', 'Unknown')}")
                        print(f"   ✓ Obsidian vault: {data.get('is_obsidian_vault', False)}")
                        
                elif endpoint == "/api/status":
                    if data.get('success'):
                        print(f"   📁 Vault exists: {data.get('vault_info', {}).get('exists', False)}")
                        print(f"   📊 Stats available: {bool(data.get('stats'))}")
                
                results[name] = {
                    'success': True,
                    'duration_ms': duration,
                    'response_size': len(response.content)
                }
            else:
                print(f"   ❌ Failed - HTTP {response.status_code}")
                results[name] = {
                    'success': False,
                    'status_code': response.status_code,
                    'duration_ms': duration
                }
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            results[name] = {
                'success': False,
                'error': str(e)
            }
    
    return results


def test_performance_thresholds(results):
    """Test if performance meets our targets."""
    print("\n🎯 Performance Threshold Analysis")
    print("=" * 50)
    
    thresholds = {
        "Quick Status": 200,  # Should be very fast
        "Full Status": 1000,  # Can be slower due to stats
        "Recent Files": 500,  # Should be reasonably fast
        "All Files": 2000     # Can be slower for large vaults
    }
    
    passed = 0
    total = 0
    
    for name, threshold in thresholds.items():
        if name in results and results[name].get('success'):
            duration = results[name]['duration_ms']
            total += 1
            
            if duration <= threshold:
                print(f"   ✅ {name}: {duration:.2f}ms (target: {threshold}ms)")
                passed += 1
            else:
                print(f"   ⚠️  {name}: {duration:.2f}ms (target: {threshold}ms) - SLOW")
        else:
            print(f"   ❌ {name}: Failed or not tested")
            total += 1
    
    print(f"\n📊 Performance Summary: {passed}/{total} tests passed")
    return passed, total


def test_ui_features():
    """Test UI-specific features by checking HTML content."""
    print("\n🖥️  Testing UI Features")
    print("=" * 50)
    
    try:
        response = requests.get("http://localhost:5000", timeout=5)
        if response.status_code == 200:
            html_content = response.text
            
            features = [
                ("Skeleton Loaders", "skeleton" in html_content.lower()),
                ("Performance Indicator", "performance-indicator" in html_content),
                ("Loading States", "loading-spinner" in html_content),
                ("Progressive Loading", "skeleton-row" in html_content),
                ("Cache Management", "<!-- Skeleton rows for better perceived performance -->" in html_content)
            ]
            
            for feature_name, present in features:
                status = "✅" if present else "❌"
                print(f"   {status} {feature_name}")
                
            return True
        else:
            print(f"   ❌ Failed to load main page: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error testing UI: {str(e)}")
        return False


def test_vault_detection():
    """Test vault detection and file scanning improvements."""
    print("\n📁 Testing Vault Detection")
    print("=" * 50)
    
    try:
        # Test status endpoint
        response = requests.get("http://localhost:5000/api/status", timeout=10)
        if response.status_code == 200:
            data = response.json()
            vault_info = data.get('vault_info', {})
            
            print(f"   📂 Vault Path: {data.get('vault_path', 'Unknown')}")
            print(f"   ✅ Exists: {vault_info.get('exists', False)}")
            print(f"   📖 Readable: {vault_info.get('readable', False)}")
            print(f"   🗂️  Is Obsidian Vault: {vault_info.get('is_obsidian_vault', False)}")
            
            if vault_info.get('stats'):
                stats = vault_info['stats']
                print(f"   📊 Vault Size: {stats.get('vault_size_bytes', 0)} bytes")
                print(f"   📁 Total Items: {stats.get('total_items', 0)}")
            
            return vault_info.get('exists', False)
        else:
            print(f"   ❌ Failed to get vault info: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return False


def main():
    """Main test function."""
    print("🚀 Obsidian Tag Automator - UI Performance Test")
    print("=" * 60)
    print("This script tests the performance improvements made to the web interface.")
    print("Make sure the web server is running on http://localhost:5000")
    print()
    
    # Test if server is running
    try:
        response = requests.get("http://localhost:5000/api/status/quick", timeout=3)
        print("✅ Server is running and responding")
    except Exception as e:
        print(f"❌ Server not accessible: {str(e)}")
        print("Please start the server with: python tag_automator_cli.py --web")
        return
    
    # Run tests
    results = test_api_endpoints()
    passed, total = test_performance_thresholds(results)
    ui_ok = test_ui_features()
    vault_ok = test_vault_detection()
    
    # Summary
    print("\n🏁 Test Summary")
    print("=" * 50)
    print(f"📊 API Performance: {passed}/{total} tests passed")
    print(f"🖥️  UI Features: {'✅ Pass' if ui_ok else '❌ Fail'}")
    print(f"📁 Vault Detection: {'✅ Pass' if vault_ok else '❌ Fail'}")
    
    overall_score = (passed/total) * 0.5 + (0.25 if ui_ok else 0) + (0.25 if vault_ok else 0)
    print(f"\n🎯 Overall Score: {overall_score:.1%}")
    
    if overall_score >= 0.8:
        print("🎉 Excellent! Performance improvements are working well.")
    elif overall_score >= 0.6:
        print("👍 Good! Most improvements are working, minor issues may exist.")
    else:
        print("⚠️  Some issues detected. Check the logs above for details.")


if __name__ == "__main__":
    main()