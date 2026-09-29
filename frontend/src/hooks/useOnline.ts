import { useEffect, useState } from 'react';

/**
 * Live connectivity status.
 *
 * Uses navigator.onLine plus the window 'online'/'offline' events so the UI can
 * tell the user that what they are looking at may be stale while disconnected.
 * This is a UI hint only: it never fakes a sync and never hides a failed request.
 */
export function useOnline(): boolean {
  const [online, setOnline] = useState<boolean>(() =>
    typeof navigator === 'undefined' ? true : navigator.onLine,
  );

  useEffect(() => {
    const goOnline = () => setOnline(true);
    const goOffline = () => setOnline(false);
    window.addEventListener('online', goOnline);
    window.addEventListener('offline', goOffline);
    // Re-read once on mount: the initial render may predate hydration.
    setOnline(navigator.onLine);
    return () => {
      window.removeEventListener('online', goOnline);
      window.removeEventListener('offline', goOffline);
    };
  }, []);

  return online;
}
