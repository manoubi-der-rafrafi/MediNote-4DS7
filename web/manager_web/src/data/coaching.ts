export interface CoachingItem {
  init: string;
  name: string;
  risk: number;
  reasons: string;
  cta: string;
}

export const coachingQueue: CoachingItem[] = [
  {init:'HZ', name:'Hichem Zouari',  risk:0.91, reasons:'CA 19% of target · Visit quality D · 14 flagged reports · Prime gap 81%', cta:'Urgent 1:1'},
  {init:'NA', name:'Najla Ayari',    risk:0.84, reasons:'CA 28% · 3 months declining · 16 concurrence flags',                       cta:'Territory review'},
  {init:'KT', name:'Khaled Tounsi',  risk:0.67, reasons:'Prime 42% · visit Q = C · 8% suspicious reports',                         cta:'Report quality coaching'},
  {init:'SM', name:'Skander Mejri',  risk:0.58, reasons:'Lost 4 accounts · no formation 9 months',                                  cta:'Enroll formation γ-3'},
  {init:'LM', name:'Leila Mansouri', risk:0.51, reasons:'Comment quality dropping · 2 contradictions',                              cta:'Shadow visit'},
];
