// Learn more https://docs.expo.io/guides/customizing-metro
const { getDefaultConfig } = require('expo/metro-config');

/** @type {import('expo/metro-config').MetroConfig} */
const config = getDefaultConfig(__dirname);

// Fix Expo Go infinite reload bug
config.resolver.sourceExts = ['jsx', 'js', 'ts', 'tsx', 'json'];
config.transformer.getTransformOptions = async () => ({
  transform: {
    experimentalImportSupport: false,
    inlineRequires: true,
  },
});

module.exports = config;

// Redirect heavy native chart lib to a JS shim during Expo Go development
const path = require('path');
config.resolver.extraNodeModules = {
  'victory-native': path.join(__dirname, 'shims', 'victory-native'),
  'expo-linear-gradient': path.join(__dirname, 'shims', 'expo-linear-gradient'),
};
config.watchFolders = config.watchFolders || [];
config.watchFolders.push(path.join(__dirname, 'shims'));

module.exports = config;
