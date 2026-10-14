/**
 * `load`, run once and shared by every caller, unless it fails: a rejected promise is
 * forgotten, so the next call tries again (a Retry after the connection comes back)
 * instead of repeating the old failure.
 */
export function onceUnlessFailed<T>(load: () => Promise<T>): () => Promise<T> {
  let pending: Promise<T> | null = null;
  return () => {
    if (!pending) {
      const p = load();
      pending = p;
      p.catch(() => {
        if (pending === p) pending = null;
      });
    }
    return pending;
  };
}
