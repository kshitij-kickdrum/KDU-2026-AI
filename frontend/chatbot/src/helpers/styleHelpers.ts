import type { Style } from '../types';

export function deriveStyle(age: number): Style {
  return age <= 12 ? 'child' : 'expert';
}

export function styleLabel(style: Style): string {
  return style === 'child' ? 'Child' : 'Expert';
}

export function isChildStyle(style: Style): boolean {
  return style === 'child';
}
