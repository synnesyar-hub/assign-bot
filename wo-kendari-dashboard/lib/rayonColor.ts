/* lib/rayonColor.ts */

export const RAYON_COLOR: Record<string, string> = {
  PWT: '#cc0000',
  TPL: '#ea9999',
  ABL: '#f9cb9c',
  AND: '#b6d7a8',
  BRG: '#a4c2f4',
  KDA: '#ff6d01',
  MDGOUT: '#46bdc6',
  WWA: '#ead1dc',
  KDROUT: '#00ffff',
  KKA: '#b4a7d6',
  KKAOUT: '#d9d2e9',
  LSS: '#ffe599',
  LSSOUT: '#fff2cc',
  PMA: '#9fc5e8',
  PMAOUT: '#c9daf8',
  UNH: '#be9063',
  UNHOUT: '#e6c9a8',
  BBU: '#d9d9d9',
  BBUOUT: '#f3f3f3',
  WNC: '#d5a6bd',
  RAH: '#fce5cd',
}

export const RAYON_TEXT_COLOR: Record<string, string> = {
  PWT: '#cc0000',
  TPL: '#cc4125',
  ABL: '#b45f06',
  AND: '#38761d',
  BRG: '#1155cc',
  KDA: '#b45c00',
  MDGOUT: '#134f5c',
  WWA: '#a64d79',
  KDROUT: '#0b8484',
  KKA: '#674ea7',
  KKAOUT: '#8e7cc3',
  LSS: '#bf9000',
  LSSOUT: '#d5b60a',
  PMA: '#1c4587',
  PMAOUT: '#3d85c6',
  UNH: '#7f4a1e',
  UNHOUT: '#a9762f',
  BBU: '#666666',
  BBUOUT: '#999999',
  WNC: '#a64d79',
  RAH: '#b45f06',
}

export function getRayonColor(rayon: string | null | undefined): string {
  if (!rayon) return '#d9d9d9'
  return RAYON_COLOR[rayon] ?? '#d9d9d9'
}

export function getRayonTextColor(rayon: string | null | undefined): string {
  if (!rayon) return '#666666'
  return RAYON_TEXT_COLOR[rayon] ?? '#666666'
}