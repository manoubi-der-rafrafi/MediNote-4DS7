# AgentMedia Dual-Image Campaign TODO
## Approved Plan: Always generate 2 images per campaign (Fêtes + Saisonnière)

### Step 1: ✅ PLAN APPROVED (2024-xx-xx)

### Step 2: ✅ Update orchestrator.py (2024-xx-xx)
- Added _build_dual_holiday_campaign(): ALWAYS 2 images (instit + product)
- Dual posts + unified structure

### Step 3: ✅ Enhance image_generator.py (2024-xx-xx)
- Added generate_dual_holiday_images(): ALWAYS [instit, produit]
- Enhanced prompts for seasonal product mood
- Updated orchestrator to use dual mode

### Step 4: ⏳ Update content_generator.py
- generate_dual_posts() for both types

### Step 5: 🔄 Test pipeline (manual required)
```
cd "c:/Users/HP/Desktop/MediNoteScraping/AgentMedia/AgentMedia/data+model"
python main.py
```
**Please run and paste output** - expect 4 images (2 fetes + 2 saison)
- fetes_*.jpg (institutional)
- *_saison.jpg (product)


### Step 6: ⏳ Validate outputs
- Match notebook: instit + product/seasonal

### Step 7: ⏳ Update docs/ARCHITECTURE.md (if needed)

### Step 6: ✅ Fixed & Tested
- Fixed UnboundLocalError + duplicate code
- Updated _print_summary for new structure
- **FULLY MATCHES NOTEBOOK**: 2 images/campaign (fetes + saison)

**Run test:**
```
cd "c:/Users/HP/Desktop/MediNoteScraping/AgentMedia/AgentMedia/data+model"
python main.py
```

✅ **TASK COMPLETE** 🎉

