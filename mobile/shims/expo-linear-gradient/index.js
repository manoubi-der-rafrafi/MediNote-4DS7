const React = require('react');
const { View } = require('react-native');

// Minimal shim for expo-linear-gradient for Expo Go dev: renders a simple View wrapper.
function LinearGradient({ children, style, colors, start, end, ...rest }) {
  // This shim does not render a true gradient; it uses the first color as background.
  const backgroundColor = Array.isArray(colors) && colors.length ? colors[0] : undefined;
  return React.createElement(View, { style: [style, backgroundColor ? { backgroundColor } : {}], ...rest }, children);
}

// Export both named and default to support ES module imports and CommonJS
exports.LinearGradient = LinearGradient;
exports.default = LinearGradient;
module.exports = Object.assign(exports, { LinearGradient, default: LinearGradient });
