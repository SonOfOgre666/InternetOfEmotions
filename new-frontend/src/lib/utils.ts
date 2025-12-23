import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
/**
 * Map 3-letter ISO codes to 2-letter codes for flags
 */
export const iso3to2: Record<string, string> = {
  'USA': 'US',
  'GBR': 'GB',
  'DEU': 'DE',
  'FRA': 'FR',
  'IND': 'IN',
  'JPN': 'JP',
  'BRA': 'BR',
  'CAN': 'CA',
  'AUS': 'AU',
  'CHN': 'CN',
  'RUS': 'RU',
  'ITA': 'IT',
  'ESP': 'ES',
  'MEX': 'MX',
  'KOR': 'KR',
  'TUR': 'TR',
  'SAU': 'SA',
  'ZAF': 'ZA',
  'ARG': 'AR',
  'EGY': 'EG',
  'NGA': 'NG',
  'PAK': 'PK',
  'IDN': 'ID',
  'VNM': 'VN',
  'THA': 'TH',
  'PHL': 'PH',
  'MYS': 'MY',
  'UKR': 'UA',
  'POL': 'PL',
  'NLD': 'NL',
  'BEL': 'BE',
  'CHE': 'CH',
  'SWE': 'SE',
  'NOR': 'NO',
  'DNK': 'DK',
  'FIN': 'FI',
  'IRL': 'IE',
  'PRT': 'PT',
  'GRC': 'GR',
  'ISR': 'IL',
  'ARE': 'AE',
  'IRN': 'IR',
  'IRQ': 'IQ',
  'COL': 'CO',
  'CHL': 'CL',
  'PER': 'PE',
  'VEN': 'VE',
};

/**
 * Get 2-letter ISO code from 3-letter code
 */
export function getIso2(iso3: string): string {
  return iso3to2[iso3] || iso3.slice(0, 2);
}
  'BEL': 'BE',
  'CHE': 'CH',
  'SWE': 'SE',
  'NOR': 'NO',
  'DNK': 'DK',
  'FIN': 'FI',
  'IRL': 'IE',
  'PRT': 'PT',
  'GRC': 'GR',
  'ISR': 'IL',
  'ARE': 'AE',
  'IRN': 'IR',
  'IRQ': 'IQ',
  'COL': 'CO',
  'CHL': 'CL',
  'PER': 'PE',
  'VEN': 'VE',
};

/**
 * Get 2-letter ISO code from 3-letter code
 */
export function getIso2(iso3: string): string {
  return iso3to2[iso3] || iso3.slice(0, 2);
}
