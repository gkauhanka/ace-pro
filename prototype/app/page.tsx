"use client";

import { useState } from "react";

const matches = [
  { opponent: "Maya Chen", date: "Yesterday", score: "4–6, 6–3, 4–6", result: "L", status: "ready" },
  { opponent: "Sofia Reyes", date: "Aug 22", score: "6–3, 6–4", result: "W", status: "ready" },
  { opponent: "Nina Patel", date: "Aug 16", score: "6–7, 2–1", result: "", status: "processing" },
];

const clips = [
  [8, "12:42", "1–2, 30–40", 96], [14, "21:08", "2–3, 15–30", 91],
  [19, "29:17", "3–4, deuce", 88], [31, "45:52", "5–5, 0–15", 77],
  [38, "56:31", "1–2, 15–30", 94], [43, "1:04:22", "2–3, 30–40", 83],
  [51, "1:17:09", "4–5, 15–30", 89],
] as const;

type Screen = "home" | "matches" | "report" | "insight" | "team" | "profile" | "upload";

export default function Home() {
  const [screen, setScreen] = useState<Screen>("home");
  const [verified, setVerified] = useState<number[]>([8]);
  const [clip, setClip] = useState<(typeof clips)[number] | null>(null);

  const title = screen === "matches" ? "Matches" : screen === "report" ? "Match report" : screen === "insight" ? "Insight" : screen === "team" ? "Team" : screen === "profile" ? "You" : "";

  return (
    <main className="stage">
      <div className="phone">
        <div className="status"><b>9:41</b><span>● ●● ▰</span></div>
        {title && <header className="nav"><button onClick={() => setScreen(screen === "insight" ? "report" : "home")}>‹</button><b>{title}</b><i /></header>}

        <section className="content">
          {screen === "home" && <HomeScreen onUpload={() => setScreen("upload")} onReport={() => setScreen("report")} onInsight={() => setScreen("insight")} />}
          {screen === "matches" && <Matches onReport={() => setScreen("report")} />}
          {screen === "report" && <Report onInsight={() => setScreen("insight")} />}
          {screen === "insight" && <Insight verified={verified} setClip={setClip} />}
          {screen === "team" && <Team />}
          {screen === "profile" && <Profile />}
          {screen === "upload" && <Upload close={() => setScreen("home")} />}
        </section>

        {!(["insight", "report", "upload"] as Screen[]).includes(screen) && <nav className="tabs">
          <Tab active={screen === "home"} icon="✦" label="Today" onClick={() => setScreen("home")} />
          <Tab active={screen === "matches"} icon="▣" label="Matches" onClick={() => setScreen("matches")} />
          <Tab active={screen === "team"} icon="♟" label="Team" onClick={() => setScreen("team")} />
          <Tab active={screen === "profile"} icon="●" label="You" onClick={() => setScreen("profile")} />
        </nav>}

        {clip && <div className="modal">
          <div className="sheet">
            <div className="sheetHead"><button onClick={() => setClip(null)}>Done</button><b>Point {clip[0]}</b><i /></div>
            <div className="video"><button>▶</button><small>Mock video · {clip[1]}</small></div>
            <h3>Was this detected correctly?</h3>
            <select aria-label="Detection"><option>Short backhand return</option><option>Deep backhand return</option><option>Not a return</option></select>
            <button className="primary" onClick={() => { setVerified([...verified, clip[0]]); setClip(null); }}>Confirm detection</button>
          </div>
        </div>}
      </div>
      <aside><b>Ace Pro UX prototype</b><p>Use the phone to explore the mocked post-match flow.</p><span>Local preview · no data is uploaded</span></aside>
    </main>
  );
}

function HomeScreen({onUpload,onReport,onInsight}:{onUpload:()=>void;onReport:()=>void;onInsight:()=>void}) { return <div className="pad">
  <div className="heroHead"><div><small>ACE PRO</small><h2>Good morning, Alex</h2></div><button className="plus" onClick={onUpload}>＋</button></div>
  <button className="focus" onClick={onInsight}><span>⌖ &nbsp; YOUR NEXT FOCUS</span><h1>Build depth on your backhand return</h1><p>7 clips show the same pattern across both sets.</p><b>↗</b></button>
  <div className="sectionTitle"><h3>Recent matches</h3><button onClick={onReport}>See all</button></div>
  {matches.map((m,i)=><button className="match" key={m.opponent} onClick={onReport}><strong>{m.status === "processing" ? "◔" : m.result}</strong><span><b>vs. {m.opponent}</b><small>{m.date} · {m.score}</small></span><em>›</em></button>)}
</div> }

function Matches({onReport}:{onReport:()=>void}) { return <div className="pad"><div className="segment"><b>All</b><span>Ready</span><span>Processing</span></div>{matches.map(m=><button className="match" key={m.opponent} onClick={onReport}><strong>{m.status === "processing" ? "◔" : m.result}</strong><span><b>vs. {m.opponent}</b><small>{m.date} · {m.score}</small></span><em>›</em></button>)}</div> }

function Report({onInsight}:{onInsight:()=>void}) { return <div className="pad"><div className="reportHead"><h2>vs. Maya Chen <b>L</b></h2><h3>4–6, 6–3, 4–6</h3><p>Yesterday · 1h 42m</p><small>Riverside Tennis Club</small></div><h3>What shaped the match</h3><p className="muted">Ranked by estimated impact, with every finding linked to video evidence.</p>{[
  ["PRIORITY 1","Short backhand returns were costly","You lost 64% of points when your backhand return landed inside the service box.","7 clips"],
  ["PRIORITY 2","Second serve held up under pressure","Your second-serve win rate rose to 58% on break points.","4 clips"],
  ["PRIORITY 3","Selective net approaches worked","You won 8 of 11 points at net, mostly after a deep forehand.","3 clips"]
].map(x=><button className="insightCard" onClick={onInsight} key={x[0]}><small>{x[0]}</small><h3>{x[1]}</h3><p>{x[2]}</p><b>▣ {x[3]} <i>→</i></b></button>)}</div> }

function Insight({verified,setClip}:{verified:number[];setClip:(c:(typeof clips)[number])=>void}) { return <div className="pad"><div className="insightHero"><small>PRIORITY 1</small><h1>Short backhand returns were costly</h1><p>You lost 64% of points when your backhand return landed inside the service box. This pattern appeared in both sets.</p><div><b>64%</b> points lost</div></div><div className="practice"><small>NEXT PRACTICE</small><h3>Review return position, then practice deep cross-court returns under second-serve pressure.</h3><button>Add to practice plan</button></div><div className="sectionTitle"><h3>Evidence</h3><small>{verified.length}/7 verified</small></div><p className="muted">Tap a point to review or correct the detection.</p>{clips.map(c=><button className="clip" key={c[0]} onClick={()=>setClip(c)}><strong>▶</strong><span><b>Point {c[0]} · {c[2]}</b><small>{c[1]} · {c[3]}% confidence</small></span><em>{verified.includes(c[0]) ? "✓" : "›"}</em></button>)}</div> }

function Team(){return <div className="pad"><div className="practice"><small>THIS WEEK</small><h2>Return depth is the team’s clearest shared pattern.</h2><p>4 of 6 players lost more points after short returns. 23 clips are ready for review.</p></div><h3>Players</h3>{["Alex Morgan","Sam Rivera","Taylor Kim","Jamie Park"].map(x=><div className="match" key={x}><strong>{x[0]}</strong><span><b>{x}</b><small>Latest report ready</small></span><em>›</em></div>)}</div>}
function Profile(){return <div className="pad"><div className="profile"><strong>AM</strong><div><h2>Alex Morgan</h2><p>Right-handed · 4.5</p></div></div>{["Notifications","Video quality","Analysis settings","Recording guide","Privacy & data"].map(x=><button className="setting" key={x}>{x}<span>›</span></button>)}</div>}

function Upload({close}:{close:()=>void}){const [step,setStep]=useState(0);return <div className="upload"><div className="sheetHead"><button onClick={close}>Cancel</button><b>Add a match</b><i /></div><div className="steps"><i/><i className={step>0?"on":""}/><i className={step>1?"on":""}/></div>{step===0&&<><h2>Choose your match video</h2><p>A full match from behind the baseline works best.</p><button className="choice" onClick={()=>setStep(1)}>▧ <span><b>Photo library</b><small>Choose a video on this iPhone</small></span>›</button><button className="choice" onClick={()=>setStep(1)}>□ <span><b>Browse files</b><small>iCloud Drive, GoPro, or another source</small></span>›</button></>}{step===1&&<><h2>Match details</h2><p>This helps organize your reports.</p><input placeholder="Opponent name"/><input placeholder="Venue (optional)"/><button className="primary" onClick={()=>setStep(2)}>Continue</button></>}{step===2&&<div className="uploading"><b>↑</b><h2>Your match is uploading</h2><p>We’ll start analysis automatically.</p><progress value="42" max="100"/><small>42% · About 8 min left</small><button className="primary" onClick={close}>Done</button></div>}</div>}

function Tab({active,icon,label,onClick}:{active:boolean;icon:string;label:string;onClick:()=>void}){return <button className={active?"active":""} onClick={onClick}><b>{icon}</b><small>{label}</small></button>}
