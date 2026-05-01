export type QualityTier = 'A' | 'B' | 'C' | 'D';

export interface Delegate {
  init: string;          // 2-letter initials
  name: string;
  zone: string;
  ca: number;            // CA vs objectif %
  prime: number;         // prime realization %
  q: QualityTier;        // visit quality tier
  anom: number;          // anomaly rate %
  flags: number;         // total semantic flags count
  risk: number;          // attrition risk 0–1
  trend: string;         // e.g. '▲ +14%'
  risky: boolean;        // highlight row red background
}

export const delegates: Delegate[] = [
  {init:'AK', name:'Amor Khelifi',    zone:'Tunis Nord', ca:112, prime:94, q:'A', anom:2,  flags:6,  risk:0.12, trend:'▲ +14%',  risky:false},
  {init:'SB', name:'Sana Ben Salah',  zone:'Ariana',     ca:104, prime:88, q:'A', anom:3,  flags:9,  risk:0.18, trend:'▲ +9%',   risky:false},
  {init:'IH', name:'Ines Haddad',     zone:'Sfax Nord',  ca:98,  prime:76, q:'B', anom:4,  flags:8,  risk:0.24, trend:'▲ +5%',   risky:false},
  {init:'MG', name:'Mohamed Gharbi',  zone:'Sousse',     ca:92,  prime:71, q:'B', anom:5,  flags:11, risk:0.28, trend:'— +1%',   risky:false},
  {init:'FJ', name:'Fatma Jemli',     zone:'Manouba',    ca:89,  prime:67, q:'B', anom:4,  flags:8,  risk:0.31, trend:'▲ +4%',   risky:false},
  {init:'RB', name:'Riadh Brahim',    zone:'Ben Arous',  ca:86,  prime:63, q:'B', anom:5,  flags:10, risk:0.34, trend:'▲ +2%',   risky:false},
  {init:'YM', name:'Yassine Mhiri',   zone:'Mahdia',     ca:83,  prime:59, q:'B', anom:4,  flags:9,  risk:0.38, trend:'— 0%',    risky:false},
  {init:'AH', name:'Asma Hamrouni',   zone:'Monastir',   ca:81,  prime:56, q:'C', anom:6,  flags:12, risk:0.42, trend:'▼ -1%',   risky:false},
  {init:'MD', name:'Mahmoud Douiri',  zone:'Kef',        ca:78,  prime:53, q:'C', anom:7,  flags:14, risk:0.46, trend:'▼ -2%',   risky:false},
  {init:'SM', name:'Skander Mejri',   zone:'Bizerte',    ca:76,  prime:54, q:'C', anom:7,  flags:13, risk:0.58, trend:'▼ -3%',   risky:true},
  {init:'LM', name:'Leila Mansouri',  zone:'Nabeul',     ca:71,  prime:49, q:'C', anom:9,  flags:18, risk:0.51, trend:'▼ -5%',   risky:true},
  {init:'KT', name:'Khaled Tounsi',   zone:'Kairouan',   ca:68,  prime:42, q:'C', anom:12, flags:22, risk:0.67, trend:'▼ -8%',   risky:true},
  {init:'WB', name:'Wafa Ben Ammar',  zone:'Beja',       ca:64,  prime:38, q:'C', anom:10, flags:16, risk:0.48, trend:'— 0%',    risky:false},
  {init:'TK', name:'Tarek Kassar',    zone:'Zaghouan',   ca:61,  prime:34, q:'C', anom:11, flags:15, risk:0.52, trend:'▼ -2%',   risky:false},
  {init:'RD', name:'Rania Daoud',     zone:'Jendouba',   ca:58,  prime:31, q:'C', anom:13, flags:19, risk:0.55, trend:'▼ -4%',   risky:false},
  {init:'AB', name:'Ahmed Bahri',     zone:'Siliana',    ca:55,  prime:28, q:'D', anom:14, flags:21, risk:0.49, trend:'▼ -3%',   risky:false},
  {init:'NA', name:'Najla Ayari',     zone:'Médenine',   ca:51,  prime:28, q:'D', anom:16, flags:31, risk:0.84, trend:'▼▼ -14%', risky:true},
  {init:'HZ', name:'Hichem Zouari',   zone:'Gabès',      ca:44,  prime:19, q:'D', anom:21, flags:38, risk:0.91, trend:'▼▼ -19%', risky:true},
];
