import { realpathSync, statSync } from 'node:fs';
import path from 'node:path';

function inside(root, file) {
  const relative = path.relative(root, file);
  return relative && relative !== '..' && !relative.startsWith(`..${path.sep}`) && !path.isAbsolute(relative);
}

/** Resolve only a regular file inside a declared public root, including through links. */
export function publicFile(root, relative, allowLinks = true) {
  if (/[\\:\x00-\x1f\x7f]/.test(relative) || relative.split('/').some((part) => part.startsWith('.'))) return null;
  try {
    const directory = realpathSync(root);
    const expected = path.resolve(directory, relative);
    // Reject rooted/UNC paths before accessing the requested filesystem location.
    if (!inside(directory, expected)) return null;
    const file = realpathSync(expected);
    if (!inside(directory, file)) return null;
    // Root metadata/documents are individual public files, not a public directory.
    if (!allowLinks && file !== expected) return null;
    return statSync(file).isFile() ? file : null;
  } catch {
    return null;
  }
}
