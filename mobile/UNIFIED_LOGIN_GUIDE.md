# 🔐 Unified Login System

## Login Credentials by Mode

### Unified Entry Point
The app now has a single login screen that routes to different modes based on username prefix.

### Login Format
**Username and Password must be the same** (for testing purposes)

| Mode | Username | Password | Icon |
|------|----------|----------|------|
| **Médecin** | `med` or `medecin*` | Same as username | 👨‍⚕️ |
| **Pharmacie** | `ph` or `pharmacie*` | Same as username | 💊 |
| **Délégué** | `del` or `delegate*` | Same as username | 👛 |

*Can use any username starting with the prefix*

### Examples
```
✓ med / med      → Doctor Mode (👨‍⚕️)
✓ medecin / medecin  → Doctor Mode (👨‍⚕️)
✓ ph / ph        → Pharmacy Mode (💊)
✓ pharmacie / pharmacie → Pharmacy Mode (💊)
✓ del / del      → Delegate Mode (👛)
✓ delegate / delegate → Delegate Mode (👛)

✗ medecin / doctor   → Invalid (passwords must match)
✗ abc / abc          → Invalid (no prefix match)
```

## Architecture

### Files Changed
- **index.ts** - Now imports AppRoot instead of App
- **AppRoot.tsx** - NEW! Manages login state and mode switching
- **LoginScreen.js** - UPDATED! Now detects mode from username prefix

### Flow
```
1. App starts → AppRoot loads
2. If not authenticated → Show LoginScreen
3. User enters credentials (med*/ph*/del* format)
4. LoginScreen detects mode from username prefix
5. Sets authenticated & mode state
6. AppRoot renders appropriate app:
   - med* → AppMedecin
   - ph* → AppPharmacie
   - del* → AppDelegate (original App)
```

## Key Changes

### LoginScreen Updates
```javascript
// New prop
onModeSelect={(mode) => console.log(mode)}
// Modes: 'medecin', 'pharmacie', 'delegate'

// Mode detection logic
const getUserMode = (user) => {
  const lower = user.toLowerCase().trim();
  if (lower.startsWith('med')) return 'medecin';
  if (lower.startsWith('ph')) return 'pharmacie';
  if (lower.startsWith('del')) return 'delegate';
  return null;
};
```

## Testing Flow

### Test Médecin Mode
```
1. Open app → Login screen appears
2. Username: med, Password: med
3. Press "🔓 Se connecter"
4. App transitions to Doctor CRM
5. See: Profil Médecin tab, Historique tab
6. Theme: Teal brand
```

### Test Pharmacie Mode
```
1. Open app → Login screen appears
2. Username: ph, Password: ph
3. Press "🔓 Se connecter"
4. App transitions to Pharmacy CRM
5. See: Alertes tab, Analyse tab
6. Theme: Gold brand
```

### Test Délégué Mode
```
1. Open app → Login screen appears
2. Username: del, Password: del
3. Press "🔓 Se connecter"
4. App transitions to Delegate CRM
5. See: Feed, Brief, Saisie, Score tabs
6. Theme: Original colors
```

## Session Management

### Current Features
- ✅ Single login screen for all modes
- ✅ Mode detection from username
- ✅ Session state management
- ✅ Automatic routing to correct app

### Future Enhancements
- Real API authentication
- Token storage
- Logout functionality
- Mode switching without re-login

## Quick Reference

### Run the App
```bash
npx expo start
```

### Test All Modes
```
Login 1: med / med → Check doctor features
Restart & Login 2: ph / ph → Check pharmacy features
Restart & Login 3: del / del → Check delegate features
```

### Debug Mode Detection
Add this to LoginScreen to see detected mode:
```javascript
console.log('Detected mode:', mode);
```

---

**One login, three modes! 🚀**
