const React = require('react');
const { View, Text } = require('react-native');

function Placeholder({ children, style }) {
  return React.createElement(View, { style: [{ padding: 8, alignItems: 'center', justifyContent: 'center' }, style] },
    React.createElement(Text, { style: { color: '#888' } }, 'Chart placeholder')
  );
}

// Export lightweight stubs for the Victory components used in the app.
module.exports = {
  VictoryBar: Placeholder,
  VictoryLine: Placeholder,
  VictoryChart: ({ children, ...props }) => React.createElement(View, props, children),
  VictoryGroup: Placeholder,
  VictoryPie: Placeholder,
  VictoryAxis: Placeholder,
  VictoryTheme: {},
  VictoryLegend: Placeholder,
  VictoryStack: Placeholder,
};
