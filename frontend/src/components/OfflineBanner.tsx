import { useOnline } from '../hooks/useOnline';

/**
 * Subtle, app-wide connectivity notice.
 *
 * Shown only while the browser reports no connection. It tells the user that
 * data on screen may be stale; it does not block the UI and does not claim to
 * have synced anything.
 */
export function OfflineBanner() {
  const online = useOnline();
  if (online) return null;

  return (
    <div
      role="status"
      aria-live="polite"
      style={{
        position: 'sticky',
        top: 0,
        zIndex: 60,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        gap: 8,
        padding: '7px 12px',
        fontSize: 12.5,
        fontWeight: 500,
        letterSpacing: '0.01em',
        color: '#E7ECF2',
        background: '#2A1E12',
        borderBottom: '1px solid #4A3A22',
      }}
    >
      <span
        aria-hidden="true"
        style={{
          width: 7,
          height: 7,
          borderRadius: '50%',
          background: '#E0A34A',
          flex: '0 0 auto',
        }}
      />
      <span>Offline — showing last loaded data, which may be out of date.</span>
    </div>
  );
}
