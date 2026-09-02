/* lib/customerTypeColor.ts */

export const CUSTOMER_TYPE_BG: Record<string, string> = {
  'VVIP 3H': '#e69138',
  'INDIBIZ 4H': '#f9cb9c',
  'REGULER 24H': '#45818e',
  'HVC_PLATINUM 6H': '#a2e8e4',
  'HVC_DIAMOND 3H': '#980000',
  'WIFI ID': '#93c47d',
  'ASTINET 3.6H': '#b4a7d6',
  'ASTINET 7.2H': '#8e7cc3',
  'VPNIP 3.6H': '#ead1dc',
  'VPNIP 7.2H': '#c27ba0',
  'METRO-E 3.6H': '#a4c2f4',
  'METRO-E 7.2H': '#3c78d8',
  'IP TRANSIT 3.6H': '#ffe599',
  'IP TRANSIT 7.2H': '#f1c232',
}

export const CUSTOMER_TYPE_TEXT: Record<string, string> = {
  'VVIP 3H': '#ffffff',
  'INDIBIZ 4H': '#b45f06',
  'REGULER 24H': '#ffffff',
  'HVC_PLATINUM 6H': '#0d5c5c',
  'HVC_DIAMOND 3H': '#ffffff',
  'WIFI ID': '#274e13',
  'ASTINET 3.6H': '#351c75',
  'ASTINET 7.2H': '#20124d',
  'VPNIP 3.6H': '#a64d79',
  'VPNIP 7.2H': '#5b1f42',
  'METRO-E 3.6H': '#1155cc',
  'METRO-E 7.2H': '#0d2c6b',
  'IP TRANSIT 3.6H': '#7f6000',
  'IP TRANSIT 7.2H': '#4c3d00',
}

export function getCustomerTypeBg(type: string | null | undefined): string | null {
  if (!type) return null
  return CUSTOMER_TYPE_BG[type] ?? null
}

export function getCustomerTypeText(type: string | null | undefined): string | null {
  if (!type) return null
  return CUSTOMER_TYPE_TEXT[type] ?? null
}