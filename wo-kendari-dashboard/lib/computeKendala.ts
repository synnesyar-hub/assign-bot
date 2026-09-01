// lib/computeKendala.ts

export function computeKendala(
  onuRx: unknown,
  symptom: unknown,
  gaul: unknown
): string {
  const rxRaw = String(onuRx ?? '').trim().toLowerCase();
  const symText = String(symptom ?? '').trim().toLowerCase();

  if (rxRaw === '' && symText === '') return '';

  const match = rxRaw.match(/-?[0-9]+[.,][0-9]+|-?[0-9]+/);
  let rxValue: number | null = null;
  if (match) rxValue = parseFloat(match[0].replace(',', '.'));

  let category: string;

  if (
    rxRaw === '' ||
    rxRaw === 'null' ||
    rxValue === null ||
    rxValue === 0 ||
    rxValue > 0 ||
    rxValue <= -30
  ) {
    category = 'LOS';
  } else if (rxValue <= -25 && rxValue > -30) {
    category = 'UNSPEC';
  } else if (/remote rusak|rusak remote|remote/.test(symText)) {
    category = 'REMOTE STB';
  } else if (/stb|iptv|useetv|usee/.test(symText)) {
    category = 'USEE TBC';
  } else if (/modem rusak|modem/.test(symText)) {
    category = 'MODEM RUSAK';
  } else if (/browsing|internet|intermitten|intermittent|putus.?putus|lambat/.test(symText)) {
    category = 'INET TBC';
  } else {
    category = 'OTHER / TBC';
  }

  const gaulValue = Number(gaul ?? 0);
  if (!Number.isNaN(gaulValue) && gaulValue !== 0) {
    return `${category} | GAUL`;
  }

  return category;
}