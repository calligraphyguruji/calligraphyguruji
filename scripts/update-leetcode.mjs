import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const rootDir = path.resolve(__dirname, '..');

const USERNAME = 'calligraphyguruji';

async function fetchLeetCodeStats() {
  const query = `
    query getUserCalendar($username: String!) {
      matchedUser(username: $username) {
        userCalendar {
          streak
          totalActiveDays
          submissionCalendar
        }
        submitStats: submitStatsGlobal {
          acSubmissionNum {
            difficulty
            count
          }
        }
      }
    }
  `;

  const res = await fetch('https://leetcode.com/graphql', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Referer': `https://leetcode.com/${USERNAME}/`,
      'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'
    },
    body: JSON.stringify({
      query,
      variables: { username: USERNAME }
    })
  });

  if (!res.ok) {
    throw new Error(`GraphQL request failed with status: ${res.status}`);
  }

  const data = await res.json();
  if (!data?.data?.matchedUser) {
    throw new Error('User not found or invalid GraphQL response');
  }

  const calendar = data.data.matchedUser.userCalendar;
  const streak = calendar.streak || 0;
  const totalActiveDays = calendar.totalActiveDays || 0;

  // Compute max streak from submissionCalendar
  let maxStreak = streak;
  if (calendar.submissionCalendar) {
    try {
      const subCal = JSON.parse(calendar.submissionCalendar);
      const days = Object.keys(subCal).map(Number).sort((a, b) => a - b);
      let runningStreak = 0;
      let prevDay = 0;
      for (const t of days) {
        const day = Math.floor(t / 86400);
        if (day === prevDay + 1) {
          runningStreak++;
        } else if (day !== prevDay) {
          runningStreak = 1;
        }
        if (runningStreak > maxStreak) maxStreak = runningStreak;
        prevDay = day;
      }
    } catch (e) {
      console.warn('Failed parsing submissionCalendar:', e);
    }
  }

  return {
    streak,
    maxStreak,
    totalActiveDays,
  };
}

function generateSvg({ streak, maxStreak, totalActiveDays }) {
  return `<svg width="495" height="135" viewBox="0 0 495 135" fill="none" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="LeetCode Streak Stats: Current Streak ${streak} Days, Max Streak ${maxStreak} Days, Total Active Days ${totalActiveDays}">
  <title>Aman Mishra's LeetCode Streak</title>
  <defs>
    <linearGradient id="bgGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#161b22"/>
      <stop offset="100%" stop-color="#0d1117"/>
    </linearGradient>
    <linearGradient id="streakGrad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#FF9100"/>
      <stop offset="100%" stop-color="#FFA116"/>
    </linearGradient>
    <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="4" result="blur"/>
      <feComposite in="SourceGraphic" in2="blur" operator="over"/>
    </filter>
    <style>
      @media (prefers-reduced-motion: no-preference) {
        @keyframes flamePulse {
          0% { transform: scale(1); opacity: 0.9; }
          50% { transform: scale(1.08); opacity: 1; filter: drop-shadow(0 0 6px rgba(255, 161, 22, 0.8)); }
          100% { transform: scale(1); opacity: 0.9; }
        }
        @keyframes ringPulse {
          0% { stroke-opacity: 0.4; }
          50% { stroke-opacity: 0.9; }
          100% { stroke-opacity: 0.4; }
        }
        .flame-icon {
          transform-origin: 247.5px 36px;
          animation: flamePulse 2.4s ease-in-out infinite;
        }
        .ring-glow {
          animation: ringPulse 2.4s ease-in-out infinite;
        }
      }
      .stat-num { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Ubuntu, 'Helvetica Neue', sans-serif; font-weight: 700; }
      .stat-label { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Ubuntu, 'Helvetica Neue', sans-serif; font-weight: 600; letter-spacing: 0.5px; }
      .stat-sub { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Ubuntu, 'Helvetica Neue', sans-serif; font-weight: 400; }
    </style>
  </defs>

  <!-- Card Background -->
  <rect x="0.5" y="0.5" width="494" height="134" rx="10" fill="url(#bgGrad)" stroke="#30363d" stroke-width="1"/>

  <!-- Left: Total Active Days -->
  <g transform="translate(88, 0)">
    <text x="0" y="52" text-anchor="middle" class="stat-num" font-size="26" fill="#f0f6fc">${totalActiveDays}</text>
    <text x="0" y="78" text-anchor="middle" class="stat-label" font-size="11.5" fill="#8b949e">TOTAL ACTIVE DAYS</text>
    <text x="0" y="98" text-anchor="middle" class="stat-sub" font-size="10.5" fill="#6e7681">All-Time Activity</text>
  </g>

  <!-- Vertical Divider 1 -->
  <line x1="168" y1="28" x2="168" y2="108" stroke="#21262d" stroke-width="1" stroke-dasharray="2 2"/>

  <!-- Center: Current Streak -->
  <g>
    <!-- Outer Decorative Glow Ring -->
    <circle cx="247.5" cy="38" r="24" fill="none" stroke="#FFA116" stroke-width="2" stroke-opacity="0.3" class="ring-glow"/>
    <circle cx="247.5" cy="38" r="20" fill="#FFA116" fill-opacity="0.08"/>
    
    <!-- Flame Icon -->
    <g class="flame-icon">
      <path d="M248.5 24 C248.5 24 250.2 27.5 250.2 30.2 C250.2 32.8 248.5 34.9 245.9 34.9 C243.3 34.9 241.4 32.8 241.4 30.2 C241.4 29.8 241.5 29.3 241.6 28.9 C239.1 31.9 237.6 35.8 237.6 40.0 C237.6 45.5 242.0 50.0 247.5 50.0 C253.0 50.0 257.5 45.5 257.5 40.0 C257.5 33.3 253.4 27.8 248.5 24 Z M247.1 46.2 C244.9 46.2 243.1 44.5 243.1 42.3 C243.1 40.3 244.4 38.9 246.6 38.4 C248.8 38.0 251.1 36.9 252.4 35.2 C252.9 36.8 253.1 38.5 253.1 40.2 C253.1 43.5 250.4 46.2 247.1 46.2 Z" fill="url(#streakGrad)" filter="url(#glow)"/>
    </g>

    <!-- Streak Count -->
    <text x="247.5" y="80" text-anchor="middle" class="stat-num" font-size="28" fill="#FFA116">${streak}</text>
    <text x="247.5" y="100" text-anchor="middle" class="stat-label" font-size="12" fill="#FFA116">CURRENT STREAK</text>
    <text x="247.5" y="118" text-anchor="middle" class="stat-sub" font-size="10.5" fill="#e3b341">Active Daily Streak 🔥</text>
  </g>

  <!-- Vertical Divider 2 -->
  <line x1="327" y1="28" x2="327" y2="108" stroke="#21262d" stroke-width="1" stroke-dasharray="2 2"/>

  <!-- Right: Max Streak -->
  <g transform="translate(407, 0)">
    <text x="0" y="52" text-anchor="middle" class="stat-num" font-size="26" fill="#f0f6fc">${maxStreak}</text>
    <text x="0" y="78" text-anchor="middle" class="stat-label" font-size="11.5" fill="#8b949e">MAX STREAK</text>
    <text x="0" y="98" text-anchor="middle" class="stat-sub" font-size="10.5" fill="#6e7681">All-Time Best</text>
  </g>
</svg>`;
}

async function main() {
  console.log('Fetching live LeetCode stats for', USERNAME);
  const stats = await fetchLeetCodeStats();
  console.log('Stats:', stats);

  const svg = generateSvg(stats);
  const svgPath = path.join(rootDir, 'assets', 'leetcode-streak.svg');
  fs.writeFileSync(svgPath, svg, 'utf-8');
  console.log('Wrote SVG to', svgPath);

  // Update README.md badge if needed
  const readmePath = path.join(rootDir, 'README.md');
  let readme = fs.readFileSync(readmePath, 'utf-8');

  // Replace any streak badge in README:
  // e.g. Current%20Streak-([0-9]+)%20Days or Streak-([0-9]+)%20Days
  const streakBadgeRegex = /https:\/\/img\.shields\.io\/badge\/Current%20Streak-[0-9]+%20Days-FFA116/g;
  if (streakBadgeRegex.test(readme)) {
    readme = readme.replace(streakBadgeRegex, `https://img.shields.io/badge/Current%20Streak-${stats.streak}%20Days-FFA116`);
  }

  const maxStreakBadgeRegex = /https:\/\/img\.shields\.io\/badge\/Max%20Streak-[0-9]+%20Days-FF6B35/g;
  if (maxStreakBadgeRegex.test(readme)) {
    readme = readme.replace(maxStreakBadgeRegex, `https://img.shields.io/badge/Max%20Streak-${stats.maxStreak}%20Days-FF6B35`);
  }

  fs.writeFileSync(readmePath, readme, 'utf-8');
  console.log('Updated README.md badges with streak', stats.streak, 'and max streak', stats.maxStreak);
}

main().catch(err => {
  console.error('Error updating LeetCode stats:', err);
  process.exit(1);
});
