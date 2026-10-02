/**
 * Is this a desktop-class device? Mid-size tables (5,000 to 20,000 rows, see large-data.ts)
 * draw their points by themselves, and zoom, only on one: a fine pointer (a mouse or
 * trackpad), at least 4 cores, at least 4 GB of memory where the browser says, and no
 * Save-Data request. Anything else gets a button, so a phone never blocks for seconds on
 * a chart nobody asked for.
 */

/** The media query for a mouse or trackpad as the primary pointer. */
export const FINE_POINTER = "(pointer: fine)";
/** At least this many logical cores (`navigator.hardwareConcurrency`). */
export const DESKTOP_MIN_CORES = 4;
/** At least this many GB of memory (`navigator.deviceMemory`, Chromium only; ignored where absent). */
export const DESKTOP_MIN_MEMORY_GB = 4;

/** What the browser tells about the device. */
export interface DeviceSignals {
  finePointer: boolean;
  cores: number | undefined;
  memoryGb: number | undefined;
  saveData: boolean;
}

interface DeviceNavigator {
  hardwareConcurrency?: number;
  deviceMemory?: number;
  connection?: { saveData?: boolean };
}

/** Read the signals from a window (the page's, or a stand-in in tests). */
export function deviceSignals(win: { matchMedia(query: string): { matches: boolean }; navigator: DeviceNavigator }): DeviceSignals {
  const nav = win.navigator;
  return {
    finePointer: win.matchMedia(FINE_POINTER).matches,
    cores: nav.hardwareConcurrency,
    memoryGb: nav.deviceMemory,
    saveData: nav.connection?.saveData === true,
  };
}

export function isDesktopClass(s: DeviceSignals): boolean {
  return (
    s.finePointer &&
    (s.cores ?? 0) >= DESKTOP_MIN_CORES &&
    (s.memoryGb === undefined || s.memoryGb >= DESKTOP_MIN_MEMORY_GB) &&
    !s.saveData
  );
}
