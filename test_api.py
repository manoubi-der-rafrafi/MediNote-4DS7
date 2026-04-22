#!/usr/bin/env python3
"""Script de test pour les endpoints API"""

import requests
import json

BASE_URL = "http://127.0.0.1:5000"

def test_orchestrate():
    """Test l'endpoint /orchestrate"""
    url = f"{BASE_URL}/orchestrate"
    data = {"demande": "génère une publication pour prochaine occasion"}
    
    response = requests.post(url, json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    return response

def test_orchestrate_opportunities():
    """Test les produits en opportunités"""
    url = f"{BASE_URL}/orchestrate"
    data = {"demande": "quels sont les produits en opportunites"}
    
    response = requests.post(url, json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    return response

def test_generation_image():
    """Test l'endpoint /generationImage"""
    url = f"{BASE_URL}/generationImage"
    data = {
        "description": "Un produit vitaminé pour la santé",
        "generation_mode": "next_occasion",
        "media_type": "image"
    }
    
    response = requests.post(url, json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    return response

def test_structuration():
    """Test l'endpoint /structure-points-forts"""
    url = f"{BASE_URL}/structure-points-forts"
    data = {"text": "Ce produit est excellent, très bonne qualité, prix raisonnable"}
    
    response = requests.post(url, json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    return response

if __name__ == "__main__":
    print("=" * 50)
    print("TEST 1: Orchestrate - Publication")
    print("=" * 50)
    test_orchestrate()
    
    print("\n" + "=" * 50)
    print("TEST 2: Orchestrate - Opportunités")
    print("=" * 50)
    test_orchestrate_opportunities()
    
    print("\n" + "=" * 50)
    print("TEST 3: Generation Image")
    print("=" * 50)
    test_generation_image()
    
    print("\n" + "=" * 50)
    print("TEST 4: Structuration")
    print("=" * 50)
    test_structuration()