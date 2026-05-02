# 📱 CRM Pharma — Multi-Mode Mobile App

Complete mobile CRM application for pharmaceutical professionals with separate interfaces for **Médecin (Doctor)**, **Pharmacie (Pharmacy)**, and **Délégué (Delegate)**.

## 🏗️ Architecture

### Project Structure
```
mobile/
├── App.tsx                 # Current Délégué (Delegate) mode
├── AppMedecin.js          # Médecin (Doctor) mode
├── AppPharmacie.js        # Pharmacie (Pharmacy) mode
├── app.json               # Expo configuration
├── package.json
├── src/
│   ├── theme.js           # Unified design tokens
│   ├── components/
│   │   ├── medecin/       # Doctor-specific components
│   │   │   └── index.js
│   │   └── pharmacie/     # Pharmacy-specific components
│   │       └── index.js
│   ├── screens/
│   │   ├── ProfilMedecinScreen.js
│   │   ├── HistoriqueVisitesScreen.js
│   │   ├── AlertesStockScreen.js
│   │   ├── AnalysePharmacienScreen.js
│   │   ├── LoginScreen.js
│   │   ├── FeedScreen.js
│   │   ├── BriefScreen.js
│   │   ├── SaisieScreen.js
│   │   └── ScoreScreen.js
│   └── context/
│       └── SessionContext.js
└── ...
```

---

## 👨‍⚕️ Médecin (Doctor) Mode

**Purpose**: CRM dashboard for medical professionals

### Features
- **Profil Médecin**: Doctor profile with prescription prediction (Nb09 · AUC=1.0)
- **Historique Visites**: Visit history & quality scores (Nb11 · RF AUC=0.984)
- NLP Sentiment Analysis (Nb12 · CamemBERT)
- Product recommendations (Nb04 · Gemini AI)
- Real-time visit quality metrics

### Components
- `RingChart` - Progress visualization
- `SentimentBar` - NLP sentiment analysis display
- `ProductRow` - Recommended products list
- `VisitRow` - Visit history entries
- `FlagsRow` - Key insights from visits

### Theme Colors
- **Primary**: Teal (`#2DD4BF`) — representing healthcare
- **Accents**: Blue, Green, Orange, Red, Purple

### Usage
```javascript
import AppMedecin from './AppMedecin.js';

// In index.js or your root component
export default AppMedecin;
```

---

## 💊 Pharmacie (Pharmacy) Mode

**Purpose**: Inventory & sales analytics for pharmacies

### Features
- **Alertes Stock**: Expiry & risk management (Nb07 · 4-level classification)
- **Analyse Pharmacien**: Performance & tier eligibility analysis (Nb11 · RF AUC=0.984)
- Segment analysis (Nb03 · K-Means clustering)
- Financial impact tracking
- Product trend visualization

### Components
- `ExpiryRow` - Expiring product listings
- `ExpiryBadge` - Risk level indicators
- `SegmentBadge` - Pharmacy segmentation display
- `ProgressBar` - Tier criteria breakdown
- `ActionItem` - Recommended actions

### Theme Colors
- **Primary**: Gold/Amber (`#FBBF24`) — representing stock/value
- **Accents**: Teal, Green, Blue, Orange, Red, Purple

### Usage
```javascript
import AppPharmacie from './AppPharmacie.js';

// In index.js or your root component
export default AppPharmacie;
```

---

## 👛 Délégué (Delegate) Mode

**Purpose**: Field sales representative CRM

### Screens
- **Feed**: Activity dashboard
- **Brief**: Pre-visit briefing & guidance
- **Saisie**: Visit data entry
- **Score**: Performance metrics

---

## 🎨 Design System

### Colors (Unified Across Modes)
```javascript
{
  // Grayscale
  bg:  '#0E0E10',    // Background
  s1:  '#18181C',    // Surface 1
  s2:  '#22222A',    // Surface 2
  s3:  '#2A2A35',    // Surface 3
  bd:  'rgba(...)',  // Border
  t1:  '#F4F4F6',    // Text primary
  t2:  '#A0A0B0',    // Text secondary
  t3:  '#60607A',    // Text tertiary

  // Brands & Accents
  teal:   '#2DD4BF',  // Médecin brand
  gold:   '#FBBF24',  // Pharmacie brand
  blue:   '#4F8EF7',  // Data/info
  green:  '#34D399',  // Success
  orange: '#FB923C',  // Warning
  red:    '#F87171',  // Critical
  purple: '#A78BFA',  // Secondary accent
}
```

### Spacing
```javascript
{ xs: 4, sm: 8, md: 12, lg: 16, xl: 24, xxl: 32 }
```

### Typography
```javascript
{
  xs: 10,    // Caption
  sm: 12,    // Label
  md: 13,    // Small body
  base: 14,  // Body
  lg: 16,    // Large body
  xl: 18,    // Heading
  xxl: 22,   // Sub-heading
  h: 26,     // Display
}
```

---

## 🔄 Switching Between Modes

### Option 1: Update index.js (Recommended)
```javascript
// index.js
// import App from './App';              // Délégué
import App from './AppMedecin.js';     // Médecin
// import App from './AppPharmacie.js'; // Pharmacie

export default App;
```

### Option 2: Dynamic Mode Selection (Advanced)
Create a launcher screen that lets users select their mode at startup:

```javascript
import React, { useState } from 'react';
import AppMedecin from './AppMedecin.js';
import AppPharmacie from './AppPharmacie.js';
import App from './App';

export default function Launcher() {
  const [mode, setMode] = useState(null);

  if (!mode) {
    return <ModeSelector onSelect={setMode} />;
  }

  if (mode === 'medecin') return <AppMedecin />;
  if (mode === 'pharmacie') return <AppPharmacie />;
  return <App />;
}
```

---

## 📊 Data Models & AI Models

### Médecin Models
- **Nb09**: Rx Prediction (Random Forest) — AUC = 1.0
- **Nb12**: NLP Sentiment Analysis (CamemBERT)
- **Nb04**: Product Recommendations (Gemini AI)
- **Nb11**: Visit Quality Scoring (RF) — AUC = 0.984

### Pharmacie Models
- **Nb07**: Expiry Risk Classification (4-level)
- **Nb03**: Pharmacy Segmentation (K-Means clustering)
- **Nb11**: Tier Eligibility (RF) — AUC = 0.984
- **Nb04**: Sales Analytics (Gemini AI)

---

## 🚀 Running the App

### Install Dependencies
```bash
npm install
# or
yarn install
```

### Start Expo
```bash
npx expo start
```

### Run on Android
```bash
npx expo start --android
```

### Run on iOS
```bash
npx expo start --ios
```

---

## 🔌 Dependencies

- `react-native` 0.73.6
- `react` 18.2.0
- `@react-navigation/native` ^6.1.17
- `@react-navigation/bottom-tabs` ^6.5.20
- `@react-navigation/native-stack` ^6.9.26
- `react-native-svg` 14.1.0
- `expo` ~50.0.0

---

## 📱 Screens Overview

### Médecin Flow
```
Tab Navigator
├── Profil Médecin Stack
│   ├── ProfilMedecinScreen (Rx prediction, sentiment analysis, products)
│   └── HistoriqueVisitesScreen (visit quality, tier distribution)
└── HistoriqueVisites (direct access)
```

### Pharmacie Flow
```
Tab Navigator
├── Alertes Stock Stack
│   ├── AlertesStockScreen (expiry risks, segment analysis)
│   └── AnalysePharmacienScreen (tier eligibility, product performance)
└── Analyse Pharmacien (direct access)
```

---

## 🎯 Navigation Details

### Médecin Navigation
- Tab 1: **Profil Médecin** (👨‍⚕️) → Shows doctor profile with predictions
- Tab 2: **Historique** (📋) → Shows visit history with filters

### Pharmacie Navigation
- Tab 1: **Alertes** (🔔) → Shows expiring products and risks
- Tab 2: **Analyse** (📊) → Shows sales performance and tier eligibility

---

## 💾 State Management

Global state via `SessionContext`:
- User authentication
- Session metadata
- Current mode/branch

---

## 🔐 Security

- All screens require session context
- Sensitive data not persisted
- Safe area handling for notched devices
- Status bar theming per mode

---

## 📝 Notes

- Each mode uses its own component library for UI consistency
- Shared theme for unified design language
- Navigation patterns optimized for each user type
- All screens support dark mode natively
- Responsive design for tablets & phones

---

**Built with Expo, React Native, and React Navigation** ✨
