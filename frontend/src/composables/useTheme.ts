import { onMounted, onUnmounted, ref, watch } from 'vue';

type Theme = 'light' | 'dark';
const STORAGE_KEY = 'xiaocan-theme';

function readStored(): Theme | null {
  try {
    const v = localStorage.getItem(STORAGE_KEY);
    return v === 'light' || v === 'dark' ? v : null;
  } catch {
    return null;
  }
}

function systemPrefersDark() {
  return typeof window !== 'undefined' && window.matchMedia('(prefers-color-scheme: dark)').matches;
}

const current = ref<Theme>('light');
const isManual = ref(false);

export function useTheme() {
  function apply(theme: Theme) {
    document.documentElement.setAttribute('data-theme', theme);
    current.value = theme;
  }

  function setManual(theme: Theme) {
    isManual.value = true;
    try { localStorage.setItem(STORAGE_KEY, theme); } catch { /* noop */ }
    apply(theme);
  }

  function toggle() {
    setManual(current.value === 'light' ? 'dark' : 'light');
  }

  function init() {
    const stored = readStored();
    if (stored) {
      isManual.value = true;
      apply(stored);
    } else {
      apply(systemPrefersDark() ? 'dark' : 'light');
    }
  }

  let mql: MediaQueryList | null = null;
  const onSystemChange = (e: MediaQueryListEvent) => {
    if (!isManual.value) apply(e.matches ? 'dark' : 'light');
  };

  onMounted(() => {
    init();
    if (typeof window !== 'undefined') {
      mql = window.matchMedia('(prefers-color-scheme: dark)');
      mql.addEventListener('change', onSystemChange);
    }
  });

  onUnmounted(() => {
    mql?.removeEventListener('change', onSystemChange);
  });

  watch(current, (t) => {
    document.documentElement.setAttribute('data-theme', t);
  });

  return { theme: current, toggle, setManual };
}
