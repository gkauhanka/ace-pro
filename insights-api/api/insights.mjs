import { randomInt } from 'node:crypto';

const topics = [
  { key: 'split-step', title: 'Land your split step as they strike', category: 'Footwork', metric: 'On-time split steps', unit: '%', low: 42, high: 70, description: 'A well-timed split step helps you react in either direction and reach the ball with more time.', drill: 'In your next session, do 3 × 60 seconds of shadow returns. Land softly as your partner makes contact, then push toward the ball.', query: 'tennis split step timing drill', cue: 'Land, read, then push.' },
  { key: 'contact', title: 'Give your forehand a little more room', category: 'Technique', metric: 'Balanced contact points', unit: '%', low: 48, high: 82, description: 'Creating space between your body and the ball helps you meet it comfortably in front.', drill: 'Feed 20 easy forehands cross-court. Adjust with small steps and hold your finish for two seconds. Repeat three times.', query: 'tennis forehand spacing contact point drill', cue: 'Small steps. Contact in front.' },
  { key: 'recovery', title: 'Recover before the next ball', category: 'Movement', metric: 'Recovery consistency', unit: '%', low: 45, high: 79, description: 'Recovering toward a useful court position after your shot can reduce the space your opponent can attack.', drill: 'Play 3 × 10 cooperative cross-court rallies. After every shot, recover toward a marker before your partner hits.', query: 'tennis court recovery positioning drill', cue: 'Hit, recover, get ready.' },
  { key: 'serve', title: 'Build a repeatable second serve', category: 'Serve', metric: 'Second serves in', unit: '%', low: 55, high: 88, description: 'A repeatable toss and a generous target help build second-serve confidence without chasing speed.', drill: 'Serve 4 sets of 10 balls to a large target. Keep your full motion and count how many land in. Rest between sets.', query: 'tennis consistent second serve drill', cue: 'Same toss. Smooth rhythm.' },
  { key: 'depth', title: 'Make your rally ball land deeper', category: 'Tactics', metric: 'Balls beyond service line', unit: '%', low: 39, high: 70, description: 'More net clearance and a deeper target can make it harder for an opponent to step inside the court.', drill: 'Mark a target in the back third of the court. Rally for five minutes with comfortable net clearance, counting deep balls.', query: 'tennis groundstroke depth control drill', cue: 'Aim high. Push them back.' }
];
export function generateInsights(input, integer = randomInt) {
  if (!input || typeof input !== 'object' || Array.isArray(input) || Object.keys(input).some(k => !['durationSeconds', 'sessionType', 'focus'].includes(k))) throw new Error('Only durationSeconds, sessionType and focus are accepted. Never send video or personal data.');
  if (!Number.isFinite(input.durationSeconds) || input.durationSeconds < 1 || input.durationSeconds > 21600) throw new Error('Video duration must be between 1 second and 6 hours.');
  if (!['Match', 'Practice'].includes(input.sessionType)) throw new Error('Choose Match or Practice.');
  if (!['All-round', 'Footwork', 'Technique', 'Serve', 'Tactics'].includes(input.focus)) throw new Error('Choose a supported focus.');
  const ranked = [...topics].sort((a, b) => Number(b.category === input.focus) - Number(a.category === input.focus));
  if (input.focus === 'All-round') { const offset = integer(0, ranked.length); ranked.push(...ranked.splice(0, offset)); }
  return {
    schemaVersion: 1, simulated: true,
    disclosure: 'Random examples for coaching exploration. No video has been analyzed. Statistics and timestamps are illustrative, not measurements or detected mistakes.',
    insights: ranked.slice(0, 3).map((t, i) => ({ ...t, low: undefined, high: undefined, query: undefined,
      value: integer(t.low, t.high + 1), priority: i + 1,
      youtubeURL: ({ 'split-step': 'https://www.youtube.com/watch?v=jtWMP75377k', serve: 'https://www.youtube.com/watch?v=aGwJlCrwZ90' })[t.key] || 'https://www.youtube.com/results?search_query=' + encodeURIComponent(t.query),
      moments: [0.19, 0.48, 0.77].map((fraction, j) => ({ seconds: Math.min(Math.max(0, Math.floor(input.durationSeconds * (fraction + i * 0.025))), Math.max(0, Math.floor(input.durationSeconds) - 1)), label: ['Review your setup', 'Check your movement', 'Watch your recovery'][j] }))
    }))
  };
}
export default async function handler(req, res) {
  res.setHeader('Cache-Control', 'no-store');
  if (req.method !== 'POST') { res.setHeader('Allow', 'POST'); return res.status(405).json({ error: 'Use POST.' }); }
  if (String(req.headers['content-type']).split(';')[0].trim().toLowerCase() !== 'application/json') return res.status(415).json({ error: 'Only JSON metadata is accepted.' });
  try {
    const body = typeof req.body === 'string' ? JSON.parse(req.body) : req.body;
    if (JSON.stringify(body).length > 1024) return res.status(413).json({ error: 'Metadata exceeds 1 KB.' });
    return res.status(200).json(generateInsights(body));
  } catch (error) { return res.status(400).json({ error: error.message }); }
}
