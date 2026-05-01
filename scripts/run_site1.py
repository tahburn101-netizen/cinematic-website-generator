#!/usr/bin/env python3
"""Run pipeline for Website 1: Nobu Restaurants (restaurant niche)"""
import sys
sys.path.insert(0, '/home/ubuntu/cinematic-pipeline')
sys.path.insert(0, '/home/ubuntu/cinematic-pipeline/modules')
from pipeline import run_pipeline

result = run_pipeline("https://www.noburestaurants.com")
print("\n=== SITE 1 RESULT ===")
print(f"Success: {result['success']}")
print(f"Live URL: {result.get('live_url', 'N/A')}")
print(f"Time: {result.get('total_time')}s")
