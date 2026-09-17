/** Seeded RNG. Kernel never calls Math.random. */

export function createRng(seed) {
  let s = (Number(seed) >>> 0) || 1;
  return {
    next() {
      s |= 0;
      s = (s + 0x6D2B79F5) | 0;
      let t = Math.imul(s ^ (s >>> 15), 1 | s);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    },
  };
}

export function mathRandomRng() {
  return { next: () => Math.random() };
}

export function pick(arr, rng) {
  if (!arr.length) return undefined;
  return arr[Math.floor(rng.next() * arr.length)];
}

export function rnd(rng, a, b) {
  return a + rng.next() * (b - a);
}
