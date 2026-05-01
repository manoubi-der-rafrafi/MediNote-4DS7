// Shared design tokens - use everywhere
export const theme = {
  colors: {
    bg: '#080910',
    s1: '#0F1018',
    s2: '#161820',
    s3: '#1D1F2A',
    s4: '#252835',
    b1: '#2A2D3E',
    b2: '#353850',
    b3: '#424660',
    txt: '#ECEEF8',
    txt2: '#8B8FA8',
    txt3: '#4E5268',
    blue: '#5B8DF6',
    blueDark: '#3B6FE0',
    green: '#3DD68C',
    greenDark: '#2dbb6b',
    purple: '#9B7FFF',
    amber: '#F5A623',
    red: '#F06565',
    teal: '#2DD4BF',
  },
  fonts: {
    heading: "'Syne', sans-serif",
    body: "'DM Sans', sans-serif",
    mono: "'DM Mono', monospace",
  },
  radius: {
    r: '8px',
    r2: '12px',
    r3: '16px',
  },
  spacing: {
    xs: '4px',
    sm: '8px',
    md: '12px',
    lg: '16px',
    xl: '24px',
    '2xl': '32px',
  },
};

export const textColors = {
  title: theme.colors.txt,
  label: theme.colors.txt2,
  hint: theme.colors.txt3,
};

export const bgColors = {
  primary: theme.colors.bg,
  secondary: theme.colors.s1,
  tertiary: theme.colors.s2,
  hover: theme.colors.s3,
};

export const borderColors = {
  default: theme.colors.b1,
  hover: theme.colors.b2,
  active: theme.colors.b3,
};
