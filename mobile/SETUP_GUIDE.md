# 🎯 Setup Guide — Médecin & Pharmacie Modules

## ✅ What Was Created

### 📁 New Directories
```
src/components/
├── medecin/
│   └── index.js              # Doctor-specific UI components
└── pharmacie/
    └── index.js              # Pharmacy-specific UI components
```

### 📄 New Screen Files
```
src/screens/
├── ProfilMedecinScreen.js        # Doctor profile & Rx prediction
├── HistoriqueVisitesScreen.js    # Doctor visit history
├── AlertesStockScreen.js         # Pharmacy expiry alerts
└── AnalysePharmacienScreen.js    # Pharmacy analysis & opportunities
```

### 🚀 New App Entry Points
```
AppMedecin.js                    # Doctor mode application
AppPharmacie.js                  # Pharmacy mode application
```

### 📚 Documentation
```
MODES_DOCUMENTATION.md           # Complete architecture & usage guide
SETUP_GUIDE.md                   # This file
```

---

## 🏃 Quick Start

### 1. Choose Your Mode

#### For Médecin (Doctor) Mode
Edit `index.js`:
```javascript
import AppMedecin from './AppMedecin.js';
export default AppMedecin;
```

#### For Pharmacie (Pharmacy) Mode
Edit `index.js`:
```javascript
import AppPharmacie from './AppPharmacie.js';
export default AppPharmacie;
```

### 2. Install & Run
```bash
# Install dependencies (if not already done)
npm install

# Start the app
npx expo start

# Run on Android or iOS
npx expo start --android
# or
npx expo start --ios
```

---

## 🎨 Médecin Mode Features

### Tab 1: Profil Médecin (👨‍⚕️)
**Doctor Profile & Prescription Prediction**

What you'll see:
- Doctor avatar & info (name, specialty, tier)
- Alert strips for follow-ups
- KPI tiles (visits/year, avg Rx/month, NPS, response rate)
- Rx Prediction score with trend
- Sentiment analysis from NLP (CamemBERT)
- Recommended products
- AI brief for pre-visit preparation

**AI Models Used:**
- Nb09: Rx Prediction (AUC = 1.0)
- Nb12: NLP Sentiment Analysis
- Nb04: Product Recommendations (Gemini)

### Tab 2: Historique (📋)
**Visit History & Quality Scoring**

What you'll see:
- Quality score overview
- Visit trend sparkline
- Tier distribution (A/B/C/D)
- Filtered visit list with dates & scores
- Insights from visit data
- Filter by tier level

**AI Models Used:**
- Nb11: Quality Scoring (AUC = 0.984)

---

## 💊 Pharmacie Mode Features

### Tab 1: Alertes Stock (🔔)
**Inventory & Expiry Management**

What you'll see:
- Pharmacy info & segment badge
- Financial impact of expiring stock
- Risk distribution (CRITICAL/URGENT/WATCH/OK)
- Sortable list of at-risk lots
- Recommended actions
- KPIs (active alerts, impact, segment, loyalty score)

**AI Models Used:**
- Nb07: Expiry Risk Classification
- Nb03: Segment Analysis (K-Means)

### Tab 2: Analyse (📊)
**Sales & Tier Eligibility**

What you'll see:
- KPI tiles (CA, growth, products, market share)
- Tier A eligibility score
- Tier criteria breakdown
- Product performance analysis
- Planned animations/events
- AI insights & recommendations

**AI Models Used:**
- Nb11: Tier Eligibility (AUC = 0.984)
- Nb04: Sales Analysis (Gemini)
- Nb03: Segment Analysis

---

## 🔄 Component Structure

### Médecin Components (`src/components/medecin/index.js`)
```javascript
⊕ RingChart          // Progress indicator
⊕ SectionLabel       // Section headers with tags
⊕ Card               // Container component
⊕ Pill               // Badge/label component
⊕ Flag               // Insight flags with colors
⊕ FlagsRow          // Row of flags
⊕ KpiTile           // Key performance indicator
⊕ SentimentBar      // NLP sentiment visualization
⊕ ProductRow        // Product listing
⊕ VisitRow          // Visit entry
⊕ AlertStrip        // Alert/notification
⊕ MiniSparkline     // Trend sparkline
```

### Pharmacie Components (`src/components/pharmacie/index.js`)
```javascript
⊕ RingChart          // Progress indicator (gold branded)
⊕ SectionLabel       // Section headers
⊕ Card               // Container
⊕ Pill               // Badge (gold branded)
⊕ KpiTile           // KPIs (gold branded)
⊕ ExpiryBadge       // Risk level badge
⊕ ExpiryRow         // Expiring product row
⊕ SegmentBadge      // Segment classification
⊕ ProgressBar       // Tier criteria bar
⊕ MiniSparkline     // Product trend
⊕ ActionItem        // Recommended action
```

---

## 🎨 Theme System

All modes use unified design tokens from `src/theme.js`:

**Colors:**
- Dark backgrounds: `bg`, `s1`, `s2`, `s3`
- Text: `t1` (primary), `t2` (secondary), `t3` (tertiary)
- Brands: `teal` (Médecin), `gold` (Pharmacie)
- Accents: `blue`, `green`, `orange`, `red`, `purple`

**Spacing:** `xs` (4px), `sm` (8px), `md` (12px), `lg` (16px), `xl` (24px), `xxl` (32px)

**Typography:**
- Sizes: `xs` to `h` (10-26px)
- All fonts use system fonts (no additional libraries)

---

## 📱 Responsive Design

- ✅ Safe area handling for notches
- ✅ Scroll views for tall content
- ✅ Flex layouts for responsive sizing
- ✅ Touch feedback on buttons
- ✅ Tab bar optimized for phones

---

## 🔧 Customization

### Change Primary Colors
Edit `src/theme.js`:
```javascript
export const colors = {
  teal: '#2DD4BF',   // Doctor brand
  gold: '#FBBF24',   // Pharmacy brand
  // ... rest of colors
};
```

### Add/Remove Tabs
Edit `AppMedecin.js` or `AppPharmacie.js`:
```javascript
const TABS = [
  { name: 'ProfilMedecin', label: 'Profil Médecin', icon: '👨‍⚕️' },
  // Add or modify tabs here
];
```

### Customize Screen Data
Edit individual screen files (e.g., `ProfilMedecinScreen.js`):
```javascript
const DOCTOR = {
  name: 'Dr. Your Name',
  specialty: 'Your Specialty',
  // ... modify data
};
```

---

## 🐛 Troubleshooting

### Components not found
- Ensure imports use correct paths: `'../components/medecin'` or `'../components/pharmacie'`
- Check that directories exist

### Theme not applying
- Verify `src/theme.js` is correctly updated
- Clear cache: `expo start -c`

### Navigation errors
- Ensure screen names match between Tab.Screen and Stack.Screen
- Check navigation.navigate() calls use correct screen names

### Missing dependencies
- Run `npm install` again
- Check `package.json` has all required packages

---

## 📊 Data Models Reference

| Model | Purpose | Accuracy |
|-------|---------|----------|
| Nb09 | Rx Prediction | AUC = 1.0 |
| Nb12 | NLP Sentiment | CamemBERT |
| Nb04 | AI Recommendations | Gemini |
| Nb11 | Quality/Tier Scoring | AUC = 0.984 |
| Nb07 | Expiry Risk | 4-level classification |
| Nb03 | Segmentation | K-Means clustering |

---

## 🎯 Next Steps

1. **Run the app**: `npx expo start`
2. **Test navigation**: Tab between screens
3. **Customize data**: Update mock data in screens
4. **Add API integration**: Replace static data with API calls
5. **Deploy**: Build with `eas build`

---

## 📞 Support

For issues or questions:
1. Check `MODES_DOCUMENTATION.md` for detailed architecture
2. Review component files for prop interfaces
3. Test imports and navigation paths
4. Clear cache and rebuild: `expo start -c`

---

**Happy coding! 🚀**
