import { useEffect, useState } from 'react';
import { Moon, Sun } from 'lucide-react';

type Theme = 'light' | 'dark';
export default function ThemeToggle() {
 const [preference, setPreference] = useState<Theme | null>(() => {
  try { const saved = localStorage.getItem('parallax-theme'); return saved === 'light' || saved === 'dark' ? saved : null; } catch { return null; }
 });
 const [systemDark, setSystemDark] = useState(() => matchMedia('(prefers-color-scheme: dark)').matches);
 const theme = preference ?? (systemDark ? 'dark' : 'light');
 useEffect(() => {
  const media = matchMedia('(prefers-color-scheme: dark)');
  const update = () => setSystemDark(media.matches);
  media.addEventListener('change', update);
  return () => media.removeEventListener('change', update);
 }, []);
 useEffect(() => {
  document.documentElement.dataset.theme = theme;
  document.querySelector('meta[name="theme-color"]')?.setAttribute('content', theme === 'dark' ? '#101619' : '#f5f4ef');
 }, [theme]);
 function toggle() {
  const next = theme === 'dark' ? 'light' : 'dark';
  setPreference(next);
  try { localStorage.setItem('parallax-theme', next); } catch { /* The toggle still works without browser storage. */ }
 }
 return <button className="theme-toggle" aria-label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'} title={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'} onClick={toggle}>{theme === 'dark' ? <Sun size={19}/> : <Moon size={19}/>}</button>;
}
